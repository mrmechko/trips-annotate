#!/usr/bin/env bash

# Create dir $2
# for each sentence, add a file $2/i with parse, alt1, alt2
mkdir $2
index=1
base=http://raw.githubusercontent.com/mrmechko/trips-annotate/master/data/$2/
echo id,reference,img_1,img_2 > ${2}/data.csv
while read sentence; do
    mkdir $2/$index
    trips-cli query -n 3 --text "'$sentence'" > $2/$index/parse.json
    trips-cli render -p $2/$index/parse.json -f svg -o $2/$index/best -s style.json
    trips-cli render -p $2/$index/parse.json -f svg -o $2/$index/first -a 0 -s style.json
    trips-cli render -p $2/$index/parse.json -f svg -o $2/$index/second -a 1 -s style.json
    echo $index,${base}${index}/best.svg\?sanitize=true,${base}${index}/first.svg\?sanitize=true,${base}${index}/second.svg\?sanitize=true >> ${2}/data.csv
    ((index+=1))
done < $1

mlr --c2j --jlistwrap cat $2/data.csv | jq > $2/data.json
