"""Row 1088, Holm-Bonferroni - Step-down correction.

holm_adjust encodes supplied p-values as x/(100+y), orders ascending p then
label, and computes adjusted p at rank i as capped running maximum of
(m-i)*p_i, with zero-based i and family size m. Returns adjusted as
(label,Fraction string) in p-rank order, rejected in that order when adjusted
p is at most alpha percent. Raw p-value validity is caller responsibility.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
alpha defaults to 5, an exact int from 1 to 100.
Validation order: rows type, rows size, alpha, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: p-value validity, sampling provenance, causal claims, actual family coverage, production readiness.
"""

SCOPE = 'PARTIAL: applies exact Holm step-down adjusted p-values to supplied rational p-values'
NOT_CLAIMED = ('p-value validity', 'sampling provenance', 'causal claims', 'actual family coverage', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def holm_adjust(rows, alpha=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(alpha) is not int or not 1 <= alpha <= 100:
        raise ValueError('alpha must be a nonbool integer between 1 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    ranked = sorted([(n, F(x, 100+y)) for n, x, y in clean], key=lambda r: (r[1], r[0]))
    adjusted = []
    running = F(0)
    for i, (n, p) in enumerate(ranked):
        running = max(running, (len(ranked) - i) * p)
        adjusted.append((n, min(F(1), running)))
    return {'adjusted': [(n, str(p)) for n, p in adjusted],
            'rejected': [n for n, p in adjusted if p <= F(alpha, 100)]}
