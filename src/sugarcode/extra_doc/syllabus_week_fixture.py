"""Row 1426, Syllabus Creation.

syllabus_week_fixture formats supplied label, lecture x and practice y
counts into fixed weekly strings in label order, assigning consecutive
weeks from first_week. Returns sorted lines (label,text), last_week, hours
sum and weeks row count. No syllabus content design, course policy,
academic dates, prerequisite inference or accreditation compliance is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
first_week defaults to 1, an exact int from 1 to 10.
Validation order: rows type, rows size, first_week, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: syllabus content design, course policy generation, accreditation compliance, production readiness.
"""

SCOPE = 'PARTIAL: formats supplied topic/hour counts into abstract weekly lines, no syllabus content design'
NOT_CLAIMED = ('syllabus content design', 'course policy generation', 'accreditation compliance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def syllabus_week_fixture(rows, first_week=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(first_week) is not int or not 1 <= first_week <= 10:
        raise ValueError('first_week must be a nonbool integer between 1 and 10')
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
    values=[(n,f'Week {first_week+i}: {n} ({x} lecture, {y} practice)',first_week+i) for i,(n,x,y) in enumerate(sorted(clean,key=lambda r:r[0]))]
    return {'lines':[(n,text) for n,text,week in values],'last_week':values[-1][2],
            'hours':sum(x+y for n,x,y in clean),'weeks':len(clean)}
