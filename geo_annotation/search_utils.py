from collections import defaultdict
from elasticsearch import Elasticsearch
from elasticsearch_dsl.query import MultiMatch, Match, Q
from elasticsearch_dsl import Search
from misc.obo import Record, Ontology


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