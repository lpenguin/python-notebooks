
# coding: utf-8

# In[2]:

import pandas as pd
import pymongo

db_meta = pymongo.MongoClient().scraper_meta
db_pa = pymongo.MongoClient().pharm_atlas


# In[3]:

m = pd.read_pickle('./data/set_with_meta.pickle')
disease_doid = pd.DataFrame(m.groupby('disease')['doid'].first())
disease_doid[:10]


# In[5]:

tr_set = pd.read_csv('./data/out_training_set_exp.csv', sep=';')
tr_set.columns


# In[6]:

tr_set.set_index('sample_accession', inplace=True)


# In[69]:

PAGE_SIZE = 1000

series_by_samples = tr_set.reset_index().groupby('sample_accession')['accession'].apply(set)

db_pa.samples.remove({})
for i in range(0, tr_set.shape[0], PAGE_SIZE):
    accessions = list(tr_set.index[i: i+PAGE_SIZE])
    samples_c = db_meta.samples.find({'accession': {'$in': accessions}})
    samples_b = []
    for sample in samples_c:
        sample['disease'] = tr_set.loc[sample['accession']].disease
        sample['tissue'] = tr_set.loc[sample['accession']].tissue
        sample['series'] = list(series_by_samples.loc[sample['accession']])
        samples_b.append(sample)
    db_pa.samples.insert_many(samples_b)
    
tr_set.shape


# In[8]:

db_pa.samples.count()


# In[71]:

PAGE_SIZE = 1000

samples_by_series = tr_set.reset_index().groupby('accession')['sample_accession'].apply(set)
db_pa.series.remove({})
series = list(tr_set['accession'].unique())
for i in range(0, len(series), PAGE_SIZE):
    accessions = series[i: i+PAGE_SIZE]
    c = list(db_meta.series.find({'accession': {'$in': accessions}}))
    bucket = []
    for s in c:
        s['samples'] = list(samples_by_series.loc[s['accession']])
        bucket.append(s)
    db_pa.series.insert_many(bucket)
    
db_pa.series.count()


# In[72]:

samples_c = list(db_pa.samples.find())
series_c = list(db_pa.series.find())


# In[11]:

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk

es = Elasticsearch()
es_i = IndicesClient(es)




# In[12]:

get_ipython().system("curl -XDELETE 'http://localhost:9200/series/'")
get_ipython().system("curl -XDELETE 'http://localhost:9200/samples/'")


# In[73]:

import json
from bson import json_util

get_ipython().system('mkdir -p data/pharm-atlas/')


json.dump(samples_c, open('data/pharm-atlas/samples.json', 'w'), default=json_util.default)
json.dump(series_c, open('data/pharm-atlas/series.json', 'w'), default=json_util.default)


# In[25]:

series_mapping = {
        'series': {
                'properties': {
                    'organism': {'type': 'string', "index" : "not_analyzed"},
                    'title': {'type': 'string'},
                    'accession': {'type': 'string', "index" : "not_analyzed"},
                    'summary': {'type': 'string'},
                    'overall_design': {'type': 'string'},
                    'samples': {'type': 'string', "index" : "not_analyzed"},
                    'platforms': {'type': 'string', "index" : "not_analyzed"},
                    'type': {'type': 'string', "index" : "not_analyzed"}
                }            
        }
}

samples_mapping = {
        'samples': {
                'properties': {
                    'organism': {'type': 'string', "index" : "not_analyzed"},
                    'source_name': {'type': 'string'},
                    'sample_type': {'type': 'string'},
                    'description': {'type': 'string'},
                    'disease': {'type': 'string', "index" : "not_analyzed"},
                    'platform': {'type': 'string', "index" : "not_analyzed"},
                    'series': {'type': 'string', "index" : "not_analyzed"},
                    'accession': {'type': 'string', "index" : "not_analyzed"},
                }            
        }
}
es.indices
def import_index(client, file_name, index, doc_type, mapping, delete=False):
    def to_action(_index, _type, _source):
        if '_id' in _source:
            del _source['_id']
        return {
            '_index': _index,
            '_type': _type,
            '_source': _source
        }


    if delete:
        client.indices.delete(index=index, ignore=[400, 404])
        
    client.indices.create(index=index, ignore=400)        
    
    if mapping:
        client.indices.put_mapping(index=index, doc_type=doc_type, body=mapping)
    
    collection = json.load(open(file_name))

    return bulk(client, map(lambda s: to_action(index, doc_type, s), collection))


# In[28]:

import_index(es, 'data/pharm-atlas/series.json', 'series', 'series', series_mapping, delete=True)
import_index(es, 'data/pharm-atlas/samples.json', 'samples', 'samples', samples_mapping, delete=True)


# In[29]:

es_i.get_mapping(index='series', doc_type='series')


# In[66]:

es.search(index='series', body={
        'query': {
            'term': {
                'organism': 'Homo sapiens'
            }
        }, 
        "fields" : ['accession']
    })


# In[70]:

es.search(index='samples', body={
        'query': {
            'terms': {
                'series': ['GSE3744', 'GSE10810']
            }
        }, 
        "fields" : ['accession']
    })


# In[75]:

es.search(index='series', body={
        'size': 0,
        "aggs" : {
            "series" : {
                "terms" : { "field" : "platforms" }
            }
        }
    })
#  , GSE10810 


# In[132]:

series_field_defs = {
    'organism': {'type': 'term'},
    'title': {'type': 'match'},
    'accession': {'type': 'term'},
    'summary': {'type': 'match'},
    'overall_design': {'type': 'match'},
    'samples': {'type': 'term'},
    'platforms': {'type': 'term'},
    'type': {'type': 'term'}
}

samples_field_defs = {
    'organism': {'type': 'term'},
    'source_name': {'type': 'match'},
    'sample_type': {'type': 'match'},
    'description': {'type': 'match'},
    'disease': {'type': 'term'},
    'platform': {'type': 'term'},
    'series': {'type': 'term'},
    'accession': {'type': 'term'},
}


def query(predicates):
    series_query = []
    samples_query = []
    for c_p, value in predicates.items():
        c, p = c_p.split('.')
        
        if c == 'series':
            t = series_field_defs[p]['type']
            query = series_query
        elif c == 'samples':
            t = samples_field_defs[p]['type']
            query = samples_query
            
        if t == 'term':
            query.append({'term': {p: value}})
        elif t == 'match':
            query.append({'match': {p: value}})
        
    return series_query, samples_query


def must_query(index, doc_type, args):
#     fields = fields or []
    return  es.search(index=index, doc_type=doc_type, body={
             'query' : {'bool': {'must': args}}
        })

def accession_query(index, doc_type, args):
    return [hit.get('fields')['accession'][0] for hit in es.search(index=index, doc_type=doc_type, body={
             'query' : {'bool': {'must': args}},
             'fields': ['accession']
        })['hits']['hits'] ]


def search(predicates):
    series_query, samples_query = query(predicates)
    
    series_accessions = []
    if len(series_query) > 0:
        series_accessions = accession_query('series', 'series', series_query)
        
    if len(series_query) > 0:
        if len(series_accessions) == 0:
            return None
        samples_query.append({'terms': {'series': series_accessions}})
    
    return must_query(args=samples_query, index='samples', doc_type='samples')
        
    
search({
        'series.accession': "GPL96"
    })


# In[37]:

import pprint

pprint.pprint(es.search(index='series', size=1)['hits']['hits'][0]['_source'])


# In[43]:

get_ipython().magic('run ~/Sources/PharmAtlas/PharmAtlas/metadata/metadata.py')


# In[39]:

get_search_fields()


# In[49]:




# In[74]:

get_ipython().magic('run ~/Sources/PharmAtlas/PharmAtlas/metadata/rawdata.py')
get_samples(['GSM496090', 'GSM496091', 'GSM496092'], '/Users/nikita/Sources/PharmAtlas/Data/raw')


# In[ ]:



