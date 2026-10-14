"""Row 1872, Title: Genre Studies

classify_shelves(rows): rows are (shelf, book, code) triples; shelf
and book strings of 1 to 16 characters; code a nonbool integer
between 1 and 99. Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each shelf the number of books,
for each shelf the digital root of its total code (repeated digit
sums until one digit remains), the prime shelves (a root of 2, 3, 5
or 7) in ascending order, the perfect shelves (a root of 9) in
ascending order, and the dominant root (the root held by the most
shelves, the smaller root on ties).

SCOPE: PARTIAL: shelf classification over supplied codes
NOT_CLAIMED: real librarianship, numerology, collection value,
genre boundaries, production readiness.
"""

SCOPE = 'PARTIAL: shelf classification over supplied codes'
NOT_CLAIMED = ('real librarianship', 'numerology', 'collection value',
               'genre boundaries', 'production readiness')


def classify_shelves(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (shelf, book, code) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        shelf, book, code = row
        if type(shelf) is not str or not 1 <= len(shelf) <= 16:
            raise ValueError(f'row {i}: shelf must be a string of 1 to 16 characters')
        if type(book) is not str or not 1 <= len(book) <= 16:
            raise ValueError(f'row {i}: book must be a string of 1 to 16 characters')
        if type(code) is not int or not 1 <= code <= 99:
            raise ValueError(f'row {i}: code must be a nonbool integer between 1 and 99')
    books = {}
    totals = {}
    for shelf, book, code in rows:
        if shelf not in books:
            books[shelf] = 0
        books[shelf] += 1
        if shelf not in totals:
            totals[shelf] = 0
        totals[shelf] += code
    roots = {}
    for shelf in totals:
        root = totals[shelf] % 9
        roots[shelf] = root if root else 9
    prime = sorted(s for s in roots if roots[s] in (2, 3, 5, 7))
    perfect = sorted(s for s in roots if roots[s] == 9)
    holders = {}
    for shelf in roots:
        if roots[shelf] not in holders:
            holders[roots[shelf]] = 0
        holders[roots[shelf]] += 1
    dominant = None
    for root in holders:
        if (dominant is None or holders[root] > holders[dominant]
                or (holders[root] == holders[dominant]
                    and root < dominant)):
            dominant = root
    return {'total': len(rows),
            'books': books,
            'roots': roots,
            'prime': prime,
            'perfect': perfect,
            'dominant': dominant}
