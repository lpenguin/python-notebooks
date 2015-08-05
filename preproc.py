
# coding: utf-8

# In[2]:

import pandas as pd


# In[30]:

exprs = get_ipython().getoutput('ls -1 /Users/nikita/Data/preproc/GSE19864_GPL570/out/*.expr')
exprs[:10]


# In[35]:

samples = []
for e in exprs:
    samples.append(pd.read_csv(e, skiprows=1, sep=' ', names=['probe', 'expr']))


# In[36]:

samples[1][:10]


# In[37]:

for s in samples:
    print(s['expr'].mean())


# In[ ]:



