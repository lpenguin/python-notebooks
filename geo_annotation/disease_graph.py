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
import pickle
from os.path import exists

reload(geo_annotation.search_utils)
reload(misc.obo)
pd.set_option('display.width', 512)

larisa_vd = pd.read_pickle('data/larisa_set_uncleaned.pickle')
larisa_vd['series'] = larisa_vd['dataset_name'].str.split('_').str.get(0).str.split(' ').str.get(0)
larisa_vd['id'] = larisa_vd['series'].map(lambda s: int(s[3:]))
larisa_vd_ids = [int(x) for x in larisa_vd['id'].unique()]

es = Elasticsearch()
# Берем только последователей BTO:0001489 (whole body)
ontology = read_ontology('data/geo-annotation/doid.obo',
                         exclude_duplicates=True,
                         skip_obsolete=False)

# # Граф синонимов
# synonyms_graph = build_synonyms_graph(ontology, es, 'brenda-ontology')

annotation_result_file = 'data/geo-annotation/series.disease.res1.pickle'
if not exists(annotation_result_file):
    res = search_ontology(client=es,
                          ontology=ontology,
                          index='series',
                          ids=larisa_vd_ids)

    len(res)

    import pickle
    with open(annotation_result_file, 'wb') as f:
        pickle.dump(res, f)

else:
    with open(annotation_result_file, 'rb') as f:
        res = pickle.load(f)

def doid_id(item_id):
    return "DOID:{:07}".format(item_id)

def ontology_name(item_id):
    return ontology.meta[item_id].name

def to_name(series_id):
    return "GSE{}".format(series_id)


view = pd.DataFrame.from_records(list(res.items()), columns=('id', 'matches'))
view['name'] = view['id'].map(to_name)
view['matches_names'] = view['matches'].map(lambda matches: [ontology_name(m) for m in matches])
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
            if id1 not in graph:
                print('{}  not in graph'.format(id1))
                continue

            if id2 not in graph:
                print('{}  not in graph'.format(id2))
                continue


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
view['collapsed_matches_names'] = view['collapsed_matches'].map(lambda matches: [ontology_name(m) for m in matches])
# view['collapsed_matches_syns'] = view['collapsed_matches'].map(collapse_matches(synonyms_graph))
# view['collapsed_matches_syns_count'] = view['collapsed_matches_syns'].map(len)
# nx.has_path(synonyms_graph, 'BTO:0000887', 'BTO:0001149')

[item for item in ontology.items() if any('CD3'.lower() in name for name in item.names())]

view.shape[0], view[view.matches_count == 1].shape[0], view[view.collapsed_matches_count==1].shape[0]
# (289, 107, 149, 166)
# Ок примерно до половины остается с одной тканью, пока все.
view_m1 = view[view.collapsed_matches_count == 1].copy()

vd = larisa_vd[['doid', 'series']].copy()
vd = pd.DataFrame(vd.groupby('series').doid.apply(lambda x: list(set(x)))).reset_index()

check_m1 = pd.merge(view_m1, vd.set_index('series'), left_index=True, right_index=True)
check_m1.shape, check_m1[check_m1['collapsed_matches'] == check_m1['doid']].shape

# ((82, 8), (51, 8)) многовато ошибок

check_m1['doid_names'] = check_m1['doid'].map(lambda matches: [ontology_name(m.strip()) for m in matches])

check_m1[check_m1['collapsed_matches'] != check_m1['doid']][['collapsed_matches', 'doid', 'collapsed_matches_names', 'doid_names']]
check_m1.loc['GSE42252']
# id                                               42252
# matches                          [DOID:1793, DOID:162]
# matches_names              [pancreatic cancer, cancer]
# matches_count                                        2
# collapsed_matches                          [DOID:1793]
# collapsed_matches_count                              1
# collapsed_matches_names            [pancreatic cancer]
# doid                                      [DOID:10534]
# doid_names                            [stomach cancer]

# Если открыть GEO то высветится еще gastric cancer, которого нет в DOID
# Скорее всего изза синонимии gaster и stomach,
# однако, в синонимах DOID это не проставлено
check_m11 = check_m1[check_m1['doid'].map(lambda d: len(d) == 1)].copy()
check_m11['has_path_res_vd'] = [doid[0] in ontology.graph.nodes() and ontology.has_path(matches[0], doid[0]) for matches, doid in zip(check_m11['matches'], check_m11['doid'])]
check_m11[~check_m11['has_path_res_vd']]
check_m11.loc['GSE16155']
# id                                           16155
# matches                                [DOID:1712]
# matches_names              [aortic valve stenosis]
# matches_count                                    1
# collapsed_matches                      [DOID:1712]
# collapsed_matches_count                          1
# collapsed_matches_names    [aortic valve stenosis]
# doid                                   [DOID:7497]
# doid_names                      [brain ependymoma]
# has_path_res_vd                              False

# ТАМ ВОБЩЕ НЕТ СЛОВ aortic valve stenosis

check_m11.loc['GSE34942']
# id                                            34942
# matches                        [DOID:299, DOID:162]
# matches_names              [adenocarcinoma, cancer]
# matches_count                                     2
# collapsed_matches                        [DOID:299]
# collapsed_matches_count                           1
# collapsed_matches_names            [adenocarcinoma]
# doid                                    [DOID:3717]
# doid_names                 [gastric adenocarcinoma]
# has_path_res_vd                               False

# ??? нет пути из adenocarcinoma в gastric adenocarcinoma
# ?? Почему вообще не нашлось gastric adenocarcinoma

from geo_annotation.search_utils import search_term, search_item
search_item(es, ontology.meta['DOID:3717'], 'series', ids=[34942])
search_item(es, ontology.meta['DOID:3717'], 'series', ids=[34942])
search_term(es, ['gastric adenocarcinomas'], 'series', ids=[34942])
# Какаято гадость, adenocarcinomas ищет, а adenocarcinoma нет