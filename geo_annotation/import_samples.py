# importing all series into elastic search index

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch_dsl import Mapping, String, Integer
from elasticsearch.helpers import bulk
import pymongo
from time import sleep
from lib.utils import iter_bucket

es = Elasticsearch()
ies = IndicesClient(es)

index_name = 'samples'

if ies.exists(index_name):
    ies.delete(index_name)
ies.create(index_name)
sleep(1)
ies.close(index_name)
m = Mapping(index_name)

m.field('accession', String(index='not_analyzed'))
m.field('id', Integer())
m.field('organism', String(index='not_analyzed'))
m.field('platform', String(index='not_analyzed'))
m.field('series', String(index='not_analyzed'))

m.field('title', String())
m.field('description', String())
m.field('source_name', String())
# m.field('characteristics', String())
m.field('characteristics_raw', String())

m.save(index_name, using=es)

ies.put_settings(index=index_name, body={
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
ies.open(index_name)

db = pymongo.MongoClient().scraper_meta


def fields(fields_list):
    return dict((f, 1) for f in fields_list)

fields_list = list(m.to_dict()[index_name]['properties'].keys())
for bucket in iter_bucket(db.samples.find({}, fields(fields_list))):
    actions = [dict(
                _index=index_name,
                _type=index_name,
                _source=dict([('id', int(s['accession'][3:]))] + list((k, v) for (k, v) in s.items() if k != '_id'))
                ) for s in bucket]
    print('inserting')
    bulk(es, actions)
