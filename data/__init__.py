import sys
sys.path.append('..')

import pandas as pd
from os.path import dirname, realpath, join
from lib.obo import read_ontology


script_dir = dirname(realpath(__file__))


def larisa_series():
    larisa_vd = pd.read_pickle(join(script_dir, 'larisa_set_uncleaned.pickle'))
    larisa_vd['series'] = larisa_vd['dataset_name'].str.split('_').str.get(0).str.split(' ').str.get(0)
    larisa_vd['id'] = larisa_vd['series'].map(lambda s: int(s[3:]))
    larisa_vd['doid'] = larisa_vd['doid'].map(lambda x: x.strip())
    return larisa_vd.set_index('id')


def tissue_ontology():
    return read_ontology(join(script_dir, 'geo-annotation', 'brenda-tissue-ontology.obo'))

def disease_ontology():
    return read_ontology(join(script_dir, 'geo-annotation', 'doid-patched.obo'))    