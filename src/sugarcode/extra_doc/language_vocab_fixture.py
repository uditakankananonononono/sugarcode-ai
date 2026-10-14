"""Row 1518, Language Learning.

language_vocab_fixture caps supplied recalled count y at vocabulary
count x, counts gaps and allocates reviews per gap. Returns sorted vocabulary
(label,recalled,gap,review_count), complete zero-gap labels, review_total and
recalled total. No language learning assessment, language identification,
recall verification, instruction or learning effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
reviews defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, reviews, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: language learning assessment, language identification, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied vocabulary/recall count review budget, no language learning assessment'
NOT_CLAIMED = ('language learning assessment', 'language identification', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def language_vocab_fixture(rows, reviews=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(reviews) is not int or not 1 <= reviews <= 5:
        raise ValueError('reviews must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(x,y),max(x-y,0),reviews*max(x-y,0)) for n,x,y in clean)
    return {'vocabulary':values,'complete':[n for n,r,g,b in values if g==0],
            'review_total':sum(b for n,r,g,b in values),'recalled':sum(r for n,r,g,b in values)}
