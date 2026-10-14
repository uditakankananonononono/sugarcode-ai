"""Row 593: Federated Learning - Trains without centralizing.

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


def aggregate_updates(rows):
    """Rows: (client_id, sample_count, parameter_delta_1, parameter_delta_2).
    Exact sample-weighted FedAvg aggregation over supplied two-coordinate
    updates. Raw examples are not inputs, but this function does not train
    clients or provide transport, secure aggregation, DP or privacy guarantees.
    All client updates are visible here; external distributed workflow omitted.
    """
    _rows(rows, 4)
    for client, samples, first, second in rows:
        _label(client)
        _integer(samples, 1, 1000000)
        _integer(first, -1000000, 1000000)
        _integer(second, -1000000, 1000000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate client')
    from fractions import Fraction as F
    total=sum(x[1] for x in rows)
    first=sum(samples*delta for _,samples,delta,_ in rows)
    second=sum(samples*delta for _,samples,_,delta in rows)
    return {'update_fraction':[str(F(first,total)),str(F(second,total))],
            'sample_count':total,'clients':len(rows)}
