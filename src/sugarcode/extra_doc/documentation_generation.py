"""Row 703, Documentation Generation: numbering a table of contents.

Creates docs structure from supplied sections. Sections apply in
order, each a (title, level) row with title a string of 1 to 40
characters and level a nonbool int from 1 to 3. The first section must
be level 1 and each later section may go at most one level deeper than
the one before it; moving shallower is always allowed. Each section
gets a dotted number: a new level-1 section bumps the leading counter,
a deeper section starts a fresh counter at 1, and counters below the
current level reset. Reported: the (number, title) pairs in order and
the section count.
Caps (checked before any work): 0 to 50 sections.
NOT_CLAIMED: markup parsing, static site generation, cross references,
search indexing, templates, localization, production readiness.
"""
SCOPE = 'PARTIAL: dotted-number table of contents over supplied sections, no real doc tooling'
NOT_CLAIMED = ('markup parsing', 'static site generation', 'cross references',
               'search indexing', 'templates', 'localization', 'production readiness')

MAX_SECTIONS = 50
MAX_TITLE = 40
MAX_LEVEL = 3


def generate(sections):
    if type(sections) not in (list, tuple):
        raise TypeError('sections must be a list or tuple')
    if len(sections) > MAX_SECTIONS:
        raise ValueError('sections must contain at most 50 rows')
    rows = []
    previous = 0
    for row in sections:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each section must be a (title, level) row')
        title, level = row
        if type(title) is not str or not 1 <= len(title) <= MAX_TITLE:
            raise ValueError('title must be a string of 1 to 40 characters')
        if type(level) is not int or not 1 <= level <= MAX_LEVEL:
            raise ValueError('level must be a nonbool integer between 1 and 3')
        if level > previous + 1:
            raise ValueError('levels must step one level at a time')
        previous = level
        rows.append((title, level))
    counters = [0, 0, 0]
    toc = []
    for title, level in rows:
        counters[level - 1] += 1
        for deeper in range(level, MAX_LEVEL):
            counters[deeper] = 0
        toc.append(('.'.join(str(counters[i]) for i in range(level)), title))
    return {'toc': toc, 'sections': len(rows)}
