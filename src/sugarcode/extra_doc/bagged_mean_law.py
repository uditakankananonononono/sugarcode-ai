"""Row 1104, Bagging - Bootstrap aggregating.

bagged_mean_law pools paired readings into an empirical population, draws
draws independent values with replacement and considers their mean. Returns
expected_mean as empirical mean Fraction string, mean_variance as empirical
population variance divided by draws Fraction string, draws as supplied draw
count, population as pooled count. This gives exact bootstrap mean moments,
not trained model aggregation or a confidence interval.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
draws defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, draws, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: trained bagged models, generalization, independent data, bootstrap consistency, production readiness.
"""

SCOPE = 'PARTIAL: computes exact bootstrap mean expectation and variance from supplied paired readings'
NOT_CLAIMED = ('trained bagged models', 'generalization', 'independent data', 'bootstrap consistency', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def bagged_mean_law(rows, draws=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(draws) is not int or not 1 <= draws <= 5:
        raise ValueError('draws must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not -10 <= x <= 10:
            raise ValueError('x must be a nonbool integer between -10 and 10')
        if type(y) is not int or not -10 <= y <= 10:
            raise ValueError('y must be a nonbool integer between -10 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    values = [v for n, x, y in clean for v in (x, y)]
    mean = F(sum(values), len(values))
    variance = sum(((v - mean) ** 2 for v in values), F(0)) / len(values)
    return {'expected_mean': str(mean), 'mean_variance': str(variance / draws),
            'draws': draws, 'population': len(values)}
