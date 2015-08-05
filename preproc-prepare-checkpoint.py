
# coding: utf-8

# In[1]:

get_ipython().magic('run ../misc/pandas-monkey.ipynb')

import pymongo
db = pymongo.MongoClient().scraper_meta


# In[4]:

platforms = ['GPL' + str(x) for x in [
            571, 1261,
            # 6244, getting strange errors
            6246, 90, 3921, 5175,
            # 5188, getting strange errors
            8321
        ]]
db.samples.count({'platform': {'$in': platforms}})


# In[1]:

(97405 * 300) / (50) / (3600 * 24)
# Семь суток будут препроцессится все семплы для аффиметриксовых платформ


# In[5]:

import pandas as pd

s = pd.DataFrame(list(db.samples.find({'platform': {'$in': platforms}}, 
                                      {'accession': 1, 'series': 1, 'platform': 1})))\
    .expand('series')
s[:1]


# In[7]:

samples_by_series = (s.groupby(['platform', 'series'])['accession']
  .apply(','.join).reset_index()
  .rename(columns={'series': 'accession', 'accession': 'samples'})
)
print(samples_by_series.shape)
samples_by_series[:5]


# In[10]:

samples_by_series.to_csv('series_affy.csv', index=False, header=True)


# In[12]:

get_ipython().system('ls -lah *.csv')


# In[13]:

get_ipython().system('scp *.csv npryanichnikov@ui2.computing.kiae.ru:/home/users/npryanichnikov/ls2/preproc/')


# In[42]:

get_ipython().system('git add ../elasitc-annotation/ ../misc/ ../stargeo-annotation.ipynb ../data/pharm-atlas/')


# In[44]:

get_ipython().system('git add preproc-prepare.ipynb')


# In[46]:

get_ipython().system("git commit -am 'preproc prepare'")


# In[47]:

get_ipython().system('git push origin master')

