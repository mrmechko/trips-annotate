#!/usr/bin/env python3

import json
import click
from tqdm import tqdm

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


def get_db(cred_file="firebase-admin.json"):
    project_id = json.load(open(cred_file))["project_id"]
    cred = credentials.Certificate(cred_file)
    firebase_admin.initialize_app(cred, {
        'projectId': project_id
    })

    return firestore.client()

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
cli.add_command(assign, "assign")
cli.add_command(enable, "enable")
cli.add_command(disable, "disable")

if __name__ == "__main__":
    cli()
