"""Row 1096, Random Forests - Ensemble of trees.

forest_stumps treats x as a supplied stump threshold and y as its supplied
integer importance score. Vote one when query>=threshold, else zero. Aggregate
unweighted majority with tie zero. Returns votes as sorted (label,bit),
prediction as majority bit, margins as sorted (label,query-threshold),
importance_sum as supplied importance total. Importances are reported only,
not used in voting; no random forest training or randomization is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
query defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, query, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: random forest training, feature subsampling, generalization accuracy, tree validity, production readiness.
"""

SCOPE = 'PARTIAL: aggregates supplied threshold stumps with deterministic majority, no forest is trained'
NOT_CLAIMED = ('random forest training', 'feature subsampling', 'generalization accuracy', 'tree validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def forest_stumps(rows, query=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(query) is not int or not 0 <= query <= 100:
        raise ValueError('query must be a nonbool integer between 0 and 100')
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
    votes = [(n, int(query >= threshold)) for n, threshold, importance in sorted(clean, key=lambda r: r[0])]
    ones = sum(v for n, v in votes)
    margins = [(n, query - threshold) for n, threshold, importance in sorted(clean, key=lambda r: r[0])]
    importance_sum = sum(importance for n, threshold, importance in clean)
    return {'votes': votes, 'prediction': int(2 * ones > len(votes)),
            'margins': margins, 'importance_sum': importance_sum}
