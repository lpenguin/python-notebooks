# -*- coding: utf-8 -*-
#%%
import pandas as pd
import numpy as np
import json

mongo_file = './data/age-biomarkers/scraper.test.characteristics.age.ic.json'
#mongo_file_uc = './data/age-biomarkers/scraper.test.characteristics.age-uc.json'

def process_line(line):
    d = json.loads(line)
    accession = d['accession']
    chars = d['characteristics']
    title = d['title']
    description = d['description']
    organism = d['organism']
    
    age = chars['age'] if 'age' in chars else chars['Age']
    
    return dict(accession=accession,
                age=age if age else np.nan,
                characteristics=chars,
                title=title,
                description=description, 
                organism=organism)

def read_characteristics(file_name):
    with open(file_name) as f:
        return [process_line(line.rstrip("\n")) for line in f.readlines()]
        
chars = pd.DataFrame(read_characteristics(mongo_file))

#%%
def age_to_value(age):
    try:
        return float(age)
    except ValueError:
        return np.nan
        
chars['age_value'] = chars['age'].map(age_to_value)

#%%
chars.reset_index(inplace=True)

#%%
chars.fillna('', inplace=True)
chars['full_text'] = (chars['title'] + ' '+chars['description'].str.join(' ')).str.lower()
#%%
chars[chars['age_value'].notnull() &
     (chars['age_value'] > 0) &  # Strange negative values
     (chars['age_value'] < 200)] # 999 or inf
     
     
#%%
_a = 1
norm_words = ['normal', 'control', 'reference']

chars['norm'] = chars['full_text'].map(lambda x: any(w in x for w in norm_words))

#%%
chars['age_correct'] = (chars['age_value'].notnull() & 
     (chars['age_value'] > 0) & # Strange negative values
     (chars['age_value'] < 200)) # 999 or inf
#%%
good_ages = chars[chars['age_correct']].copy()

#%%
from lib import obo
import numpy as np

header, ontology = obo.read_obo('data/age-biomarkers/brenda-tissue-ontology.obo')


def find_in_ontology(text, ontology):
    global c
    global l
    c += 1
    if c % 500 == 0:
        print("#{} of {}".format(c, l))
    for item in ontology:
        try:
            name = item['name'][0]
            synonyms = [x.replace(' RELATED []', '').strip('"') for x in item['synonym']]
            names = [name] + synonyms
            id = item['id'][0]
            
            if any(x in text for x in [name] + synonyms):
                return name
            else:
                continue
        except IndexError:
            continue
    return np.nan
#find_in_ontology('corolla tube', ontology)

c = 0
l = good_ages.shape[0]
good_ages['tissue'] = good_ages.full_text.map(lambda x: find_in_ontology(x, ontology))
#%%
good_ages = good_ages[good_ages['accession'].isin(hacc)]
#%%
good_ages = good_ages[good_ages.age_value > 0].copy()
#%%
good_ages['age_group'] = pd.cut(good_ages.age_value, bins=8).astype(str)
good_ages['norm_count'] = good_ages['norm']
good_ages['count'] = good_ages['norm']
#%%
t = (good_ages
        .groupby(['tissue', 'age_group'])
#        .aggregate(np.sum)
        .agg({
                    'count': len,
                    'norm': lambda x: x.sum()/len(x),
                    'norm_count': sum,
                    })
        .reset_index())
t