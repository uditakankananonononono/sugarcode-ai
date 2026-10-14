"""Row 1430, Backward Design.

backward_budget_fixture treats x as supplied goal count and y as evidence
count per goal, then multiplies evidence by activities_per_evidence. Returns
sorted budgets (label,evidence,activities), evidence/activities totals and
empty zero-evidence labels. No backward instructional design, semantic
alignment validation, goal inference or activity generation is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
activities_per_evidence defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, activities_per_evidence, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: backward instructional design, alignment validation, activity generation, production readiness.
"""

SCOPE = 'PARTIAL: derives supplied evidence/activity count budgets from goal counts, no backward instructional design'
NOT_CLAIMED = ('backward instructional design', 'alignment validation', 'activity generation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def backward_budget_fixture(rows, activities_per_evidence=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(activities_per_evidence) is not int or not 1 <= activities_per_evidence <= 5:
        raise ValueError('activities_per_evidence must be a nonbool integer between 1 and 5')
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
    values=sorted((n,x*y,x*y*activities_per_evidence) for n,x,y in clean)
    return {'budgets':values,'evidence':sum(e for n,e,a in values),
            'activities':sum(a for n,e,a in values),'empty':[n for n,e,a in values if e==0]}
