from importlib import reload
from os.path import exists

import networkx as nx
import numpy as np
import pandas as pd
import lib.obo
import lib.classification.elastic
import lib.classification.validation
import data

reload(lib.classification.validation)
reload(lib.classification.elastic)
reload(lib.obo)
reload(data)

from lib.classification.elastic import annotate_index, collapse_matches
from lib.utils import map_series
from lib.classification.validation import correct_ratio, incorrect_ratio
from elasticsearch import Elasticsearch
from lib.obo import read_ontology


pd.set_option('display.width', 512)

larisa_series = data.larisa_series()

larisa_ids = list(map(int, larisa_series.index.unique()))
larisa_vd = pd.DataFrame(dict(classes=larisa_series[['doid']]
                         .reset_index()
                         .groupby('id')['doid']
                         .apply(lambda x: list(set(x)))))


es = Elasticsearch()
ontology = read_ontology('data/geo-annotation/doid.obo',
                         exclude_duplicates=True)

# # Граф синонимов
# synonyms_graph = build_synonyms_graph(ontology, es, 'brenda-ontology')

annotation_result_file = 'data/geo-annotation/series.disease.res2.pickle'
if not exists(annotation_result_file):
    res = annotate_index(client=es,
                         ontology=ontology,
                         index='series',
                         ids=larisa_ids)

    res.to_pickle(annotation_result_file)

else:
    res = pd.read_pickle(annotation_result_file)

res['classes'] = res['classes'].map(collapse_matches(ontology.graph))

compare = pd.merge(res, larisa_vd, left_index=True, right_index=True)
metrics = pd.DataFrame(dict(
    correct_ratio=correct_ratio(res, larisa_vd),
    incorrect_ratio=incorrect_ratio(res, larisa_vd)
))

def doid_id(item_id):
    return "DOID:{:07}".format(item_id)


def ontology_name(item_id):
    if item_id not in ontology.meta:
        return item_id
    return ontology.meta[item_id].name


def to_name(series_id):
    return "GSE{}".format(series_id)


def names(df):
    return df.applymap(lambda xs: [ontology_name(x) for x in xs])

view = pd.DataFrame.from_records(list(res.items()), columns=('id', 'matches'))
view['name'] = view['id'].map(to_name)
view['matches_names'] = view['matches'].map(lambda matches: [ontology_name(m) for m in matches])
view['matches_count'] = view['matches'].map(len)
view.set_index('name', inplace=True)
view[view['matches_count'] > 1]


# Попытаемся построить графы из заматчивших тканей
ids = view.loc['GSE50081']['matches']

view['collapsed_matches'] = view['matches'].map(collapse_matches(ontology.graph))
view['collapsed_matches_count'] = view['collapsed_matches'].map(len)
view['collapsed_matches_names'] = view['collapsed_matches'].map(lambda matches: [ontology_name(m) for m in matches])
# view['collapsed_matches_syns'] = view['collapsed_matches'].map(collapse_matches(synonyms_graph))
# view['collapsed_matches_syns_count'] = view['collapsed_matches_syns'].map(len)
# nx.has_path(synonyms_graph, 'BTO:0000887', 'BTO:0001149')


view.shape[0], view[view.matches_count == 1].shape[0], view[view.collapsed_matches_count == 1].shape[0]
# (289, 107, 149, 166)
# Ок примерно до половины остается с одной тканью, пока все.
view_m1 = view[view.collapsed_matches_count == 1].copy()

vd = larisa_series[['doid', 'series']].copy()
vd = pd.DataFrame(vd.groupby('series').doid.apply(lambda x: list(set(x)))).reset_index()

check_m1 = pd.merge(view_m1, vd.set_index('series'), left_index=True, right_index=True)
check_m1.shape, check_m1[check_m1['collapsed_matches'] == check_m1['doid']].shape

# ((121, 8), (82, 8)) многовато ошибок

check_m1['doid_names'] = check_m1['doid'].map(lambda matches: [ontology_name(m.strip()) for m in matches])

check_m1[check_m1['collapsed_matches'] != check_m1['doid']][
    ['collapsed_matches', 'doid', 'collapsed_matches_names', 'doid_names']]
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
def path_length(graph, id1, id2):
    if id1 in graph.nodes() and \
                    id2 in graph.nodes() and \
            nx.has_path(graph, id1, id2):
        return len(nx.shortest_path(graph, id1, id2)) - 1 if id1 != id2 else 0
    else:
        return np.nan


check_m11 = check_m1[check_m1['doid'].map(lambda d: len(d) == 1)].copy()
check_m11['has_path_res_vd'] = map_series(lambda matches, doid: doid[0] in ontology.graph.nodes() and
                                                                ontology.has_path(matches[0], doid[0]),
                                          [check_m11['collapsed_matches'], check_m11['doid']])

check_m11['absolute_match'] = map_series(lambda matches, doid: matches[0] == doid[0],
                                         [check_m11['collapsed_matches'], check_m11['doid']])

check_m11['path_res_vd'] = map_series(lambda m, d: path_length(ontology.graph, m[0], d[0]),
                                      [check_m11['collapsed_matches'], check_m11['doid']])
check_m11[~check_m11['has_path_res_vd']]
check_m11.loc['GSE51725']
# matches                          [DOID:162]
# matches_names                      [cancer]
# matches_count                             1
# collapsed_matches                [DOID:162]
# collapsed_matches_count                   1
# collapsed_matches_names            [cancer]
# doid                           [DOID:10534]
# doid_names                 [stomach cancer]
# has_path_res_vd                        True

# Опять траблы с gastric == stomach
# Наверное надо модифицировать синонимы

# Плюс надо просерить насколько длинный путь от полученного до проверочного

check_m11.loc['GSE51105']
# matches                       [DOID:162, DOID:2394]
# matches_names              [cancer, ovarian cancer]
# matches_count                                     2
# collapsed_matches                       [DOID:2394]
# collapsed_matches_count                           1
# collapsed_matches_names            [ovarian cancer]
# doid                                   [DOID:10534]
# doid_names                         [stomach cancer]
# has_path_res_vd                                True


# check_m11[check_m11.path_res_vd == 3]
#              id     matches matches_names  matches_count collapsed_matches  collapsed_matches_count collapsed_matches_names          doid        doid_names has_path_res_vd absolute_match  path_res_vd
# GSE15459  15459  [DOID:162]      [cancer]              1        [DOID:162]                        1                [cancer]  [DOID:10534]  [stomach cancer]            True          False            3
# GSE19826  19826  [DOID:162]      [cancer]              1        [DOID:162]                        1                [cancer]  [DOID:10534]  [stomach cancer]            True          False            3
# GSE51725  51725  [DOID:162]      [cancer]              1        [DOID:162]                        1                [cancer]  [DOID:10534]  [stomach cancer]            True          False            3
# GSE57303  57303  [DOID:162]      [cancer]              1        [DOID:162]                        1                [cancer]  [DOID:10534]  [stomach cancer]            True          False            3

# Не нашел gastric


check_m11[check_m11.path_res_vd == 0].shape, check_m11.shape
# ((82, 12), (112, 12))
# Очень неплохие результаты - прямых попаданий 82 из 112

check_m11[check_m11.path_res_vd == 4]
#              id                        matches                             matches_names  matches_count collapsed_matches  collapsed_matches_count  collapsed_matches_names         doid          doid_names has_path_res_vd absolute_match  path_res_vd
# GSE21687  21687  [DOID:162, DOID:3093, DOID:4]  [cancer, nervous system cancer, disease]              3       [DOID:3093]                        1  [nervous system cancer]  [DOID:7497]  [brain ependymoma]            True          False            4

# !!! тупо нет в тексте brain ependymoma, есть просто ependymoma

# Идея как еще можно померить точность: размер входящих подболезней в онтологии
# Такая метрика даст приблизительную оценку насколько "обща" проставленная болезнь

# Теперь сделаем анализ всех попаданий
