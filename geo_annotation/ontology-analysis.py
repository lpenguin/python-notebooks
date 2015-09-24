# Анализ связности онтологий

# Вхождение одного элемента в другой проверяем по двум параметрам:
# * Есть ли путь из одного в другой
# * Содержится ли имя одного в имени другого
# * Более расширено: содержится один из синонимов одного
#                    в одном из синонимов другого
from importlib import reload
import misc.obo
reload(misc.obo)
from misc.obo import read_ontology
import networkx as nx

ontology = read_ontology('data/age-biomarkers/brenda-tissue-ontology.obo')


path_graph = nx.DiGraph()

for node1 in ontology.graph.nodes_iter():
    for node2 in ontology.graph.nodes_iter():
        if nx.has_path(ontology.graph, node1, node2):
            path_graph.add_edge(node1, node2)


import json
with open('data/geo-annotation/tissue-path-adj.json', 'w') as f:
    json.dump(nx.to_dict_of_lists(path_graph), f)

path_mat = nx.to_numpy_matrix(path_graph)
path_mat

for i in range(path_mat.shape[0]):
    for j in range(path_mat.shape[0]):
        if i == j:
            continue
        x = path_mat[i, j]
        y = path_mat[j, i]

        if x == 1 and y == 1:
            print('bad path: ', i, j)

# нету путей туда обратно, ну и ок

import numpy as np


def contains_syns(ontology, id1, id2):
    item1 = ontology.meta[id1]
    item2 = ontology.meta[id2]
    return any(n1 in n2 for n1 in item1.names() for n2 in item2.names())


syns_graph = nx.DiGraph()

for node1 in ontology.graph.nodes_iter():
    for node2 in ontology.graph.nodes_iter():
        if node1 != node2 and contains_syns(ontology, node1, node2):
            syns_graph.add_edge(node1, node2)


print(nx.info(syns_graph))

with open('data/geo-annotation/tissue-syns-adj.json', 'w') as f:
    json.dump(nx.to_dict_of_lists(syns_graph), f)

for node1 in ontology.graph.nodes_iter():
    syns_graph.remove_edge(node1, node1)

syns_graph_ud = nx.Graph(syns_graph)
nx.number_connected_components(syns_graph_ud)
nx.number_weakly_connected_components(syns_graph)

list(nx.weakly_connected_components(syns_graph))[:10]

syns_mat = nx.to_numpy_matrix(syns_graph)

n = syns_mat.shape[0]
t = np.multiply(syns_mat,
                np.transpose(syns_mat))

syns_check = np.nonzero(np.triu(t))

nodes = ontology.graph.nodes()
syns_rev_nodes = [(ontology.meta[nodes[i]],
  ontology.meta[nodes[j]])
    for (i, j) in zip(*syns_check)]
syns_rev_nodes

[contains_syns(ontology, nodes[i],
  nodes[j])
    for (i, j) in zip(*syns_check)]

[syns_mat[i, j] == syns_mat[j, i] for (i, j) in zip(*syns_check)]



# Поиск синонимов в самих тканях
# Построим таблицу частоты встречаимости синонимов

names = [name for item in ontology.items() for name in item.names()]
import pandas as pd
names = pd.Series(names)
names_counts = names.value_counts()
names_counts[names_counts > 1].sum(), names_counts.shape

# Выберем синонимы дубликаты
duplicates = set(names_counts[names_counts > 1].index)

# Идея: убирать из синонимов `duplicates`, оставить их в имени,
# Т.к. имя важнее

# Удаляем дубликаты из синонимов
for item in ontology.items():
    item.synonyms = [s for s in item.synonyms if s not in duplicates]

from geo_annotation import search_utils
from elasticsearch import Elasticsearch
es = Elasticsearch()

res = search_utils.search_ontology(client=es,
                                   index='brenda-ontology',
                                   ontology=ontology)

def ontology_id(item_id: int, ontology_name: str='BTO'):
    return "{ontology_name}:{id:07}".format(ontology_name=ontology_name,
                                           id=item_id)


res = dict((ontology_id(name, 'BTO'), value) for name, value in res.items())

syns_graph = nx.DiGraph()

for item_id, matched_ids in res.items():
    for matched_id in matched_ids:
        if item_id != matched_id:
            syns_graph.add_edge(item_id, matched_id)

import numpy as np
syns_mat = nx.to_numpy_matrix(syns_graph)
n = syns_mat.shape[0]

syns_check = np.nonzero(np.triu(np.multiply(
    syns_mat,
    np.transpose(syns_mat)
)))

nodes = syns_graph.nodes()


[(ontology.meta[nodes[i]].id, ontology.meta[nodes[i]].names(),
  ontology.meta[nodes[j]].id, ontology.meta[nodes[j]].names())
    for (i, j) in zip(*syns_check)]

for (i, j) in zip(*syns_check):
    names_i = ontology.meta[nodes[i]].names()
    names_j = ontology.meta[nodes[j]].names()

    l = max(len(names_i), len(names_j))

    names_i += [np.nan] * (l - len(names_i))
    names_j += [np.nan] * (l - len(names_j))
    d = pd.DataFrame({
        ontology.meta[nodes[i]].id: names_i,
        ontology.meta[nodes[j]].id: names_j
    })

    print(d)
    print()

# И тут оказывается что синонимы то некоторые совпадают!!
# например
"""
(['peripheral primitive neuroectodermal tumor cell',
   'peripheral PNET cell',
   'PPNET cell',
   'PPNET-peripheral neuroepithelioma cell'],
  ['primitive neuroectodermal tumor cell',
   'peripheral neuroepithelioma cell',
   'PNET cell']),

    (['alveolar cell type II',
   'alveolar cell type 2',
   'alveolar T2 cell',
   'alveolar type 2 cell ',
   'alveolar type II cell',
   'granular pneumonocyte',
   'great alveolar cell',
   'large alveolar cell',
   'T2 cell',
   'type 2 pneumocyte'],
  ['T2 cell', '174xCEM.T2 cell']),
"""

# Тоесть есть синонимы встречаюющиеся во многих такнях!
"""
'T2 cell', 'PNET cell'
и тп
"""

# Исправил ошибки выше, убиранием дубликатов из синонимов (но не имен)

# Еще несколько типов ошибок
# Не учитываются знаки +/-, ну и вобще все спец символы.

"""
                    BTO:0005245                   BTO:0005246
0  culture condition:CD31+ cell  culture condition:CD31- cell

                   BTO:0004410                  BTO:0004411
0  culture condition:CD8+ cell  culture condition:CD8- cell
"""

# Осталось в синонимах, хотя болжно было удалиться,
# ошибка изз того что синонимы не приводятся к нижнему регистру
"""
        BTO:0003355 BTO:0003356
0  BEAS-2B/BBM cell    BBm cell
1          BBM cell         NaN

                              BTO:0002363                  BTO:0004625
0          pancreatic ductal carcinoma cell  plasmacytoid dendritic cell
1  duct cell carcinoma cell of the pancreas    interferon-producing cell
2  duct-cell carcinoma cell of the pancreas                     IPC cell
3          ductal carcinoma of the pancreas                     pDC cell
4         pancreas duct-cell carcinoma cell                          NaN
5       pancreatic duct cell carcinoma cell                          NaN
6                                  PDC cell                          NaN
"""

# Более сложный случай,
# изза того, что в ElasticSearch проставлен параметр span на перестановку слов,
# один элемент онтологии содержащий один длинный (nasal cavity olfactory epithelium)
# и один короткий синоним (nasal epithelium)
# совпадает с другим у которого срежний синоним (nasal cavity epithelium)
# Получается перекрестное вхождение

"""
                         BTO:0000108              BTO:0000912
0               olfactory epithelium             nasal mucosa
1  nasal cavity olfactory epithelium  nasal cavity epithelium
2                   nasal epithelium                      NaN
3                   olfactory mucosa                      NaN
4       olfactory sensory epithelium                      NaN

             BTO:0000944     BTO:0005065
0           NIH-3T3 cell  Swiss-3T3 cell
1               3T3 cell  Swiss 3T3 cell
2         3T3 fibroblast  Swiss/3T3 cell
3  3T3-Swiss albino cell   Swiss3T3 cell
4           NIH 3T3 cell             NaN
5           NIH/3T3 cell             NaN
6            NIH3T3 cell             NaN

                            BTO:0000037            BTO:0000680
0             renal cell carcinoma cell     kidney cancer cell
1         adenocarcinoma cell of kidney  kidney carcinoma cell
2                            CCRCC cell      kidney tumor cell
3  clear cell renal cell carcinoma cell      renal cancer cell
4                  Grawitz`s tumor cell   renal carcinoma cell
5          hypernephroid carcinoma cell       renal tumor cell
6                    hypernephroma cell                    NaN
7            kidney adenocarcinoma cell                    NaN
8             renal adenocarcinoma cell                    NaN
"""

# Хаха просто поменяны местами слова

"""
    BTO:0000555 BTO:0001804
0   hair root   root hair
"""

# Просто совпадают, хи
"""
                                BTO:0002230                               BTO:0003832
0  culture condition:naphthalene-grown cell  culture-condition:naphthalene-grown cell
"""

# Гм, а вот случай, когда непонятно,
# почему эластик нашел перекрестное вхождение

"""
              BTO:0000375 BTO:0000382
0  keratinocyte cell line     Kc cell
1                      KC         NaN

                            BTO:0004258                                      BTO:0004261
0  primitive neuroectodermal tumor cell  peripheral primitive neuroectodermal tumor cell
1      peripheral neuroepithelioma cell                             peripheral PNET cell
2                             PNET cell                                       PPNET cell
3                                   NaN           PPNET-peripheral neuroepithelioma cell
"""
