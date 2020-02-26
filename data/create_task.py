#!/usr/bin/env python3

import json
import click

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
    res = [{
        "taskset": taskset,
        "annotations": [],
        "data": dict(data, type=type_, sentence=get_sentence(taskset, data["id"])),
        "requirements": {
            "agreement": agreement,
            "coverage": coverage,
            "annotators": []
        },
        "is_active": active
    } for data in dataset]
    click.echo(json.dumps(res, indent=2))

if __name__ == "__main__":
    transform()
