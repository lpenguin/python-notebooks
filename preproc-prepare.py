
# coding: utf-8
#%%

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
#%%
        
platforms = ['GPL4133','GPL6480','GPL15849','GPL1708','GPL887','GPL4091','GPL9128','GPL7264','GPL11387','GPL8687','GPL6848','GPL2879','GPL5477','GPL8841','GPL10123','GPL4093','GPL11386','GPL10806','GPL8269','GPL10150','GPL8583','GPL15931','GPL4126','GPL10152','GPL16050','GPL2567','GPL9053','GPL14550','GPL5325','GPL10808','GPL13691','GPL9075','GPL8736','GPL885','GPL9777','GPL7504','GPL8693','GPL2873','GPL17077','GPL10734','GPL13953','GPL13607','GPL13685','GPL7015','GPL15560','GPL18623','GPL10481','GPL16280','GPL8737','GPL11068']
#%%
db.samples.count({'platform': {'$in': platforms}})


# In[1]:

(102393 * 300) / (50) / (3600 * 24)
# Семь суток будут препроцессится все семплы для аффиметриксовых платформ


# In[5]:

import pandas as pd

s = pd.DataFrame(list(db.samples.find({'platform': {'$in': platforms}}, 
                                      {'accession': 1, 'series': 1, 'platform': 1,
                                       'channel': 1})))\
    .expand('series')
s[:1]

#%%
s.drop_duplicates(subset=['accession'], inplace=True)

# In[7]:

samples_by_series = (s.groupby(['platform', 'series'])['accession']
  .apply(','.join).reset_index()
  .rename(columns={'series': 'accession', 'accession': 'samples'})
)
print(samples_by_series.shape)
samples_by_series[:5]


# In[10]:

samples_by_series.to_csv('series_agilent_2ch.csv', index=False, header=True)


