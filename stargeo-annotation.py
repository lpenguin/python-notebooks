
# coding: utf-8

# In[8]:

import pymongo
import pandas as pd

db = pymongo.MongoClient().stargeo
# In[10]:

samples = pd.DataFrame(list(db.samples.find()))
print(samples.shape)
samples[:5]
# In[106]:

samples['tags'] = samples['tags'].map(lambda tags: set(t.strip() for t in tags))
samples[:10]


# In[25]:

tags_set = set()
for tags in samples.tags:
    for t in tags:
        tags_set.add(t)

# In[112]:

import numpy as np
t = pd.read_csv('data/tags.csv')
t.columns = ['id', 'tag', 'disease']
t['disease'] = t['disease'].map(lambda x: x.lower().replace("'", '').strip())
t['disease'] = t['disease'].map(lambda x: np.nan if x == '' else x)
t['disease'].value_counts().shape
t['tag'] = t['tag'].map(lambda x: x.lower())

#%%
def contains_values(string, values):
    for value in values:
        if value in string:
            return True
    return False
    

t_cleaned = (t[t['tag'].map(lambda x: not contains_values(x, [
        'control', 'ctrl', 'normal', 'non_tumour', 'non_tumor']))]
            .dropna(subset=['disease'])
            .set_index('tag'))
        
#%%
tag_to_disease = {}
for tag, disease in t_cleaned['disease'].items():
    tag_to_disease[tag.strip()] = disease.strip()


# In[120]:

def to_disease(tags):
    result = set(tag_to_disease[tag.lower()] for tag in tags if tag.lower() in tag_to_disease)
    return result if result else np.nan
    
samples['disease'] = samples['tags'].map(to_disease)
samples[:3]

#%%
samples_with_disease = samples.dropna(subset=['disease'])

#%%
from lib import pandas_monkey
pandas_monkey.pandas_patch()
#%%
se = samples_with_disease.expand('disease')

# In[134]:

def make_train_set(samples):
#    samples = samples[samples['disease'].map(lambda x: len(x) > 0)]
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
out = make_train_set(se)
out.to_csv('data/stargeo_train_set.csv', set=';')

#%%
se_series = se.drop_duplicates(subset=['series', 'disease'])

#%%
se_series.to_pickle('data/se_series.pickle')



