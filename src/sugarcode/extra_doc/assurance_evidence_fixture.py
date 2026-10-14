"""Row 1545, Quality Assurance.

assurance_evidence_fixture caps copies times supplied evidence y counts
at supplied requirement x counts. Returns sorted covered counts, required
total, missing count and complete inclusive coverage boolean. No quality
assurance certification, evidence validity, audit execution, standards
compliance or real product-quality judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
copies defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, copies, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: quality assurance certification, evidence validity, audit execution, standards compliance, production readiness.
"""

SCOPE = 'PARTIAL: supplied requirement/evidence count coverage, no quality assurance certification'
NOT_CLAIMED = ('quality assurance certification', 'evidence validity', 'audit execution', 'standards compliance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def assurance_evidence_fixture(rows, copies=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(copies) is not int or not 1 <= copies <= 5:
        raise ValueError('copies must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(x,copies*y)) for n,x,y in clean)
    required=sum(x for n,x,y in clean)
    covered=sum(v for n,v in values)
    return {'covered':values,'required':required,'missing':required-covered,
            'complete':all(x<=copies*y for n,x,y in clean)}
