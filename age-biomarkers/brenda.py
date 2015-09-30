#%%
from rdflib import Graph
g = Graph()
g.parse('data/age-biomarkers/brenda-tissue-ontology.owl')

#%%
import pprint
for i, item in enumerate(g):
    pprint.pprint(item)
    if i > 100:
        break
    
#%%
from lib import obo
obo.read_obo('data/age-biomarkers/brenda-tissue-ontology.obo')