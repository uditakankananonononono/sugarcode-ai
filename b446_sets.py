"""Bounded exact finite-set arithmetic over caller-supplied integer IDs.

SCOPE: up to eight lists/tuples, each at most sixteen distinct IDs -100..100.
NOT_CLAIMED: retrieval, network, fuzzy matching, product integration.
"""
from fractions import Fraction
from itertools import combinations

CLAIMS = False
SCOPE = "exact arithmetic on bounded caller-supplied finite integer sets"
NOT_CLAIMED = "retrieval, network, fuzzy matching, product integration"
MAX_ITEMS = 16
MAX_GROUPS = 8
MAX_ID = 100


def _set(values):
    if type(values) not in (list, tuple):
        raise TypeError("set must be a list or tuple")
    if len(values) > MAX_ITEMS:
        raise ValueError("set size out of range")
    result = set()
    for value in values:
        if type(value) is not int:
            raise TypeError("id must be an integer")
        if value < -MAX_ID or value > MAX_ID:
            raise ValueError("id out of range")
        if value in result:
            raise ValueError("ids must be distinct")
        result.add(value)
    return result


def _pair(left, right):
    return _set(left), _set(right)


def _groups(groups):
    if type(groups) not in (list, tuple):
        raise TypeError("groups must be a list or tuple")
    if not 1 <= len(groups) <= MAX_GROUPS:
        raise ValueError("group count out of range")
    return [_set(group) for group in groups]


def union_size(left, right):
    a,b = _pair(left,right)
    return len(a | b)


def intersection_size(left, right):
    a,b = _pair(left,right)
    return len(a & b)


def symmetric_difference_size(left, right):
    a,b = _pair(left,right)
    return len(a ^ b)


def jaccard_similarity(left, right):
    """Empty/empty has similarity one."""
    a,b = _pair(left,right)
    denominator = len(a | b)
    return Fraction(len(a & b), denominator) if denominator else Fraction(1)


def dice_similarity(left, right):
    """Empty/empty has similarity one."""
    a,b = _pair(left,right)
    denominator = len(a)+len(b)
    return Fraction(2*len(a & b), denominator) if denominator else Fraction(1)


def overlap_coefficient(left, right):
    """Both empty yields one; exactly one empty yields zero."""
    a,b = _pair(left,right)
    if not a and not b:
        return Fraction(1)
    denominator = min(len(a),len(b))
    return Fraction(len(a & b), denominator) if denominator else Fraction(0)


def containment_fraction(left, right):
    """Fraction of left contained in right; empty left yields one."""
    a,b = _pair(left,right)
    return Fraction(len(a & b),len(a)) if a else Fraction(1)


def incidence_histogram(groups):
    """Map every degree 1..group count to its count in the implicit union."""
    data = _groups(groups)
    counts = {}
    for group in data:
        for value in group:
            counts[value] = counts.get(value,0)+1
    return {degree:sum(v==degree for v in counts.values()) for degree in range(1,len(data)+1)}


def exact_membership_count(groups, degree):
    """Count IDs in exactly degree groups; degree zero is zero (implicit union)."""
    data = _groups(groups)
    if type(degree) is not int:
        raise TypeError("degree must be an integer")
    if degree < 0 or degree > MAX_GROUPS:
        raise ValueError("degree out of range")
    universe = set().union(*data)
    return sum(sum(value in group for group in data)==degree for value in universe)


def inclusion_exclusion_union_size(groups):
    data = _groups(groups)
    total = 0
    for k in range(1,len(data)+1):
        for selected in combinations(data,k):
            total += (-1)**(k+1)*len(set.intersection(*selected))
    return total
