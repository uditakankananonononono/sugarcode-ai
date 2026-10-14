"""Row 1497, Programmed Instruction.

programmed_branch_fixture chooses advance if supplied response score x
meets threshold, otherwise repeat if supplied retry count y is positive,
else stop. Returns sorted branches and advance/repeat/stop label lists.
Advance takes priority even at zero retries. No actual programmed instruction,
content generation, response validation or learning effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
threshold defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: programmed instruction, content generation, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied response-count branch labels, no programmed instruction'
NOT_CLAIMED = ('programmed instruction', 'content generation', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def programmed_branch_fixture(rows, threshold=5):
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
    values=sorted((n,'advance' if x>=threshold else 'repeat' if y>0 else 'stop') for n,x,y in clean)
    return {'branches':values,'advance':[n for n,b in values if b=='advance'],
            'repeat':[n for n,b in values if b=='repeat'],'stop':[n for n,b in values if b=='stop']}
