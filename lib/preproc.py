
from collections import Iterable
import pandas as pd

def list_set(xs):
    return list(set(xs))


def tasks_for_series(db, series_accession, type_='preproc'):
    if not isinstance(series_accession, str) and \
        isinstance(series_accession, Iterable):
        return [task 
                for acc in series_accession 
                for task in tasks_for_series(db, acc, type_)]
        
    samples = pd.DataFrame(list(db.samples.find({'series': series_accession},
                    {'_id': 0,
                     'platform': 1,
                     'accession': 1} 
                   )))
    if samples.shape[0] == 0:
        return []
    
    _t = (
        samples
        .groupby('platform')
        .agg({'accession': list_set})
    )
    
    return [dict(name='{}_{}'.format(series_accession, platform),
          type=type_,
          meta=dict(
                accession=series_accession,
                platform=platform,
                samples=samples
            ))
        for platform, (samples, ) in _t.iterrows()]
        
    