# -*- coding: utf-8 -*-
#%%
import pymongo

db = pymongo.MongoClient().scraper_meta
#%%

def query(col, q, f=None):
    f = f or {}
    return list(col.find(q, f))

#%%

#se_files = query(db.series, {}, {'platforms': 1, 'supplementary_files': 1, 'accession': 1, '_id': 0})

#%%

import pandas as pd
import numpy as np

def flatten(xs, field_name, exp_fields):
    res = []
    for x in xs:        
        if x[field_name]:
            for v in x[field_name]:
                r = x.copy()
                
                if exp_fields:
                    del r[field_name]
                    for k in exp_fields:
                        r[k] = v[k]
                res.append(r)
        else:
            if exp_fields:
                for k in exp_fields:
                    x[k] = np.nan
                del x[field_name]
            res.append(x)
            
    return res
            
se_files = pd.DataFrame(flatten(flatten(query(db.series, {'data_source': 'geo'}, {'supplementary_files': 1, 'accession': 1, 'platforms': 1, '_id': 0})
, 'supplementary_files', ['name', 'type']), 'platforms', [])).set_index('accession')

#%%
se_files = pd.read_pickle('../data/preproc/se_files-res.pickle')