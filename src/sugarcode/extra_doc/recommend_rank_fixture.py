"""Row 1472, Recommendation Systems.

recommend_rank_fixture ranks supplied interest count x twice minus cost
count y descending, ties label ascending, then takes at most limit. Returns
selected and remaining (label,score) in rank order, limit and selected_total.
No learned recommendations, real user preference inference, external data
retrieval, relevance validation or actual recommendation quality is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
limit defaults to 3, an exact int from 1 to 8.
Validation order: rows type, rows size, limit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: learned recommendations, user preference inference, external data retrieval, production readiness.
"""

SCOPE = 'PARTIAL: supplied interest/cost count top-k ranking, no learned recommendations'
NOT_CLAIMED = ('learned recommendations', 'user preference inference', 'external data retrieval', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def recommend_rank_fixture(rows, limit=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(limit) is not int or not 1 <= limit <= 8:
        raise ValueError('limit must be a nonbool integer between 1 and 8')
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
    ranked=sorted(clean,key=lambda r:(-(2*r[1]-r[2]),r[0]))
    values=[(n,2*x-y) for n,x,y in ranked]
    return {'selected':values[:limit],'remaining':values[limit:],'limit':limit,
            'selected_total':sum(v for n,v in values[:limit])}
