"""Row 1132, Sepsis Early Warning.

warning_run consumes supplied marker pairs x,y in caller order; a hit means
both are at least threshold. Returns hits as (label,bool) in caller order,
longest as maximum consecutive hit count, first_pair as label of the second
hit in the earliest consecutive pair, or None. Threshold and marker meanings
are supplied, not clinical; no sepsis detection or medical warning is made.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
threshold defaults to 50, an exact int from 1 to 100.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: sepsis warning, clinical thresholds, medical diagnosis, measurement validity, production readiness.
"""

SCOPE = 'PARTIAL: detects consecutive supplied dual-marker threshold hits, no sepsis warning is generated'
NOT_CLAIMED = ('sepsis warning', 'clinical thresholds', 'medical diagnosis', 'measurement validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def warning_run(rows, threshold=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 1 <= threshold <= 100:
        raise ValueError('threshold must be a nonbool integer between 1 and 100')
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
    hits = []
    run = longest = 0
    first_pair = None
    for n, first, second in clean:
        hit = first >= threshold and second >= threshold
        hits.append((n, hit))
        run = run + 1 if hit else 0
        longest = max(longest, run)
        if run == 2 and first_pair is None:
            first_pair = n
    return {'hits': hits, 'longest': longest, 'first_pair': first_pair}
