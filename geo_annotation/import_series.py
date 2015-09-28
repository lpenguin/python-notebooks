# importing all series into elastic search index

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch_dsl import Mapping, String, Integer
from time import sleep


es = Elasticsearch()
ies = IndicesClient(es)

if ies.exists('series'):
    ies.delete('series')
ies.create('series')
sleep(1)
ies.close('series')
m = Mapping('series')

m.field('accession', String(index='not_analyzed'))
m.field('id', Integer())
m.field('organism', String(index='not_analyzed'))
m.field('platforms', String(index='not_analyzed'))
m.field('samples', String(index='not_analyzed'))

m.field('title', String())
m.field('summary', String())
m.field('overall_design', String())

m.save('series', using=es)

ies.put_settings(index='series', body={
    "analysis":{
      "analyzer":{
        "default":{
          "type":"custom",
          "tokenizer":"standard",
          "filter":[ "standard", "lowercase", "stop", "kstem" ]
        }
      }
    }
})
sleep(1)
ies.open('series')

import pymongo
db = pymongo.MongoClient().scraper_meta
db.series.count()
#%%
def fields(fields_list):
    return dict((f, 1) for f in fields_list)
    
series = list(db.series.find({}, fields(['accession', 'organism', 'platforms', 'samples', 'title', 'summary', 'overall_design'])))
#%%
actions = [dict(
            _index='series',
            _type='series',
            _source=dict([('id', int(s['accession'][3:]))] + list((k, v) for (k, v) in s.items() if k != '_id'))
            ) for s in series]


from elasticsearch.helpers import bulk

bulk(es, actions)