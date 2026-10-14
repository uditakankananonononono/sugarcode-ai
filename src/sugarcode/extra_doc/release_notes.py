"""Row 702, Release Notes: drafting one note from supplied entries.

Informs users what one release brings. The version is a (major, minor,
patch) row. Entries apply in supplied order, each a (kind, text) row
with kind the string breaking, feature, or fix and text a string of 1
to 40 characters. The report carries the title 'Release M.m.p', the
breaking, features, and fixes lists in supplied order, and
upgrade_required, true exactly when the breaking list is nonempty.
Caps (checked before any work): each supplied version component a
nonbool int from 0 to 100; 0 to 100 entries.
NOT_CLAIMED: git tags, release automation, changelog parsing, markdown
rendering, audience targeting, localization, production readiness.
"""
SCOPE = 'PARTIAL: entry grouping and title formatting over supplied data, no real release tooling'
NOT_CLAIMED = ('git tags', 'release automation', 'changelog parsing',
               'markdown rendering', 'audience targeting', 'localization',
               'production readiness')

MAX_COMPONENT = 100
MAX_ENTRIES = 100
MAX_TEXT = 40


def draft(version, entries):
    if type(version) not in (list, tuple):
        raise TypeError('version must be a list or tuple')
    if len(version) != 3:
        raise ValueError('version must be a (major, minor, patch) row')
    for component in version:
        if type(component) is not int or not 0 <= component <= MAX_COMPONENT:
            raise ValueError('version components must be nonbool integers between 0 and 100')
    if type(entries) not in (list, tuple):
        raise TypeError('entries must be a list or tuple')
    if len(entries) > MAX_ENTRIES:
        raise ValueError('entries must contain at most 100 rows')
    rows = []
    for row in entries:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each entry must be a (kind, text) row')
        kind, text = row
        if type(kind) is not str or kind not in ('breaking', 'feature', 'fix'):
            raise ValueError('kind must be the string breaking, feature, or fix')
        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:
            raise ValueError('text must be a string of 1 to 40 characters')
        rows.append((kind, text))
    major, minor, patch = version
    breaking = [text for kind, text in rows if kind == 'breaking']
    features = [text for kind, text in rows if kind == 'feature']
    fixes = [text for kind, text in rows if kind == 'fix']
    return {'title': 'Release %d.%d.%d' % (major, minor, patch),
            'breaking': breaking, 'features': features, 'fixes': fixes,
            'upgrade_required': len(breaking) > 0}
