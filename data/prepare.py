#!/usr/bin/env python3

from tripsbleu.diff import three_way_diff
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
    """given an input_ directory of gold-picked parses, a json style file, an output_dir and a target repo
    1. select gold-picked annotations with interesting properties (ie gold and alternatives are moderately separated)
    2. generate an annotation task
    3. write it all into output_dir
    """
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
        first, second, both = three_way_diff(gold,
                                             get_nth_parse(res, alt["first"]),
                                             get_nth_parse(res, alt["second"]))
        os.mkdir(output)
        as_dot(both, format=style).graph().render("%s/gold_first" % output, cleanup=True, format="svg")
        as_dot(first, format=style).graph().render("%s/first" % output, cleanup=True, format="svg")
        as_dot(second, format=style).graph().render("%s/second" % output, cleanup=True, format="svg")
        as_dot(both, format=style).graph().render("%s/gold_second" % output, cleanup=True, format="svg")

        return dict(id=id,
               reference=make_url(repo, output),
               data=alt,
               source=parse,
               sentence=res["sentence"])
    with open("%s/data.json" % output_dir, 'w') as f:
        json.dump([get_parse(p, i) for i, p in enumerate(ls(input_)) if p], f)

def get_most_interesting_alternatives(data, max_gold_sim=1.0, min_gold_sim=0.0, max_candidate_sim=1.0, min_candidate_sim=0.0):
    """Eventually want to select varieties of parses
    max_gold_sim, min_gold_sim -> how similar/dissimilar a candidate should be from gold
    max_candidate_sim, min_candidte_sim -> how similar/dissimilar candidates shoud be from each other
    """
    if data["annotation"]["parser"] != "STEP":
        print("data is not step")
        return None
    gold = get_gold(data)
    if not gold:
        print("no gold found")
        return None
    other = [(i, compare_trips(gold, get_nth_parse(data, i))) for i in range(len(data["alternatives"]))]
    other = sorted(other, key=lambda x: x[1])
    # remove identical matches:
    other = [x for x in other if min_gold_sim < x[1] < max_gold_sim]
    if len(other) < 2:
        print("no alt found")
        return None
    random.shuffle(other[2:])
    # make sure the two candidates aren't identical
    # We have already shuffled them to ensure that they are randomly selected
    for first, score1 in other[:-1]:
        first_ = get_nth_parse(data, first)
        for second, score2 in other[1:]:
            second_ = get_nth_parse(data, second)
            if min_candidate_sim < compare_trips(first_, second_) < max_candidate_sim:
                return dict(gold=get_gold(data, True), first=first, second=second)
    print("candidates too similar")
    return None

@click.group()
def cli():
    pass

cli.add_command(render, "render")

if __name__ == "__main__":
    cli()
