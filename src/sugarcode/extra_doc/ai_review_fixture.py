"""Row 1463, Artificial Intelligence in Education.

ai_review_fixture assigns review_per_item count checks per supplied
item count x and compares to supplied completed review count y. Returns
sorted reviews (label,required,done_capped,gap), ready zero-gap labels,
backlog and required totals. No educational AI system, content generation,
pedagogical validation, model safety assessment or actual student judgment.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
review_per_item defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, review_per_item, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: educational AI system, content generation, pedagogical validation, production readiness.
"""

SCOPE = 'PARTIAL: supplied generated/reviewed count review-backlog budget, no educational AI system'
NOT_CLAIMED = ('educational AI system', 'content generation', 'pedagogical validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ai_review_fixture(rows, review_per_item=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(review_per_item) is not int or not 1 <= review_per_item <= 5:
        raise ValueError('review_per_item must be a nonbool integer between 1 and 5')
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
    values=sorted((n,review_per_item*x,min(review_per_item*x,y),max(review_per_item*x-y,0)) for n,x,y in clean)
    return {'reviews':values,'ready':[n for n,r,d,g in values if g==0],
            'backlog':sum(g for n,r,d,g in values),'required':sum(r for n,r,d,g in values)}
