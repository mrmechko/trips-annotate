#!/usr/bin/env python3

import json
import click

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


def get_db(cred_file="firebase-admin.json"):
    cred = credentials.Certificate(cred_file)
    firebase_admin.initialize_app(cred, {
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


    for d in data:
        doc_ref.add(dict(d, taskset=taskset["name"])) # think I can optimize this?

    click.echo("added %d new tasks." % len(data))
    return 1


def get_sentence(taskset, id):
    with open("%s/%d/parse.json" % (taskset, id)) as parse:
        return json.load(parse)["sentence"]

@click.command()
@click.option("--task-set", "taskset", type=str, help="output folder for prepare.sh")
@click.option("--type", "type_", default="a_b_parse", type=str, help="task_type")
@click.option("--coverage", "coverage", default=3, type=int, help="minimum number of annotators requested")
@click.option("--agreement", "agreement", default=0.0, type=float, help="minimum amount of agreement required")
@click.option("--active/--no-active", "active", default=True)
def transform(taskset, type_="a_b_parse", coverage=3, agreement=0, active=True):
    # Read in data from prepare.sh and create a task object
    fname = "%s/data.json" % taskset
    with open(fname) as inp:
        dataset = json.load(inp)
    tasks = [{
        "annotations": [],
        "data": dict(data, type=type_, sentence=get_sentence(taskset, data["id"])),
        "requirements": {
            "agreement": agreement,
            "coverage": coverage,
            "annotators": []
        },
        "is_active": active
    } for data in dataset]
    res = dict(name=taskset, tasks=tasks, definition=dict(type=type_, items=len(tasks), groups=dict()))
    click.echo(json.dumps(res, indent=2))

@click.command()
@click.option("--task-set", "taskset", type=str, help="The task set to assign")
@click.option("--type", "type_", type=str, help="worker type to assign the task to", default="researcher")
@click.option("--set", "s", type=int, help="worker set to assign the task to", default=0)
def assign(taskset, type_, s):
    print(taskset, type_, s)


@click.group()
def cli():
    pass

cli.add_command(add_tasks, "upload")
cli.add_command(transform, "transform")
cli.add_command(assign, "assign")

if __name__ == "__main__":
    cli()
