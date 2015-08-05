
# coding: utf-8

# In[2]:

import pandas as pd


# In[3]:

meta_set = pd.read_pickle('../data/set_with_meta.pickle')
meta_set[:2]


# In[4]:

meta_set[meta_set['accession'] == 'GSE21422']


# In[5]:

meta_set['disease'] = meta_set['disease'].map(lambda x: x.strip())


# In[7]:

from elasticsearch import Elasticsearch
es = Elasticsearch(host='scraper.now.im', port='8080')

res = es.search(index="series", body={"query": {"match_all": {}}})
print("Got %d Hits:" % res['hits']['total'])


# In[35]:

def search_phrase(phrase):
#     {
#   "query": {
#     "match": {
#       "title": {
#         "query": "invasive ductal carcinoma",
#         "type": "phrase"
#       }
#     }
#   },
#   "aggs": {}
# }
    res = es.search(index='series', body={
            'query': {
                'match': {
                    'title': {
                        'query': phrase,
                        'operator': 'and'
                    }
                }
            }
        })
    hits = res['hits']['hits']
    for hit in hits:
        yield hit['_score'], hit['_source']['accession']
    


# In[36]:

list(search_phrase('invasive ductal carcinoma'))


# In[80]:

diseases = list(meta_set['disease'].unique())
len(diseases)


# In[82]:

from collections import defaultdict

annotations = defaultdict(list)
for disease in diseases:
    for score, accession in search_phrase(disease):
        annotations[accession].append((score, disease))
        
len(annotations)


# In[86]:

meta_set.accession.unique().shape


# In[6]:

series_diseases = meta_set.groupby('accession')['disease'].apply(set)
series_diseases[:10]


# In[91]:

annotations_v = []
annotations_i = []
for accession, dis in annotations.items():
    annotations_v.append( set(dis))
    annotations_i.append(accession)

annotations_s = pd.DataFrame(pd.Series(data=annotations_v, index=annotations_i, name='diseases'))
annotations_s[:10]


# In[92]:

scores = pd.DataFrame.from_records([series_diseases]).T
scores.columns = ['diseases_correct']
scores = pd.merge(scores, annotations_s, left_index=True, right_index=True)
scores[:10]


# In[93]:

def match(diseases_correct, diseases):
    m = 0
    for score, d in diseases:
        if d in diseases_correct:
            m += 1
            
    return m/len(diseases_correct), (len(diseases) - m)/len(diseases)

scores['match'] = scores.apply(lambda row: match(row['diseases_correct'], row['diseases'])[0], axis=1)
scores['garb'] = scores.apply(lambda row: match(row['diseases_correct'], row['diseases'])[1], axis=1)
scores['str.diseases_correct'] = scores['diseases_correct'].map(', '.join)
scores['str.diseases'] = scores['diseases'].map(lambda x: ', '.join(a[1] for a in x))
scores[:10]


# In[94]:

scores[(scores['match'] < 1.0)][['match','garb','str.diseases_correct','str.diseases']]


# In[95]:

scores[(scores['garb'] > 0.0)][['match','garb','str.diseases_correct','str.diseases']]


# In[96]:

print(scores[(scores['garb'] > 0.0) |(scores['match'] < 1.0)].shape[0], scores.shape[0])


# In[1]:

scores.loc['GSE32924']['str.diseases']


# In[11]:

series_diseases[series_diseases.map(lambda x: len(x) == 1)].shape, series_diseases.shape


# In[9]:



