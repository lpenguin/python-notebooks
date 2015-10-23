from collections import defaultdict
import pymongo
from lib.utils import iter_bucket

__author__ = 'nikita'


class ApiException(Exception):
    pass


class Api:
    def __init__(self, db_name, host=None, port=None):
        self.db_name = db_name
        self.port = port
        self.host = host
        self.db = pymongo.MongoClient(host=host, port=port)[db_name]

    def write_annotation(self, annotation_iter, ):
        for bucket in iter_bucket(annotation_iter):
            bulk = self.db.samples.initialize_unordered_bulk_op()
            for accession, item in bucket:
                annotation = {}
                for key, value in item.items():
                    annotation['annotation.{}'.format(key)] = value
                (
                    bulk
                        .find({'accession': accession})
                        .update_one({'$set': annotation})
                )
            bulk.execute()

    @staticmethod
    def conds_to_mongo(conditions):
        def cond_to_mongo(cond_key, cond_value):
            if isinstance(cond_value, list):
                return cond_key, {'$in': cond_value}
            else:
                return cond_key, cond_value

        conds = []

        for cond_key, cond_value in conditions.items():
            if cond_key == 'tissue_id':
                conds.append(cond_to_mongo(cond_key, cond_value))
            elif cond_key == 'disease_id':
                conds.append(cond_to_mongo(cond_key, cond_value))
            elif cond_key == 'norm':
                conds.append(cond_to_mongo(cond_key, int(cond_value)))
            elif cond_key == 'preprocessed':
                conds.append(cond_to_mongo(cond_key, int(cond_value)))
            elif cond_key == 'age.gt':
                conds.append(('age', {'$gt': cond_value}))
            elif cond_key == 'age.lt':
                conds.append(('age', {'$lt': cond_value}))
            elif cond_key == 'age.exists':
                conds.append(('age', {'$ne': None}))
            elif cond_key == 'tissue_id.exists':
                conds.append(('tissue_id', {'$ne': None}))
            elif cond_key == 'disease_id.exists':
                conds.append(('disease_id', {'$ne': None}))
            else:
                raise ApiException('Invalid condition: {} = {}. Unknown key {}'.format(
                    cond_key, cond_value, cond_key)
                )

        return dict(conds)

    def search_samples(self, **conditions):
        return self.db.samples.find(Api.conds_to_mongo(conditions), {
            '_id': 0,
        })

    def samples_count(self, **conditions):
        return self.db.samples.count(Api.conds_to_mongo(conditions))

    def search_series(self, **conditions):
        samples = self.search_samples(**conditions)

        series_samples = defaultdict(list)
        for s in samples:
            for series in s['series']:
                series_samples[series].append(s)

        def create_series(series):
            accession = series['accession']
            series['samples'] = series_samples[accession]
            return series

        return map(create_series, self.db.series.find({
            'accession': {'$in': list(series_samples.keys())}
        }, {
            '_id': 0
        }))
