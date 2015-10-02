# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 14:39:40 2015

@author: nikita
"""

#%%

from pymongo import MongoClient

db = MongoClient().scraper_meta

#%%
import re

manufacturer_re = re.compile('.*agilent.*', re.IGNORECASE)
agilent_platforms = list(db.platforms.find({'manufacturer': manufacturer_re,
                                            'organism': 'Homo sapiens'}, 
                                           {'manufacturer': 1, 
                                            'accession': 1, '_id': 0}))
                                           
#%%

agilent_2ch = list(filter(lambda p: list(db.samples.find(
                                {'platform': p['accession'], 
                                 'channel': 2}).limit(1)), agilent_platforms))
                        
                                  
#%%
import json

with open('data/agilent_2ch.json', 'w') as f:
    json.dump(agilent_2ch, f)
    
#%%

counts = list(map(lambda p: (p['accession'], db.samples.count({'platform': p['accession'],
                                                              'channel': 1   })), agilent_2ch))


#%%
counts = sorted(counts, key=lambda x: x[1], reverse=True)
    