"""Row 1092, Permutation-Based FDR - Empirical null.

permutation_false_ratio treats x as observed test score and y as a supplied
null score. For every unique observed/null threshold descending, count inclusive
exceedances in both sets. Estimate null exceedances/(replicates*observed
exceedances), capped at one, None with zero observed discoveries. Returns
estimates as (threshold, observed_count, null_count, Fraction_string_or_None),
replicates as the supplied scaling count. It does not create permutations or
verify that pooled null scores represent the stated number of replicates.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
replicates defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, replicates, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: exchangeability validity, FDR guarantee, null provenance, sampling independence, production readiness.
"""

SCOPE = 'PARTIAL: compares observed and permutation-null exceedance counts with a supplied null-replicate count'
NOT_CLAIMED = ('exchangeability validity', 'FDR guarantee', 'null provenance', 'sampling independence', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def permutation_false_ratio(rows, replicates=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(replicates) is not int or not 1 <= replicates <= 5:
        raise ValueError('replicates must be a nonbool integer between 1 and 5')
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
    thresholds = sorted({v for n, observed, null in clean for v in (observed, null)}, reverse=True)
    estimates = []
    for t in thresholds:
        discoveries = sum(observed >= t for n, observed, null in clean)
        false_count = sum(null >= t for n, observed, null in clean)
        estimate = min(F(1), F(false_count, replicates * discoveries)) if discoveries else None
        estimates.append((t, discoveries, false_count, str(estimate) if estimate is not None else None))
    return {'estimates': estimates, 'replicates': replicates}
