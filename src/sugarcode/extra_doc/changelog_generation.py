"""Row 701, Changelog Generation: grouping supplied entries into sections.

Documents changes by category. Entries apply in order, each a
(category, text) row with category the string added, changed, fixed,
or removed and text a string of 1 to 40 characters. The report groups
texts under their category, keeping the supplied order inside each
section and listing sections in the canonical order added, changed,
fixed, removed, skipping empty ones. Reported: the sections and the
total number of entries.
Caps (checked before any work): 0 to 100 entries; text a string of 1
to 40 characters.
NOT_CLAIMED: git history, commit parsing, release automation, markdown
rendering, version inference, localization, production readiness.
"""
SCOPE = 'PARTIAL: category grouping over supplied entries, no real changelog tooling'
NOT_CLAIMED = ('git history', 'commit parsing', 'release automation',
               'markdown rendering', 'version inference', 'localization',
               'production readiness')

MAX_ENTRIES = 100
MAX_TEXT = 40
ORDER = ('added', 'changed', 'fixed', 'removed')


def generate(entries):
    if type(entries) not in (list, tuple):
        raise TypeError('entries must be a list or tuple')
    if len(entries) > MAX_ENTRIES:
        raise ValueError('entries must contain at most 100 rows')
    rows = []
    for row in entries:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each entry must be a (category, text) row')
        category, text = row
        if type(category) is not str or category not in ORDER:
            raise ValueError('category must be the string added, changed, fixed, or removed')
        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:
            raise ValueError('text must be a string of 1 to 40 characters')
        rows.append((category, text))
    grouped = {category: [] for category in ORDER}
    for category, text in rows:
        grouped[category].append(text)
    return {'sections': [(category, grouped[category]) for category in ORDER if grouped[category]],
            'total': len(rows)}
