from importlib import reload
import networkx as nx
import numpy as np
import pandas as pd
from misc.obo import read_ontology
import misc.obo
import geo_annotation.search_utils
from geo_annotation.search_utils import search_ontology, build_synonyms_graph
from elasticsearch import Elasticsearch
from misc.utils import align_length_dict
import pymonad

reload(geo_annotation.search_utils)
reload(misc.obo)
pd.set_option('display.width', 512)

larisa_vd = pd.read_pickle('data/larisa_set_uncleaned.pickle')
larisa_vd['series'] = larisa_vd['dataset_name'].str.split('_').str.get(0).str.split(' ').str.get(0)
larisa_vd['id'] = larisa_vd['series'].map(lambda s: int(s[3:]))
larisa_vd_ids = [int(x) for x in larisa_vd['id'].unique()]

es = Elasticsearch()
# Берем только последователей BTO:0001489 (whole body)
ontology = read_ontology('data/age-biomarkers/brenda-tissue-ontology.obo',
                         exclude_duplicates=True,
                         subgraph='BTO:0001489')

# Граф синонимов
synonyms_graph = build_synonyms_graph(ontology, es, 'brenda-ontology')

res = search_ontology(client=es,
                      ontology=ontology,
                      index='series',
                      ids=larisa_vd_ids)

len(res)

import pickle
with open('data/geo-annotation/series.tissue.res1.pickle', 'wb') as f:
    pickle.dump(res, f)

res

def brenda_id(item_id):
    return "BTO:{:07}".format(item_id)

def brenda_name(item_id):
    return ontology.meta[item_id].name

def to_name(series_id):
    return "GSE{}".format(series_id)


view = pd.DataFrame.from_records(list(res.items()), columns=('id', 'matches'))
view['name'] = view['id'].map(to_name)
view['matches_names'] = view['matches'].map(lambda matches: [brenda_name(m) for m in matches])
view['matches_count'] = view['matches'].map(len)
view.set_index('name', inplace=True)
view[view['matches_count'] > 1]


# Попытаемся построить графы из заматчивших тканей
ids = view.loc['GSE50081']['matches']



@pymonad.curry
def collapse_matches(graph: nx.DiGraph, matches):
    g = nx.DiGraph()
    g.add_nodes_from(matches)
    for id1 in matches:
        for id2 in matches:
            if id1 != id2 and nx.has_path(graph, id1, id2):
                g.add_edge(id1, id2)


    leafs = []
    for subg in nx.weakly_connected_component_subgraphs(g):
        for node in subg.nodes_iter():
            if not subg.successors(node):
                leafs.append(node)

    return leafs


view['collapsed_matches'] = view['matches'].map(collapse_matches(ontology.graph))
view['collapsed_matches_count'] = view['collapsed_matches'].map(len)
view['collapsed_matches_names'] = view['collapsed_matches'].map(lambda matches: [brenda_name(m) for m in matches])
view['collapsed_matches_syns'] = view['collapsed_matches'].map(collapse_matches(synonyms_graph))

pd.DataFrame(align_length_dict(view.loc['GSE16395']))
pd.DataFrame(align_length_dict(view.loc['GSE30806']))
#   collapsed_matches  collapsed_matches_count collapsed_matches_names     id      matches  matches_count matches_names
# 0       BTO:0000140                        3                    bone  30806  BTO:0001149              3    quadriceps
# 1       BTO:0000887                        3                  muscle  30806  BTO:0000140              3          bone
# 2       BTO:0001149                        3              quadriceps  30806  BTO:0000887              3        muscle
# muscle это не quadriceps по онтологии, но
# muscle входит в синонимы quadriceps

nx.has_path(synonyms_graph, 'BTO:0000887', 'BTO:0001149')

[item for item in ontology.items() if any('CD3'.lower() in name for name in item.names())]

