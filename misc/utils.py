from itertools import islice
import networkx as nx
import pandas as pd
import pymonad


def iter_window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def align_length(items):
    max_len = max(len(item) for item in items if isinstance(item, list))

    return [
        item + [np.nan] * (max_len - len(item)) if isinstance(item, list) else item
    for item in items]


def align_length_dict(d: dict)->dict:
    keys, values = list(zip(*d.items()))
    return dict(
        zip(keys, align_length(values))
    )


def iter_bucket(iterable):
    page_size = 3000
    bucket = []
    for item in iterable:
        bucket.append(item)
        if len(bucket) > page_size:
            yield bucket
            bucket = []
    yield bucket


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


def zip_map_series(mapf, series):
    index = series[0].index
    data = list(map(lambda xs: mapf(*xs), zip(*series)))
    return pd.Series(data=data, index=index)