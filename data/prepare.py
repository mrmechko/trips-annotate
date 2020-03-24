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
@click.option("--repo", "-r", "repo", prompt=True)
@click.option("--gold-sim", "-g", "gold_sim", prompt=True, help="comma-separated range for candidate-gold similarity", default="0,1.0")
@click.option("--candidate-sim", "-c", "candidate_sim", prompt=True, help="comma-separated range for candidate-candidate similarity", default="0,1.0")
@click.option("--use-reparsed", "-u", "reparsed", help="Use reparsed values for candidates instead of original")
def render(input_, style, output_dir, repo, gold_sim, candidate_sim, reparsed=False):
    """given an input_ directory of gold-picked parses, a json style file, an output_dir and a target repo
    1. select gold-picked annotations with interesting properties (ie gold and alternatives are moderately separated)
    2. generate an annotation task
    3. write it all into output_dir
    """
    gs = sorted([float(x) for x in gold_sim.split(",")])
    cs = sorted([float(x) for x in candidate_sim.split(",")])
    def get_parse(parse, id):
        res = json.load(open(parse))
        # find some alternatives that are more interesting than the average bear
        try:
            alt = get_most_interesting_alternatives(res, gs[0], gs[1], cs[0], cs[1], reparsed)
        except:
            print("error finding most interesting: %s" % parse)
            return None
        print(alt)
        if not alt or len(alt) != 4:
            return None
        # convert parses to graphs
        output = "%s/%d" % (output_dir, id)

        gold = get_gold(res)
        target_list = "alternatives"
        if reparsed:
            target_list = "reparsed"
        first, second, both = three_way_diff(gold,
                                             get_nth_parse(res, alt["first"], target_list),
                                             get_nth_parse(res, alt["second"], target_list))
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

def get_most_interesting_alternatives(data, min_gold_sim=0, max_gold_sim=1.0, min_candidate_sim=0.0, max_candidate_sim=1.0, reparsed=False):
    """Eventually want to select varieties of parses
    max_gold_sim, min_gold_sim -> how similar/dissimilar a candidate should be from gold
    max_candidate_sim, min_candidte_sim -> how similar/dissimilar candidates shoud be from each other

    We want cases where
    1. the parses are distributed evenly
    2. the candidates are similar to each other but not to the reference
    3. one candidate is similar to the reference and one candidate is not
    4. all three are similar to each other

    proposed range:

    similar ~=        [1.0-0.9]
    moderately similar ~= [0.9-0.7]
    moderately dissimilar ~=  [0.7-0.5]
    dissimilar ~=                 [0.5-0.0]
    """
    print(max_gold_sim, min_gold_sim, max_candidate_sim, min_candidate_sim)
    if data["annotation"]["parser"] != "STEP":
        print("data is not step")
        return None
    gold = get_gold(data)
    if not gold:
        print("no gold found")
        return None
    target_list = "alternatives"
    if reparsed:
        target_list = "reparsed"
    other = [(i, compare_trips(gold, get_nth_parse(data, i, target_list))) for i in range(len(data[target_list]))]
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
        first_ = get_nth_parse(data, first, target_list)
        for second, score2 in other[1:]:
            second_ = get_nth_parse(data, second, target_list)
            if min_candidate_sim < compare_trips(first_, second_) < max_candidate_sim:
                return dict(gold=get_gold(data, True), first=first, second=second, reparsed=reparsed)
    print("candidates too similar")
    return None

@click.group()
def cli():
    pass

cli.add_command(render, "render")

if __name__ == "__main__":
    cli()
