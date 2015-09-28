from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch_dsl import Mapping, String, Search

es = Elasticsearch()
ies = IndicesClient(es)

ies.delete('test')
ies.create('test')
ies.close('test')

ies.put_settings(index='test', body={
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



m = Mapping('test')
m.field('f', String())
m.save(index='test', using=es)

ies.open(index='test')

es.index('test', 'test', {
    'f': 'gastric adenocarcinomas',
})

es.index('test', 'test', {
    'f': 'gastric adenocarcinoma',
})

es.index('test', 'test', {
    'f': 'carcinomas',
})

es.index('test', 'test', {
    'f': 'carcinoma',
})


list(Search(es).query('match', f='carcinomas').execute())