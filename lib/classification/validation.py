import pandas as pd
from lib import utils

__all__ = [
    'correct_ratio',
    'incorrect_ratio'
]


def _create_check(result: pd.DataFrame, validation: pd.DataFrame):
    check = pd.merge(result, validation,
                     left_index=True,
                     right_index=True,
                     suffixes=('_result', '_validation'))
    return check


def calc_metrics(result: pd.DataFrame, validation: pd.DataFrame,
                 metrics: callable,
                 result_col: str = 'classes', validation_col='classes'):
    if isinstance(result, pd.DataFrame) and isinstance(validation, pd.DataFrame):
        check = _create_check(result, validation)

        if result_col == validation_col:
            result_col += '_result'
            validation_col += '_validation'
        series = [check[result_col], check[validation_col]]
    elif isinstance(result, pd.Series) and isinstance(validation, pd.Series):
        series = [result, validation]
    return utils.map_series(metrics, series)


def correct_ratio(result: pd.DataFrame, validation: pd.DataFrame,
                  result_col: str = 'classes', validation_col='classes',
                  compare_func=None):
    compare_func = compare_func or (lambda x, y: x == y)

    def metrics(result_classes: [], validation_classes: []):
        correct_count = len(set(vc
                                for rc in result_classes
                                for vc in validation_classes
                                if compare_func(rc, vc)))

        return correct_count / len(validation_classes)

    return calc_metrics(result, validation,
                        metrics=metrics,
                        result_col=result_col,
                        validation_col=validation_col)


def incorrect_ratio(result: pd.DataFrame, validation: pd.DataFrame,
                    result_col: str = 'classes', validation_col='classes',
                    compare_func=None):
    compare_func = compare_func or (lambda x, y: x == y)

    def metrics(result_classes: [], validation_classes: []):
        if not result_classes:
            return 0
        incorrect_count = len(set(rc
                                  for rc in result_classes
                                  for vc in validation_classes
                                  if not compare_func(rc, vc)))

        return incorrect_count / len(result_classes)

    return calc_metrics(result, validation,
                        metrics=metrics,
                        result_col=result_col,
                        validation_col=validation_col)


def perfect_match(result: pd.DataFrame, validation: pd.DataFrame,
                  result_col: str = 'classes', validation_col='classes',
                  compare_func=None):
    compare_func = compare_func or (lambda x, y: x == y)

    def metrics(result_classes: [], validation_classes: []):
        res = set((rc, vc)
                  for vc in validation_classes
                  for rc in result_classes
                  if compare_func(rc, vc))
        # res = set(rc for rc in result_classes
        #           if any(compare_func(rc, vc) for vc in validation_classes))
        return len(res) == len(validation_classes)

    return calc_metrics(result, validation,
                        metrics=metrics,
                        result_col=result_col,
                        validation_col=validation_col)
