import lib.obo
from lib.obo import read_ontology
import elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk


def import_ontology(ontology: lib.obo.Ontology, index_name: str):
    es = elasticsearch.Elasticsearch()

    ies = IndicesClient(es)

    actions = [dict(
        _index=index_name,
        _type=index_name,
        _source=dict(
            id=item.id,
            names=item.names()
        )
    ) for item in ontology.items()]

    if ies.exists(index_name):
        ies.delete(index_name)
    ies.create(index_name)
    return bulk(es, actions=actions)


# def cell():
#     ontology = read_ontology('data/age-biomarkers/brenda-tissue-ontology.obo', exclude_duplicates=True)



# ontology = read_ontology('data/geo-annotation/doid.obo',
#                          exclude_duplicates=True)
#
# import_ontology(ontology, 'disease_ontology')

