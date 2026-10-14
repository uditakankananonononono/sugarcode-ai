"""Row 1455, Microlearning.

microlearning_chunk_fixture combines supplied content x and practice y
counts and splits each row into chunk-sized pieces with trailing remainder,
no zero-sized chunk. Returns sorted chunks (label,list), count and load
total. Zero load produces an empty list. No microlearning pedagogy,
content generation, learner assessment or learning effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
chunk defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, chunk, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: microlearning pedagogy, content generation, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: splits supplied content/practice counts into small count chunks, no microlearning pedagogy'
NOT_CLAIMED = ('microlearning pedagogy', 'content generation', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def microlearning_chunk_fixture(rows, chunk=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(chunk) is not int or not 1 <= chunk <= 5:
        raise ValueError('chunk must be a nonbool integer between 1 and 5')
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
    values=[]
    for n,content,practice in sorted(clean,key=lambda r:r[0]):
        total=content+practice; q,r=divmod(total,chunk)
        values.append((n,[chunk]*q+([r] if r else [])))
    return {'chunks':values,'count':sum(len(v) for n,v in values),
            'load':sum(x+y for n,x,y in clean)}
