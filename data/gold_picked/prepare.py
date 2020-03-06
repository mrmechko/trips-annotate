#!/usr/bin/env python3

from tripsbleu.diff import trips_diff
from tripscli.parse.web.dot import as_dot
import click
from tqdm import tqdm
import json, random, os
from soul.files import ls

from tripsbleu.trips import get_gold, get_nth_parse
from tripsbleu.ngrams import compare_trips

def make_url(repo, output_dir):
    return "http://raw.githubusercontent.com/%s/master/data/%s/" % (repo, output_dir)
   
@click.command()
@click.option("--input-dir", "-i", "input_", prompt=True)
@click.option("--style", "-s", "style", default="", type=str)
@click.option("--output-dir", "-o", "output_dir", prompt=True)
@click.option("--rep", "-r", "repo", prompt=True)
def render(input_, style, output_dir, repo):
    def get_parse(parse, id):
        res = json.load(open(parse))
        # find some alternatives that are more interesting than the average bear
        try:
            alt = get_most_interesting_alternatives(res)
        except:
            print("error finding most interesting: %s" % parse)
            return None
        if not alt or len(alt) != 3:
            return None
        # convert parses to graphs
        output = "%s/%d" % (output_dir, id)

        gold = get_gold(res)
        first = trips_diff(gold, get_nth_parse(res, alt["first"]))
        first_r = trips_diff(get_nth_parse(res, alt["first"]), gold)
        second = trips_diff(gold, get_nth_parse(res, alt["second"]))
        second_r = trips_diff(get_nth_parse(res, alt["second"]), gold)
        os.mkdir(output)
        as_dot(first_r, format=style).graph().render("%s/gold_first" % output, cleanup=True, format="svg")
        as_dot(first, format=style).graph().render("%s/first" % output, cleanup=True, format="svg")
        as_dot(second, format=style).graph().render("%s/second" % output, cleanup=True, format="svg")
        as_dot(second_r, format=style).graph().render("%s/gold_second" % output, cleanup=True, format="svg")

        return dict(id=id,
               reference=make_url(repo, output),
               data=alt,
               source=parse,
               sentence=res["sentence"])
    with open("%s/data.json" % output_dir, 'w') as f:
        json.dump([get_parse(p, i) for i, p in enumerate(ls(input_)[:20]) if p], f)

def get_most_interesting_alternatives(data):
    """Eventually want to select varieties of parses"""
    if data["annotation"]["parser"] != "STEP":
        return None
    gold = get_gold(data)
    if not gold:
        return None
    other = [i for i in range(len(data["alternatives"]))]
    other = sorted(other, key=lambda x: compare_trips(gold, get_nth_parse(data, x)))
    if len(other) < 2:
        return None
    random.shuffle(other[2:])
    return {
        "gold": data["annotation"]["judgement"],
        "first": other[0],
        "second": other[1]
    }

@click.group()
def cli():
    pass

cli.add_command(render, "render")

if __name__ == "__main__":
    cli()
