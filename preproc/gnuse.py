# -*- coding: utf-8 -*-
#%%
import pandas as pd
from sh import find
#%%

from os.path import dirname, basename
import numpy as np

def read_value(line):
    return float(line.rstrip('\n').split(' ')[1].strip('"')) if line else np.nan
    
def read_median(file_name):
    task_name = basename(dirname(dirname(file_name)))
    series, platform = task_name.split('_')
    sample = basename(file_name)
    with open(file_name) as f:
        f.readline()
        median = read_value(f.readline())
        IQR = read_value(f.readline())
        p95 = read_value(f.readline())
        p99 = read_value(f.readline())
#        if not line:
#            median = np.nan
#        else:
#            median = float(line.rstrip('\n').split(' ')[1].strip('"'))
    return dict(series=series, 
                sample=sample,
                platform=platform, 
                median=median,
                IQR=IQR,
                p95=p95,
                p99=p99)
    
#read_median('data/preproc/data/GSE27564_GPL1261/out/GSM682247.gnuse')

#%%

l = [f.rstrip('\n') for f in find('./data/preproc/data', '-name', '*.gnuse')]

#%%

medians = pd.DataFrame([read_median(x) for x in l])