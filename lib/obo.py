from collections import defaultdict
import networkx as nx
import re
import pandas as pd
import numpy as np

def to_dict(ontology: 'Ontology'):
    def item_to_dict(item: 'Record')->dict:
        item_dict = item.dict()
        item_dict['parents'] = item.get_parents()
        return item_dict
        
    return [to_dict(item) for item in ontology.items()]
    
def read_obo_as_graph(file_name):
    _, items = read_obo(file_name)
    items = [Record(item) for item in items if 'is_obsolete' not in item]
    graph = nx.DiGraph()

    graph.add_nodes_from(item.id for item in items)
    for item in items:
        for parent in item.get_parents():
            graph.add_edge(parent, item.id)

    print('Read obo graph')
    print(nx.info(graph))
    return graph, items


def read_ontology(file_name: str, exclude_duplicates: bool=False, subgraph=None)->'Ontology':
    """
    :param file_name: read from file
    :param exclude_duplicates: exclude duplicate records from synonyms
    :param subgraph: take subgraph maked of descendants of "subgraph" node
    :param skip_obsolete: skip records with "is_obsolete == True"
    :return:
    """
    graph, records = read_obo_as_graph(file_name)
    if subgraph:
        descendants = set(nx.descendants(graph, subgraph))
        descendants.add(subgraph)
        graph = nx.subgraph(graph, descendants)
        records = [r for r in records if r.id in descendants]

    return Ontology(graph=graph, records=records, exclude_duplicates=exclude_duplicates)


def read_obo(file_name, kind='dict'):
    assert kind in ['dict', 'class']

    with open(file_name) as fd:
        fd_iter = _iter_lines(fd)
        header = _read_term(fd_iter)
        items = []
        typedefs = []
        for item_type in fd_iter:
            item = _read_term(fd_iter)
            if item_type == '[Term]':
                items.append(item)
            elif item_type == '[Typedef]':
                    typedefs.append(item)

    return (header, items)


def _read_single_or_none(d, field):
    if field not in d:
        return None
    else:
        return d[field][0]


def parse_is_a(is_a):
    if is_a is None:
        return None

    parent_id, *tokens = is_a.split(' ! ')
    return parent_id


def parse_relationship(relationship):
    #    part_of BTO:0000282 ! head -> part_of, BTO:0000282
    kind, id = parse_is_a(relationship).split(' ')
    return id, kind


def extract_str(phrase):
    # extract foo from "foo" bar baz
    if not phrase:
        return phrase

    res = re.match(r'[^\"]*\"([^\"]+)\".*', phrase)
    if not res:
        return phrase
    return res.group(1)


class Record:
    def __init__(self, dict_item):
        self._read_dict(dict_item)

    def _read_dict(self, d):
        self.id = _read_single_or_none(d, 'id')
        self.name = _read_single_or_none(d, 'name').lower()
        self.is_a = parse_is_a(_read_single_or_none(d, 'is_a'))
        self.is_obsolete = _read_single_or_none(d, 'is_obsolete')
        self.relationships = [parse_relationship(rel) for rel in d.get('relationship', [])]

        self.xrefs = d.get('xref', [])
        self.subsets = d.get('subset', [])
        self.synonyms = [extract_str(syn).lower() for syn in d.get('synonym', [])]
        self.defs = [extract_str(def_) for def_ in d.get('def', [])]
        self.alt_ids = d.get('alt_id', [])

    def get_parents(self):
        rel_ids = [id for (id, kind) in self.relationships]
        if self.is_a:
            rel_ids.append(self.is_a)
        return rel_ids

    def dict(self):
        return self.__dict__

    def __str__(self):
        return str(self.dict())

    def __repr__(self):
        return self.__str__()

    def int_id(self):
        _, str_id = self.id.split(":")
        return int(str_id)

    def names(self):
        return [self.name] + self.synonyms


class Ontology:
    def __init__(self, graph: nx.DiGraph, records: [Record], exclude_duplicates: bool=False):
        assert isinstance(records, list)
        assert isinstance(graph, nx.DiGraph)

        if exclude_duplicates:
            names = pd.Series([name for item in records for name in item.names()])
            names_counts = names.value_counts()

            # Выберем синонимы дубликаты
            duplicates = set(names_counts[names_counts > 1].index)

            for item in records:
                item.synonyms = [s for s in item.synonyms if s not in duplicates]

        self.graph = graph
        self.meta = dict(
            (item.id, item) for item in records
        )

    def to_parent_f(self, node_ids):
        if isinstance(node_ids, str):
            node_ids = [node_ids]

        mapping = dict((node_id, parent_id)
                         for node_id, _ in self.meta.items()
                         for parent_id in node_ids 
                         if parent_id in self.graph and self.has_path(parent_id, node_id)
        )

        return lambda t: mapping.get(t, np.nan) if pd.notnull(t) else t


    def descendants(self, node_id, level=1):
        def descendants_level(graph, node, level):
            if level == 0:
                return [node]
            else:
                successors = graph.successors(node)
                res = []
                for succ in successors:
                    res += descendants_level(graph, succ, level - 1)
                return res
        return list(set(descendants_level(self.graph, node_id, level)))

    def name(self, node_id):
        return self.meta[node_id].name if node_id in self.meta else np.nan

    def has_path(self, id1, id2):
        return nx.has_path(self.graph, id1, id2)

    def items(self)->[Record]:
        return self.meta.values()


def _iter_terms(fd_iter):
    while True:
        yield _read_term(fd_iter)


def _iter_lines(fd):
    # i = 0
    for line in fd:
        # print(i)
        # i += 1
        yield line.rstrip('\n')


def _read_term(fd_iter):
    res = defaultdict(list)
    for line in fd_iter:
        if not line:
            return res
        # print(line)
        key, value = line.split(": ", 1)
        res[key].append(value.strip())
