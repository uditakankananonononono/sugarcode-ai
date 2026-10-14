"""Row 1421, Assessment Design.

assessment_coverage_fixture requires items_per_target times supplied
target count x and compares to supplied available item count y. Returns
sorted coverage (label,required,available,gap), adequate zero-gap labels,
additional gap total and required total. No question generation, content
alignment validation, assessment validity design or learning measurement.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
items_per_target defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, items_per_target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: assessment validity design, question generation, learning measurement, production readiness.
"""

SCOPE = 'PARTIAL: supplied target/item count coverage deficits, no assessment validity design'
NOT_CLAIMED = ('assessment validity design', 'question generation', 'learning measurement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def assessment_coverage_fixture(rows, items_per_target=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(items_per_target) is not int or not 1 <= items_per_target <= 5:
        raise ValueError('items_per_target must be a nonbool integer between 1 and 5')
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
    values=sorted((n,items_per_target*x,y,max(items_per_target*x-y,0)) for n,x,y in clean)
    return {'coverage':values,'adequate':[n for n,r,a,g in values if g==0],
            'additional':sum(g for n,r,a,g in values),'required':sum(r for n,r,a,g in values)}
