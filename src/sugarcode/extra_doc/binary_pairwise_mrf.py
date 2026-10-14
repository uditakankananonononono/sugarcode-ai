"""Row 1046 Markov Random Fields - Undirected graphical models.

Exact binary pairwise MRF inference for 2..6 ordered nodes, positive integer
unary potentials (1..9), and 0..15 pairwise factors. Factor records are exact
lists [left_label, right_label, [00,01,10,11]] with weights 1..9. Each
undirected pair occurs at most once; table axes follow supplied endpoint order.
Return partition, single-node marginals, MAP bits and MAP probability. MAP ties
choose lexicographically smallest binary vector in supplied node order.
Caps precede scans. Nodes are lowercase ASCII strings of 1..8 letters.
NOT_CLAIMED: parameter learning, large-graph inference, causal conclusions,
production readiness.
"""
from fractions import Fraction
from itertools import product

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
SCOPE = 'PARTIAL: exact positive-integer binary pairwise MRF inference only'
NOT_CLAIMED = ('parameter learning', 'large-graph inference', 'causal conclusions', 'production readiness')


def _label(value):
    if type(value) is not str or not 1 <= len(value) <= 8 or any(c not in ALPHABET for c in value):
        raise ValueError('exact lowercase ASCII label required')


def _weights(value, size):
    if type(value) is not list or len(value) != size:
        raise ValueError('potential row must be an exact list with required size')
    for weight in value:
        if type(weight) is not int or not 1 <= weight <= 9:
            raise ValueError('potentials must be exact integers 1..9')


def infer(data):
    if type(data) is not dict or set(data) != {'nodes', 'unary', 'factors'}:
        raise ValueError('exact dict with nodes, unary, factors required')
    nodes, unary, factors = (data[k] for k in ('nodes', 'unary', 'factors'))
    if type(nodes) is not list or not 2 <= len(nodes) <= 6:
        raise ValueError('nodes must be a list of 2..6 labels')
    n = len(nodes)
    if type(unary) is not list or len(unary) != n:
        raise ValueError('unary must be one list per node')
    if type(factors) is not list or len(factors) > 15:
        raise ValueError('factors must be a list of at most 15 records')
    for node in nodes:
        _label(node)
    if len(set(nodes)) != n:
        raise ValueError('nodes must be unique')
    indices = {node: i for i, node in enumerate(nodes)}
    for row in unary:
        _weights(row, 2)
    seen = set()
    indexed_factors = []
    for record in factors:
        if type(record) is not list or len(record) != 3:
            raise ValueError('factor record must be an exact three-entry list')
        a, b, table = record
        _label(a)
        _label(b)
        if a not in indices or b not in indices or a == b:
            raise ValueError('factor requires distinct declared endpoints')
        key = tuple(sorted((a, b)))
        if key in seen:
            raise ValueError('duplicate undirected factor')
        seen.add(key)
        _weights(table, 4)
        indexed_factors.append((indices[a], indices[b], table))
    partition = 0
    marginals = [0 for _ in nodes]
    best_weight = None
    best_bits = None
    for bits in product((0, 1), repeat=n):
        weight = 1
        for i in range(n):
            weight *= unary[i][bits[i]]
        for a, b, table in indexed_factors:
            weight *= table[2 * bits[a] + bits[b]]
        partition += weight
        for i in range(n):
            if bits[i]:
                marginals[i] += weight
        if best_weight is None or weight > best_weight:
            best_weight = weight
            best_bits = bits
    probability = Fraction(best_weight, partition)
    return {'partition': partition,
            'marginals': {node: [Fraction(marginals[i], partition).numerator, Fraction(marginals[i], partition).denominator] for i, node in enumerate(nodes)},
            'map': list(best_bits), 'map_probability': [probability.numerator, probability.denominator],
            'claims': [False, False, False, False]}
