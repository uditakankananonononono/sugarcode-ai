"""Row 743, Brainstorming: deduplicating supplied ideas.

Generates ideas collectively by collecting. Each idea is an
(author, text) row with author a string of 1 to 8 characters and text
a string of 1 to 40 characters. Reported: the distinct idea texts in
first-seen order, how many rows repeated an earlier text, the
(author, row count) pairs sorted by author, and the total row count.
Caps (checked before any work): 0 to 100 ideas.
NOT_CLAIMED: real sessions, idea quality, clustering, voting,
facilitation, creativity techniques, production readiness.
"""
SCOPE = 'PARTIAL: idea dedup over supplied rows, no real brainstorming'
NOT_CLAIMED = ('real sessions', 'idea quality', 'clustering', 'voting',
               'facilitation', 'creativity techniques', 'production readiness')

MAX_IDEAS = 100
MAX_AUTHOR = 8
MAX_TEXT = 40


def collect(ideas):
    if type(ideas) not in (list, tuple):
        raise TypeError('ideas must be a list or tuple')
    if len(ideas) > MAX_IDEAS:
        raise ValueError('ideas must contain at most 100 rows')
    rows = []
    for row in ideas:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each idea must be an (author, text) row')
        author, text = row
        if type(author) is not str or not 1 <= len(author) <= MAX_AUTHOR:
            raise ValueError('author must be a string of 1 to 8 characters')
        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:
            raise ValueError('text must be a string of 1 to 40 characters')
        rows.append((author, text))
    seen = set()
    unique = []
    duplicates = 0
    authors = {}
    for author, text in rows:
        if text in seen:
            duplicates += 1
        else:
            seen.add(text)
            unique.append(text)
        authors[author] = authors.get(author, 0) + 1
    return {'ideas': unique, 'duplicates': duplicates,
            'authors': sorted(authors.items()), 'total': len(rows)}
