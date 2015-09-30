import pandas as pd
from os.path import dirname, realpath, join

script_dir = dirname(realpath(__file__))


def larisa_series():
    larisa_vd = pd.read_pickle(join(script_dir, 'larisa_set_uncleaned.pickle'))
    larisa_vd['series'] = larisa_vd['dataset_name'].str.split('_').str.get(0).str.split(' ').str.get(0)
    larisa_vd['id'] = larisa_vd['series'].map(lambda s: int(s[3:]))
    return larisa_vd.set_index('id')
