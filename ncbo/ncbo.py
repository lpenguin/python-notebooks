import requests as rq
import json
import os
from pprint import pprint

REST_URL = "http://localhost:8080"
API_KEY = "b14c384b-5b5c-4702-90a3-eb4a39119a1b"

def get_json(url):
    headers = {'Authorization': 'apikey token=' + API_KEY}
    res = rq.get(url, headers=headers)
    return res.json() if res.status_code == 200 else None

import pandas as pd
d = pd.read_pickle('../data/set_with_meta.pickle')
dropped = 0
def annotate(text):
    annotations = get_json(REST_URL + "/annotator?ontologies=DO&text=" + str(text))
    if annotations is None:
         return ''
    # pprint(annotations)
    #for annotation in annotations:
    if len(annotations) == 0 or len(annotations[0]['annotations']) == 0:
         return ''
    a = annotations[0]['annotations'][0]
  
    return a['text'].lower()

#print(annotate(d['title'].iloc[0]), d['disease_main'].iloc[0])
d['text'] = d['summary'] + ' ' + d['title'] + ' ' + d['overall_design']
d['aclass'] = d['text'].map(annotate)
d['matched_main'] = d['aclass'] == d['disease_main']
d['matched'] = d['aclass'] == d['disease']

print(d['matched'].sum(), d['matched_main'].sum(), d.shape[0], (d['aclass'] == '').sum())
d.to_pickle('../data.annot_res.pickle')
