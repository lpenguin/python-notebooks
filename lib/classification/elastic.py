from collections import defaultdict
from elasticsearch import Elasticsearch
from elasticsearch_dsl.query import MultiMatch, Match, Q
from elasticsearch_dsl import Search
import networkx as nx
import numpy as np
import pandas as pd
import pymonad
from lib.obo import Record, Ontology


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


def search_term(es, term, index, fields=None, ids=None, id_field='id', debug=False) -> [str]:
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
    if debug:
        print(s.to_dict())
    return [item._d_[id_field][0] for item in iter_search(s)]


def search_item(client: Elasticsearch, item: Record, index: str, ids: [str]=None, id_field: str='id', **kvargs):
    return search_term(es=client,
                       term=item.names(),
                       index=index,
                       ids=ids,
                       id_field=id_field, **kvargs)


def search_ontology(client: Elasticsearch, ontology: Ontology, index: str, ids: [str]=None, id_field: str='id', **kvargs):
    res = defaultdict(list)
    for item in ontology.items():
        res_ids = search_item(client=client,
                              item=item,
                              index=index,
                              ids=ids,
                              id_field=id_field,
                              **kvargs)
        #        item_id = item.int_id()
        item_id = item.id
        for i in res_ids:
            res[i].append(item_id)
    return dict(res)


def annotate_index(client: Elasticsearch, ontology: Ontology, index: str, ids: [str]=None, id_field: str='id')->pd.DataFrame:
    res = search_ontology(client=client,
                          ontology=ontology,
                          index=index,
                          ids=ids,
                          id_field=id_field)

    return pd.DataFrame.from_records(
        list(res.items()),
        columns=['item', 'classes'],
    ).set_index('item')


def build_synonyms_graph(ontology: Ontology, client: Elasticsearch, index: str)->nx.DiGraph:
    res = search_ontology(ontology=ontology,
                          client=client,
                          index=index)

    graph = nx.DiGraph()
    for dest_id, source_ids in res.items():
        for source_id in source_ids:
            if source_id != dest_id:
                graph.add_edge(source_id, dest_id)

    return graph


def analyze_digraph(graph: nx.DiGraph, ontology: Ontology):
    res = []
    mat = nx.to_numpy_matrix(graph)

    syns_check = np.nonzero(np.triu(np.multiply(
        mat,
        np.transpose(mat)
    )))

    nodes = graph.nodes()

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

        res.append(d)
    return res


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