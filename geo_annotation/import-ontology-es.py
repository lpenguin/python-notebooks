__author__ = 'nikita'
from importlib import reload
import misc.obo
reload(misc.obo)
from misc.obo import read_ontology

ontology = read_ontology('data/age-biomarkers/brenda-tissue-ontology.obo')

import elasticsearch
es = elasticsearch.Elasticsearch()
from elasticsearch.client import IndicesClient
ies = IndicesClient(es)


index_name = 'brenda-ontology'
actions = [dict(
    _index=index_name,
    _type=index_name,
    _source=dict(
        id=int(item.id.split(":")[1]),
        names=item.names()
    )
) for item in ontology.items()]

from elasticsearch.helpers import bulk

if ies.exists(index_name):
    ies.delete(index_name)
ies.create(index_name)
bulk(es, actions=actions)

