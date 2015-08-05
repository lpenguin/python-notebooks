
# coding: utf-8

# In[8]:

import pymongo
import pandas as pd

db = pymongo.MongoClient().stargeo


# In[10]:

samples = pd.DataFrame(list(db.samples.find()))
print(samples.shape)
samples[:5]


# In[25]:

tags_set = set()
for tags in samples.tags:
    for t in tags:
        tags_set.add(t)
set(t.lower().replace('_non_tumour', '').replace('_tumour', '').replace('_tumor', '') for t in tags_set if ('control' not in t.lower() and 'ctrl' not in t.lower()))


# In[33]:

# t = pd.DataFrame(data=list(tags_set), columns=['tag'])
# t['disease'] = ''
# t.to_csv('data/tags.csv', sep=',')GSE38246 


# In[89]:

samples[samples.tags.map(lambda x: 'UC' in x)].groupby('series').first()


# In[112]:

import numpy as np
t = pd.read_csv('data/tags.csv')
t.columns = ['id', 'tag', 'disease']
t['disease'] = t['disease'].map(lambda x: x.lower().replace("'", '').strip())
t['disease'] = t['disease'].map(lambda x: np.nan if x == '' else x)
t['disease'].value_counts().shape


# In[ ]:




# In[106]:

samples['tags'] = samples['tags'].map(lambda tags: set(t.strip() for t in tags))
samples[:10]


# In[117]:

# t.set_index('tag', inplace=True)
t[:10]
tag_to_disease = {}
for tag, disease in t.set_index('tag').disease.dropna().items():
    tag_to_disease[tag.strip()] = disease.strip()


# In[120]:

def to_disease(tags):
    return set(tag_to_disease[tag] for tag in tags if tag in tag_to_disease)
samples['disease'] = samples['tags'].map(to_disease)
samples[:10]


# In[134]:

def make_train_set(samples):
    samples = samples[samples['disease'].map(lambda x: len(x) > 0)]
    print('Good samples {}'.format(samples.shape))
    db = pymongo.MongoClient().scraper_meta
    
    series_accession = list(samples['series'].unique())
    samples_accession = list(samples['accession'].unique())
    series = pd.DataFrame(list(db.series.find({'accession': {'$in': series_accession}})))
    samples_c = pd.DataFrame(list(db.samples.find({'accession': {'$in': samples_accession}})))
    samples_c = samples_c[['accession', 'title', 'description', 'source_name']]
    samples_c.columns = ['sample_accession', 'sample_title',
       'sample_description', 'sample_source_name']
    
    series = series[['accession', 'summary', 'title', 'overall_design']]
    
    samples = samples[['accession', 'series', 'disease']]
    samples.columns = ['sample_accession', 'accession', 'disease']
    
    _t = pd.merge(samples, samples_c)
    _t = pd.merge(_t, series)
    _t['disease'] = _t['disease'].map(','.join)
    _t['tissue'] = np.nan
    _t['norm_or_tumour'] = np.nan
    
    _t = _t[['accession', 'summary', 'title', 'overall_design',
       'disease', 'tissue', 'sample_accession', 'sample_title',
       'sample_description', 'norm_or_tumour', 'sample_source_name']]
    return _t
#     train_set = pd.merge(samples, series, left_on='series')
out = make_train_set(samples)
out.to_csv('data/stargeo_train_set.csv', set=';')


# In[124]:

ts = pd.read_csv('data/out_training_set_exp.csv', sep=';')
print(ts.columns)
ts[:5]

