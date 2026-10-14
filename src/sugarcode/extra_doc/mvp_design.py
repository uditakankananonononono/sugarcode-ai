"""Row 372 Minimum Viable Product Design - Tests core hypotheses: supplied-budget test selection.

Hypotheses are (label, cost, learning) with cost and learning ints 0..1000 the
caller supplies. Picks the subset within budget with the highest total learning;
ties go to lower cost, then fewer hypotheses, then the lexicographically smaller
index tuple. 1 to 12 hypotheses, budget int 0..10000, labels unique strings of
1 to 40 characters with no control, format, private-use, surrogate or unassigned
characters. Caps are implementation choices.
NOT_CLAIMED: that any hypothesis is true or was tested, accuracy of the supplied
cost or learning numbers, customer evidence, market demand or product viability.
"""
import itertools
import unicodedata


def _label_ok(s):
    return type(s) is str and 1 <= len(s) <= 40 and all(unicodedata.category(c)[0] != 'C' for c in s)


def select_tests(hypotheses, budget):
    if type(hypotheses) not in (list, tuple):
        raise TypeError('hypotheses must be a list or tuple')
    if not 1 <= len(hypotheses) <= 12:
        raise ValueError('hypothesis count must be between 1 and 12')
    if any(type(h) not in (list, tuple) or len(h) != 3 for h in hypotheses):
        raise ValueError('hypotheses must be label cost learning triples')
    if any(not _label_ok(h[0]) for h in hypotheses):
        raise ValueError('labels must be 1 to 40 characters without control or unassigned characters')
    if any(type(v) is not int or not 0 <= v <= 1000 for h in hypotheses for v in h[1:]):
        raise ValueError('cost and learning must be nonbool integers zero through 1000')
    if type(budget) is not int or not 0 <= budget <= 10000:
        raise ValueError('budget must be a nonbool integer zero through 10000')
    if len({h[0] for h in hypotheses}) != len(hypotheses):
        raise ValueError('labels must be unique')
    best = None
    for r in range(len(hypotheses) + 1):
        for ch in itertools.combinations(range(len(hypotheses)), r):
            cost = sum(hypotheses[i][1] for i in ch)
            if cost > budget:
                continue
            key = (-sum(hypotheses[i][2] for i in ch), cost, r, ch)
            if best is None or key < best:
                best = key
    neg, cost, _, ch = best
    return {'selected': list(ch), 'labels': [hypotheses[i][0] for i in ch], 'learning': -neg,
            'cost': cost, 'hypotheses_tested': False}
