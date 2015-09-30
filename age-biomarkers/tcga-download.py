# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 20:09:34 2015

@author: nikita
"""
#%%
import requests as req
from lxml import html
from os.path import join, basename


root_url = 'http://gdac.broadinstitute.org/runs/stddata__2015_06_01/data/'

def get_elems(url):
    page = req.get(url)
    tree = html.fromstring(page.text)
    return [(a.get('href'), a.text) for a in tree.xpath('//table/tr/td/a') 
            if a.text != 'Parent Directory']
    
elems = get_elems(root_url)
elems

#%%
def download_tar(disease, date, tar_name):
    print("Download tar", disease, date, tar_name)
    url = join(root_url, disease, date, tar_name)
    r = req.get(url, stream=True)

    with open(tar_name, 'wb') as fd:
        for chunk in r.iter_content(1024):
            fd.write(chunk)
        
def download_date(disease, date):
    print("Download date", disease, date)
    url = join(root_url, disease, date)
    elems = get_elems(url)

    tar_name = next((x for x in elems 
                    if 'Merge_Clinical' in x[0] and
                        x[0].endswith('.tar.gz')), (None,None))[0]
    print(tar_name)
    download_tar(disease, date, tar_name)
    
def download_disease(name):
    print("Download disease", name)
    url = join(root_url, name)
    date = get_elems(url)[0][0]
    download_date(name, date)
    

for e in elems:
    download_disease(e[1])
