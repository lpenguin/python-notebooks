from itertools import islice
import itertools

import pandas as pd


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


def align_length_dict(d: dict) -> dict:
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


def map_series(mapf, series):
    index = series[0].index
    data = list(map(lambda xs: mapf(*xs), zip(*series)))
    return pd.Series(data=data, index=index)


def expand(df_or_s, column_name=None):
    if isinstance(df_or_s, pd.DataFrame):
        if column_name is None:
            raise ValueError('column must not be None for DataFrame')
        return expand_dataframe(df_or_s, column_name)
    elif isinstance(df_or_s, pd.Series):
        return expand_series(df_or_s)
    else:
        raise ValueError('Unknown expanded type')


def expand_series(s):
    expanded = (
        s
            .apply(lambda x: pd.Series(x))
            .unstack()
            .reset_index(level=0, drop=True)
    )
    expanded.name = s.name
    return expanded


def expand_dataframe(df, column_name):
    expanded = (
        df[column_name]
            .apply(lambda x: pd.Series(x))
            .unstack()
            .reset_index(level=0, drop=True)
    )
    res = df.join(pd.DataFrame(expanded))
    del res[column_name]
    return res.rename(columns={0: column_name})


def flatten(iters):
    return itertools.chain.from_iterable(iters)