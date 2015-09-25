from itertools import islice


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