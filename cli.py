#!/usr/bin/env python3

import json
import click
from tqdm import tqdm

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


def get_db(cred_file="firebase-admin.json"):
    cred = credentials.Certificate(cred_file)
    firebase_admin.initialize_app(cred, {
        # NOTE: hardcoded file name should really be loaded from .firebaserc
        'projectId': 'trips-annotate-35636'
    })

    return firestore.client()

def filter_tasks(tasks, taskset, sentence):
    return [t for t in tasks if not (t["taskset"] == taskset and t["data"]["sentence"] == sentence)]

def unique_tasks(new_tasks, tasks):
    """Ensure that a sentence is unique for the given taskset"""
    query = tasks.select(field_paths=["taskset", "data.sentence"])
    for q in query.stream():
        q = q.to_dict()
        new_tasks = filter_tasks(new_tasks, q["taskset"], q["data"]["sentence"])
    return new_tasks


@click.command()
@click.option("--task-set", "fname", type=str, help="formatted data to upload")
@click.option("--credentials", "cred_file", type=str, default="firebase-admin.json", help="firebase credentials file")
def add_tasks(fname, cred_file="firebase-admin.json"):
    """Add tasks from the given task-set json file.  The input json file should be generated using `transform`"""
    db = get_db(cred_file)

    with open(fname) as inp:
        taskset = json.load(inp)
    click.echo("looking up taskset:%s" % taskset["name"])
    taskset_ref = db.collection(u'taskset').document(taskset["name"])
    if taskset_ref.get().exists:
        click.echo("please rename the taskset! %s already exists" % taskset["name"])
        return -1

    taskset_ref.set(taskset["definition"]) # guess I'm not updating tasksets

    data = taskset["tasks"]
    doc_ref = db.collection(u'tasks')


    for d in tqdm(data):
        doc_ref.add(dict(d, taskset=taskset["name"])) # think I can optimize this?

    click.echo("added %d new tasks." % len(data))
    return 1


def get_sentence(taskset, id):
    with open("%s/%d/parse.json" % (taskset, id)) as parse:
        return json.load(parse)["sentence"]

@click.command()
@click.option("--task-set", "taskset", type=str, help="output folder for prepare.sh")
@click.option("--name", "name", type=str, help="the name for the taskset.")
@click.option("--output", "output", type=str, help="directory to write all output to")
@click.option("--type", "type_", default="a_b_parse", type=str, help="task_type")
@click.option("--coverage", "coverage", default=3, type=int, help="minimum number of annotators requested")
@click.option("--agreement", "agreement", default=0.0, type=float, help="minimum amount of agreement required")
@click.option("--active/--no-active", "active", default=True)
def transform(taskset, name, output, type_="a_b_parse", coverage=3, agreement=0, active=True):
    """Read in a json list of tasks and create a task object for upload to firebase"""
    fname = "%s/data.json" % taskset
    name = name or taskset.split("/")[-1]
    with open(fname) as inp:
        dataset = json.load(inp)
    tasks = [{
        "annotations": [],
        "data": dict(data, type=type_), # sentence getting is now done in prepare.py
        "requirements": {
            "agreement": agreement,
            "coverage": coverage,
            "annotators": []
        }
    } for data in dataset if data]
    num_sets = len(tasks) // 50
    print("writing %d task-sets" % num_sets)
    for i in range(num_sets-1):
        res = dict(name="%s-%d" % (name, i), tasks=tasks[i * 50 : (i+1) * 50], definition=dict(type=type_, items=len(tasks), groups=[], is_active=active))
        with open("%s/%s-%d.json" % (output, name, i), 'w') as out:
            json.dump(res, out, indent=2)
    with open("%s/%s-rem.json" % (output, name), 'w') as out:
        res = dict(name="%s/%s-rem.json" % (output, name), tasks=tasks[(num_sets - 1) * 50:], definition=dict(type=type_, items=len(tasks), groups=[], is_active=active))
        json.dump(res, out, indent=2)

@click.command()
@click.option("--task-set", "taskset", type=str, help="The task set to assign")
@click.option("--type", "type_", type=str, help="worker type to assign the task to", default="researcher")
@click.option("--set", "s", type=int, help="worker set to assign the task to", default=0)
@click.option("--credentials", "cred_file", type=str, default="firebase-admin.json", help="firebase credentials file")
def assign(taskset, type_, s, cred_file="firebase-admin.json"):
    """Assign a taskset to a group consisting of (usertype, set).  Make sure to upload the taskset first"""
    db = get_db(cred_file)
    # 1. add to taskset
    task_ref = db.collection("taskset").document(taskset)
    if not task_ref.get().exists:
        click.echo("incorrect taskset : %s does not exist.  Use `upload` to put the taskset on firebase first." % taskset)
        return -1
    task_ref.update({"groups.%s" % type_: firestore.ArrayUnion([s])})

    task_ids = [r.id for r in db.collection("tasks").where("taskset", "==", taskset).stream()]

    # 2. add to group
    ref = db.collection("groups").document(type_)

    # 2. a. create group if necessary
    if not ref.get().exists:
        ref.set({})
    # Need to deal with the condition that this task has already been assigned
    ref.update({str(s): firestore.ArrayUnion([taskset])})

    # 3. for each user in the defined group, queue the task
    # This should be done as a cloud function
    #user_ref = db.collection("users").where("type.role", "==", type_).where("type.set", "==", s)
    #batch = db.batch()
    ## Need to deal with the condition that this task has already been assigned
    #for document in user_ref.stream():
    #    # make sure the required taskid exists in the list.  Union with an empty array to prevent overwriting
    #    # prior annotations.  Solves duplication of tasks
    #    batch.update(document.reference, {"tasks.%s.annotations" % id: firestore.ArrayUnion([]) for id in task_ids})
    #    batch.update(document.reference, {"tasks.%s.completed" % id: firestore.Increment(0) for id in task_ids})
    #batch.commit()

def set_taskset_enabled(taskset, value, cred_file):
    db = get_db(cred_file)
    taskset_ref = db.collection("taskset").document(taskset)
    if not taskset_ref.get().exists:
        click.echo("incorrect taskset : %s does not exist.  Use `upload` to put the taskset on firebase first." % taskset)
    return taskset_ref.update({"is_active" : value})

@click.command()
@click.option("--task-set", "taskset", type=str, help="task-set to toggle")
@click.option("--credentials", "cred_file", type=str, default="firebase-admin.json", help="firebase credentials file")
def enable(taskset, cred_file):
    """enable a task-set"""
    set_taskset_enabled(taskset, True, cred_file=cred_file)

@click.command()
@click.option("--task-set", "taskset", type=str, help="task-set to toggle")
@click.option("--credentials", "cred_file", type=str, default="firebase-admin.json", help="firebase credentials file")
def disable(taskset, cred_file):
    """disable a task-set"""
    set_taskset_enabled(taskset, False, cred_file=cred_file)

@click.group()
def cli():
    """Firebase annotation cli"""
    pass

cli.add_command(add_tasks, "upload")
cli.add_command(transform, "transform")
cli.add_command(assign, "assign")
cli.add_command(enable, "enable")
cli.add_command(disable, "disable")

if __name__ == "__main__":
    cli()
