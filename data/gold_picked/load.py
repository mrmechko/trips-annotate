from lxml import etree
import urllib
from tripscli.parse.web import read as read_xml
import json
from tqdm import tqdm

class GoldPick:
    def __str__(self):
        return "%s.%s.%s-%d: %s" % (self.judge, self.timestamp, self.parser, self.judgement, self.sentence)

    def __init__(self, timestamp, parser, judge, judgement, sentence, link):
        self.timestamp = timestamp
        self.parser = parser
        self.judge = judge
        if judgement == "none":
            self.judgement = -1;
        else:
            self.judgement = judgement
        self.sentence = sentence
        self.link = link

    def fname(self):
        return "%s.%s.json" % (self.judge, self.timestamp)

    def json(self):
        xml = urllib.request.urlopen(self.link)
        data = xml.read()
        xml.close()
        res = read_xml.to_json(data)[0]
        res["annotation"] = dict(judge=self.judge, parser=self.parser, timestamp=self.timestamp, link=self.link, judgement=self.judgement)
        return res

    @staticmethod
    def from_tr(row, baseurl="http://trips.ihmc.us/parser/"):
        cols = [c for c in row.iterchildren()]
        ts = cols[0].text
        parser = cols[1].text
        judge = cols[2].text
        judgement = cols[3].attrib["class"].split(" ")[1].split("-")[-1]
        if judgement != "none":
            judgement = int(judgement)
        sentence = cols[4].text
        link = baseurl + cols[5][0].attrib["href"][3:]
        return GoldPick(ts, parser, judge, judgement, sentence, link)

rows = [row for row in etree.HTML(open("table.html").read()).find("body/table").iterchildren()][2:]
#[r.text for r in rows[0].iterchildren()]

gold = [GoldPick.from_tr(row) for row in rows]
# [str(x) for x in gold]

for g in tqdm(gold):
    fname = "data/" + g.fname()
    with open(fname, 'w') as f:
        json.dump(g.json(), f, indent=2)
