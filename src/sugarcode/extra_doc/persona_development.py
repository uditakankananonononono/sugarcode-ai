"""Row 367 Persona Development - Creates representative users: modal attribute summary.

Records are dicts of attribute to value that the caller already holds. For each
chosen attribute the persona takes the most common value (first appearance wins
ties) with its count and exact share of all records. 1 to 40 records, 1 to 4
attributes, names and values are strings of 1 to 40 characters with no control, format, private-use, surrogate or unassigned characters. Caps are
implementation choices.
NOT_CLAIMED: that records are accurate or representative, that a real user
matches the persona, demand, behavior, research validity or deployment.
"""
import unicodedata
from fractions import Fraction


def _s(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be str')
    if not 1 <= len(v) <= 40 or any(unicodedata.category(c)[0] == 'C' for c in v):
        raise ValueError(what + ' must be 1 to 40 characters without control or unassigned characters')
    return v


def build_persona(records, attributes):
    if type(records) not in (list, tuple) or type(attributes) not in (list, tuple):
        raise TypeError('records and attributes must be lists or tuples')
    if not 1 <= len(records) <= 40:
        raise ValueError('record count must be between 1 and 40')
    if not 1 <= len(attributes) <= 4:
        raise ValueError('attribute count must be between 1 and 4')
    names = [_s(a, 'attribute names') for a in attributes]
    if len(set(names)) != len(names):
        raise ValueError('attribute names must be unique')
    for r in records:
        if type(r) is not dict:
            raise TypeError('each record must be a dict')
        for a in names:
            if a not in r:
                raise ValueError('record is missing attribute ' + a)
            _s(r[a], 'attribute values')
    n = len(records)
    persona = {}
    for a in names:
        tally = {}
        for r in records:
            tally[r[a]] = tally.get(r[a], 0) + 1
        top = max(tally.values())
        value = next(v for v in tally if tally[v] == top)
        persona[a] = {'value': value, 'count': top, 'share': Fraction(top, n)}
    return {'persona': persona, 'record_count': n, 'representative_validated': False}
