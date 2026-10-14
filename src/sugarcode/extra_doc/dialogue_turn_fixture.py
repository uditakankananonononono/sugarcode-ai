"""Row 1500, Dialogue-Based Tutoring.

dialogue_turn_fixture caps supplied answered count y at question count x,
counts unanswered and allocates followups per unanswered. Returns sorted
turns (label,answered,unanswered,followup_count), answered, followup_total
and complete zero-unanswered labels. No dialogue tutoring, language
understanding, question generation or learning effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
followups defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, followups, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: dialogue tutoring, language understanding, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied question/answer count turn budget, no dialogue tutoring'
NOT_CLAIMED = ('dialogue tutoring', 'language understanding', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def dialogue_turn_fixture(rows, followups=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(followups) is not int or not 0 <= followups <= 5:
        raise ValueError('followups must be a nonbool integer between 0 and 5')
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
    values=sorted((n,min(x,y),max(x-y,0),followups*max(x-y,0)) for n,x,y in clean)
    return {'turns':values,'answered':sum(a for n,a,u,f in values),
            'followup_total':sum(f for n,a,u,f in values),'complete':[n for n,a,u,f in values if u==0]}
