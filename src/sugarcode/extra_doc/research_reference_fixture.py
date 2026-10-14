"""Row 1220, Legal Research.

research_reference_fixture expands supplied start x and count y into opaque
(label,index) references and chunks them by page_size in label/index order.
Returns pages, count and empty labels with zero supplied count. It retrieves
no law, case, authority or source and supplies no legal advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
page_size defaults to 3, an exact int from 1 to 10.
Validation order: rows type, rows size, page_size, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal research, source retrieval, legal authority, jurisdictional advice, production readiness.
"""

SCOPE = 'PARTIAL: paginates abstract supplied reference indices, no legal research'
NOT_CLAIMED = ('legal research', 'source retrieval', 'legal authority', 'jurisdictional advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def research_reference_fixture(rows, page_size=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(page_size) is not int or not 1 <= page_size <= 10:
        raise ValueError('page_size must be a nonbool integer between 1 and 10')
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
    references=[]
    for n,start,count in sorted(clean,key=lambda r:r[0]):
        references.extend((n,i) for i in range(start,start+count))
    pages=[references[i:i+page_size] for i in range(0,len(references),page_size)]
    return {'pages':pages,'count':len(references),'empty':sorted(n for n,start,count in clean if count==0)}
