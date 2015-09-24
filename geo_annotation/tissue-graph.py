# import sys
# sys.path.append('..')

import misc.obo
from importlib import reload
from collections import defaultdict
import requests as rq
import pandas as pd

reload(misc.obo)
from misc.obo import read_ontology, Record, Ontology

obo_file = 'data/age-biomarkers/brenda-tissue-ontology.obo'
ontology = read_ontology('data/age-biomarkers/brenda-tissue-ontology.obo')

# %%
# %%
# l1000 validation dataset
l1000 = pd.DataFrame(rq.get('http://amp.pharm.mssm.edu/L1000CDS2/diseases').json())
# %%
l1000['series'] = l1000['term'].str.split('_').str.get(1)
l1000['disease'] = l1000['term'].str.split('_').str.get(0)

# %%
# Larisa validation dataset

larisa_vd = pd.read_pickle('data/larisa_set_uncleaned.pickle')
larisa_vd['series'] = larisa_vd['dataset_name'].str.split('_').str.get(0).str.split(' ').str.get(0)
larisa_vd['id'] = larisa_vd['series'].map(lambda s: int(s[3:]))
larisa_vd_ids = [int(x) for x in larisa_vd['id'].unique()]
# %%
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch, Match, Q

es = Elasticsearch()


def iter_search(search):
    res = search[:1].execute()
    total = res.hits.total
    page_size = 1000
    for i in range(0, total, page_size):
        for item in search[i:i + page_size].execute():
            yield item


def query_for_term(term, fields):
    return MultiMatch(query=term, fields=fields, type='phrase', slop=3)


def query_for_terms(terms, fields):
    qs = [query_for_term(term, fields) for term in terms]
    return Q('bool', should=qs)


def search_term(es, term, index, fields=None, ids=None, id_field='id') -> [str]:
    fields = fields or ['_all']
    ids = ids or []

    s = Search(es, index)
    if ids:
        s = s.filter('terms', **{id_field: ids})

    if isinstance(term, list):
        s = s.query(query_for_terms(term, fields))
    else:
        s = s.query(query_for_term(term, fields))

    s = s.extra(fields=[id_field])
    return [item._d_[id_field][0] for item in iter_search(s)]


# %%
_r = search_term(es, 'cancer', 'series')
len(_r)
# %%

_r = search_term(es, 'cancer', 'series', ids=larisa_vd_ids)
len(_r)

# %%
# Пробуем найти ткани, которые проставлены ларисой
larisa_tissues = larisa_vd['tissue'].unique()
check1 = dict(
    (tissue, search_term(es, tissue, 'series', ids=larisa_vd_ids))
    for tissue in larisa_tissues
)
# %%
larisa_vd['q'] = [id in check1[tissue] for (tissue, id) in zip(larisa_vd.tissue, larisa_vd.id)]


# %%
def search_item(client: Elasticsearch, item: Record, index: str, ids: [str]=None, id_field: str='id'):
    names = [item.name] + item.synonyms
    return search_term(es=client,
                      term=names,
                      index=index,
                      ids=ids,
                      id_field=id_field)


def search_ontology(client: Elasticsearch, ontology: Ontology, index: str, ids: [str]=None, id_field: str='id'):
    res = defaultdict(list)
    for item in ontology.items():
        res_ids = search_item(client=client,
                              item=item,
                              index=index,
                              ids=ids,
                              id_field=id_field
                              )
        #        item_id = item.int_id()
        item_id = item.id
        for i in res_ids:
            res[i].append(item_id)
    return dict(res)


# %%
res = search_ontology(es, ontology, 'series', ids=larisa_vd_ids)

data = list((series_id, ','.join(ontology.meta[tissue_id].name for tissue_id in tissues_ids), tissues_ids)
           for series_id, tissues_ids in res.items())

data = pd.DataFrame.from_records(data, columns=['series_id', 'tissues', 'tissue_ids']).set_index('series_id')

ids = data.loc[19554].tissue_ids

def fmt_name(item_id):
    return "{} ({})".format(ontology.meta[item_id].name, item_id)

def name(id):
    return ontology.meta[id].name

mat = [(fmt_name(id1), fmt_name(id2), ontology.has_path(id1, id2)) for id1 in ids for id2 in ids]

mat = pd.DataFrame.from_records(data=mat, columns=['id1', 'id2', 'has_path'])
mat = mat.pivot(index='id1', columns='id2', values='has_path')
mat


def contains_name(id1, id2):
    return ontology.meta[id1].name in ontology.meta[id2].name

mat1 = [(name(id1), name(id2), contains_name(id1, id2)) for id1 in ids for id2 in ids]

mat1 = pd.DataFrame.from_records(data=mat1, columns=['id1', 'id2', 'has_path'])
mat1 = mat1.pivot(index='id1', columns='id2', values='has_path')
mat1

# %%
1
