# -*- coding: utf-8 -*-
#%%
import pymongo
db = pymongo.MongoClient().scraper_meta
db.samples.count()

#%%
c = db.samples.find({
    'characteristics.age': {'$exists': 1},
    'organism': 'Homo sapiens',
    'channel': {'$ne': 2}
}, {
    '_id': 0,
    'accession': 1,
    'characteristics': 1,
    'source_name': 1,
    'title': 1,
    'description': 1
})

res = list(c)

#%%
import json
with open('data/geo-annotation/samples.age.json', 'w') as f:
    json.dump(list(db.samples.find({
    #    'characteristics.age': {'$exists': 1},
        'organism': 'Homo sapiens',
        'channel': {'$ne': 2}
    }, {
        '_id': 0,
        'accession': 1,
        'characteristics': 1,
        'source_name': 1,
        'title': 1,
        'description': 1
    })), f)
    
#%%
# !gzip data/geo-annotation/samples.age.jso