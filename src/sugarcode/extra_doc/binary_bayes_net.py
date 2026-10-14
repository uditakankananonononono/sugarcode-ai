"""Row 1045 Bayesian Networks - Causal probabilistic models.

Exact observational inference in a binary DAG with 2..6 ordered nodes. Parents
must precede their child; CPT lists hold integer P(node=1) percentages 1..99,
indexed by parent bits in supplied parent order, most significant bit first.
Evidence is a node->0/1 dict. Return exact evidence probability and posterior
P(node=1) fractions. No intervention or causal identification is inferred.
Caps precede scans. Nodes are lowercase ASCII strings of 1..8 letters.
NOT_CLAIMED: causal identification, intervention inference, parameter learning,
production readiness.
"""
from fractions import Fraction
from itertools import product

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
SCOPE = 'PARTIAL: exact observational inference in a supplied binary DAG only'
NOT_CLAIMED = ('causal identification', 'intervention inference', 'parameter learning', 'production readiness')


def _label(value):
    if type(value) is not str or not 1 <= len(value) <= 8 or any(c not in ALPHABET for c in value):
        raise ValueError('exact lowercase ASCII label required')


def infer(data):
    if type(data) is not dict or set(data) != {'nodes', 'parents', 'cpt', 'evidence'}:
        raise ValueError('exact dict with nodes, parents, cpt, evidence required')
    nodes, parents, cpt, evidence = (data[k] for k in ('nodes', 'parents', 'cpt', 'evidence'))
    if type(nodes) is not list or not 2 <= len(nodes) <= 6:
        raise ValueError('nodes must be a list of 2..6 labels')
    n = len(nodes)
    if type(parents) is not list or len(parents) != n:
        raise ValueError('parents must be one list per node')
    if type(cpt) is not list or len(cpt) != n:
        raise ValueError('cpt must be one list per node')
    if type(evidence) is not dict or len(evidence) > n:
        raise ValueError('evidence must be a bounded exact dict')
    for node in nodes:
        _label(node)
    if len(set(nodes)) != n:
        raise ValueError('nodes must be unique')
    indices = {node: i for i, node in enumerate(nodes)}
    parent_indices = []
    for i, row in enumerate(parents):
        if type(row) is not list or len(row) > i:
            raise ValueError('parent rows must be exact bounded lists')
        for parent in row:
            _label(parent)
            if parent not in nodes[:i]:
                raise ValueError('parents must precede their child')
        if len(set(row)) != len(row):
            raise ValueError('parents must be unique')
        parent_indices.append([indices[parent] for parent in row])
        table = cpt[i]
        if type(table) is not list or len(table) != 2 ** len(row):
            raise ValueError('cpt row size must equal 2**parent_count')
        for probability in table:
            if type(probability) is not int or not 1 <= probability <= 99:
                raise ValueError('cpt entries must be exact integer percentages 1..99')
    for key, value in evidence.items():
        _label(key)
        if key not in indices or type(value) is not int or value not in (0, 1):
            raise ValueError('evidence must name declared nodes with exact binary values')
    mass = Fraction(0)
    posterior = [Fraction(0) for _ in nodes]
    for bits in product((0, 1), repeat=n):
        if any(bits[indices[key]] != value for key, value in evidence.items()):
            continue
        weight = Fraction(1)
        for i in range(n):
            pattern = ''.join(str(bits[parent]) for parent in parent_indices[i])
            index = int(pattern or '0', 2)
            probability = cpt[i][index]
            weight *= Fraction(probability if bits[i] else 100 - probability, 100)
        mass += weight
        for i in range(n):
            if bits[i]:
                posterior[i] += weight
    return {'evidence_probability': [mass.numerator, mass.denominator],
            'posterior': {node: [(posterior[i] / mass).numerator, (posterior[i] / mass).denominator] for i, node in enumerate(nodes)},
            'claims': [False, False, False, False]}
