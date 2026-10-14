"""Row 546: Model Monitoring - Detects drift.

SCOPED planning aid over caller supplied rows. No external actions, persistence,
capability development evidence, organization quality, or optimal policy claim.
Explicit import only; 1..32 tuple rows. Labels are lowercase ASCII identifiers.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _integer(value, low, high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low <= value <= high:
        raise ValueError('integer outside declared range')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')


def monitor_drift(rows):
    """Rows: (metric_name, reference_mean, current_mean, threshold).
    Flag absolute supplied-mean differences strictly above caller thresholds.
    Not statistical significance, distribution drift, model health or a live
    monitoring service. No schedules, data collection or alerts are sent.
    """
    _rows(rows, 4)
    for metric, reference, current, threshold in rows:
        _label(metric)
        _integer(reference, -1000000, 1000000)
        _integer(current, -1000000, 1000000)
        _integer(threshold, 0, 1000000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate metric')
    drift = [(metric,current-reference,abs(current-reference),abs(current-reference)>threshold)
             for metric,reference,current,threshold in sorted(rows)]
    return {'metrics': drift, 'flagged': [x[0] for x in drift if x[3]]}
