"""Row 1043 Conditional Random Fields - Structured prediction.

Exact inference for a positive integer potential linear-chain CRF. Labels are
ordered, ASCII lowercase identifiers (1..8 letters); there are 2..4 labels and
1..6 sites. All unary and shared transition potentials are integers 1..9.
Returns the exact partition, MAP labeling (ties by supplied label order), MAP
probability, and normalized per-site marginals as numerator/denominator pairs.
Caps precede element scans. Inputs and output containers are not shared.
NOT_CLAIMED: parameter training, feature extraction, general graph inference,
production readiness. No fitted model or scientific validation is claimed.
"""
from fractions import Fraction

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
SCOPE = 'PARTIAL: exact positive-integer linear-chain CRF inference only'
NOT_CLAIMED = ('parameter training', 'feature extraction', 'general graph inference', 'production readiness')


def _label(value):
    if type(value) is not str or not 1 <= len(value) <= 8:
        raise ValueError('label must be an exact string of 1..8 lowercase ASCII letters')
    if any(ch not in ALPHABET for ch in value):
        raise ValueError('label must be an exact string of 1..8 lowercase ASCII letters')


def _matrix(value, rows, columns):
    if type(value) is not list or len(value) != rows:
        raise ValueError('matrix row count mismatch or non-list')
    for row in value:
        if type(row) is not list or len(row) != columns:
            raise ValueError('matrix column count mismatch or non-list')
        for weight in row:
            if type(weight) is not int or not 1 <= weight <= 9:
                raise ValueError('potentials must be exact integers 1..9')


def _pair(value):
    return [value.numerator, value.denominator]


def infer_chain(data):
    if type(data) is not dict or set(data) != {'labels', 'unary', 'transition'}:
        raise ValueError('exact dict with labels, unary, transition required')
    labels, unary, transition = data['labels'], data['unary'], data['transition']
    if type(labels) is not list or not 2 <= len(labels) <= 4:
        raise ValueError('labels must be a list of 2..4 labels')
    if type(unary) is not list or not 1 <= len(unary) <= 6:
        raise ValueError('unary must be a list of 1..6 rows')
    for label in labels:
        _label(label)
    if len(set(labels)) != len(labels):
        raise ValueError('labels must be unique')
    n, sites = len(labels), len(unary)
    _matrix(unary, sites, n)
    _matrix(transition, n, n)
    forward = [unary[0][:]]
    best = [(unary[0][s], (s,)) for s in range(n)]
    for t in range(1, sites):
        forward.append([unary[t][s] * sum(forward[-1][p] * transition[p][s] for p in range(n)) for s in range(n)])
        next_best = []
        for s in range(n):
            candidates = [(weight * transition[p][s] * unary[t][s], path + (s,)) for p, (weight, path) in enumerate(best)]
            next_best.append(min(candidates, key=lambda item: (-item[0], item[1])))
        best = next_best
    partition = sum(forward[-1])
    backward = [[1] * n for _ in range(sites)]
    for t in range(sites - 2, -1, -1):
        backward[t] = [sum(transition[s][q] * unary[t + 1][q] * backward[t + 1][q] for q in range(n)) for s in range(n)]
    weight, path = min(best, key=lambda item: (-item[0], item[1]))
    return {'partition': partition, 'map': [labels[s] for s in path],
            'map_probability': _pair(Fraction(weight, partition)),
            'marginals': [[_pair(Fraction(forward[t][s] * backward[t][s], partition)) for s in range(n)] for t in range(sites)],
            'claims': [False, False, False, False]}
