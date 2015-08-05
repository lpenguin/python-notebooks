# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 21:45:06 2015

@author: nikita
"""
#%%
import os
for dir, dirs, files in os.walk('.'):
#    if dir != '.' and dir.startswith('.'):
#        continue
    for file in files:
        if file.endswith('.ipynb'):
            full_path = os.path.join(dir, file)
#            print(full_path)
            !echo ipython3 nbconvert --to=python $full_path
#    for file in files:
#        if file.endswith('.ipynb'):
#            print(file)
#%%
!ipython nbconvert --to=python ./misc/pandas-monkey.ipynb