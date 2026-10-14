"""Row 1423, Lesson Planning.

lesson_segment_fixture puts supplied teaching x then break_count then
practice y segments into a label-ordered abstract count timeline. Returns
segments (label,start,teach_end,practice_start,end), total and breaks total.
A break is included even with zero teaching/practice counts. No pedagogical
lesson plan, activity generation, outcome validation or advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
break_count defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, break_count, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: pedagogical lesson plan, activity generation, learning outcome validation, production readiness.
"""

SCOPE = 'PARTIAL: supplied teaching/practice count segment timing, no pedagogical lesson plan'
NOT_CLAIMED = ('pedagogical lesson plan', 'activity generation', 'learning outcome validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def lesson_segment_fixture(rows, break_count=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(break_count) is not int or not 0 <= break_count <= 5:
        raise ValueError('break_count must be a nonbool integer between 0 and 5')
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
    clock=0; segments=[]
    for n,teach,practice in sorted(clean,key=lambda r:r[0]):
        start=clock; practice_start=start+teach; end=practice_start+break_count+practice
        segments.append((n,start,practice_start,practice_start+break_count,end)); clock=end
    return {'segments':segments,'total':clock,'breaks':break_count*len(clean)}
