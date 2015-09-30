
# coding: utf-8

# In[8]:

import pandas as pd

def __dataframe_expand(self, column_name):
    bucket = []
    indexes = []
    for index, row in self.iterrows():
        for item in row[column_name]:
            indexes.append(index)
            row_copy = row.copy()
            row_copy[column_name] = item
            bucket.append(row_copy)
            
    return pd.DataFrame(data=bucket, index=indexes)

def pandas_patch():
    pd.DataFrame.expand = __dataframe_expand


# In[9]:
#
#pandas_patch()
#test = pd.DataFrame(data={'scalar': [1, 2, 3], 
#                          'list': [[11, 12], [21, 22], [31, 32]]})
#test.expand('list')

