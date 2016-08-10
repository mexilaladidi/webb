#!/bin/sh
MYDATE=`date +%d%m%y`
python3 manage.py dumpdata polls > ./data/newest.json
python3 manage.py dumpdata polls > ./data/polls${MYDATE}.json
git add .
git commit -m 'l'
git push
