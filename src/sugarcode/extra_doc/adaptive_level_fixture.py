"""Row 1434, Adaptive Learning.

adaptive_level_fixture raises supplied level count x by one capped at ten
when supplied success count y exceeds threshold, lowers by one floored at
zero below threshold, holds on equality. Returns sorted levels, raised and
lowered labels for actual level changes, and threshold. No adaptive learning
system, learner assessment, skill validation or pedagogical recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
threshold defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: adaptive learning system, learner assessment, pedagogical recommendation, production readiness.
"""

SCOPE = 'PARTIAL: updates supplied count levels using success-count bands, no adaptive learning system'
NOT_CLAIMED = ('adaptive learning system', 'learner assessment', 'pedagogical recommendation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def adaptive_level_fixture(rows, threshold=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 10:
        raise ValueError('threshold must be a nonbool integer between 0 and 10')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    values=sorted((n,min(x+1,10) if y>threshold else max(x-1,0) if y<threshold else x) for n,x,y in clean)
    return {'levels':values,'raised':sorted(n for n,x,y in clean if y>threshold and x<10),
            'lowered':sorted(n for n,x,y in clean if y<threshold and x>0),'threshold':threshold}
