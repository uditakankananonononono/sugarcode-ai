"""Row 748, Rhetoric: profiling supplied appeals by mode.

Persuades effectively by counting. Each row pairs a text of 1 to 60
characters with a mode of 'ethos', 'pathos', or 'logos'. Reported:
the three mode counts, the dominant mode (the largest count, ties
broken in canonical order ethos, pathos, logos, and None when there
are no rows), and the row count. Caps (checked before any work):
0 to 100 rows.
NOT_CLAIMED: real persuasion, speechwriting, audience analysis,
fallacy detection, delivery, ethics, production readiness.
"""
SCOPE = 'PARTIAL: appeal counting over supplied rows, no real rhetoric'
NOT_CLAIMED = ('real persuasion', 'speechwriting', 'audience analysis',
               'fallacy detection', 'delivery', 'ethics', 'production readiness')

MAX_ROWS = 100
MAX_TEXT = 60
MODES = ('ethos', 'pathos', 'logos')


def profile(appeals):
    if type(appeals) not in (list, tuple):
        raise TypeError('appeals must be a list or tuple')
    if len(appeals) > MAX_ROWS:
        raise ValueError('appeals must contain at most 100 rows')
    rows = []
    for row in appeals:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each appeal must be a (text, mode) row')
        text, mode = row
        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:
            raise ValueError('text must be a string of 1 to 60 characters')
        if type(mode) is not str or mode not in MODES:
            raise ValueError('mode must be ethos, pathos, or logos')
        rows.append((text, mode))
    counts = {'ethos': 0, 'pathos': 0, 'logos': 0}
    for text, mode in rows:
        counts[mode] += 1
    dominant = None
    if rows:
        dominant = max(MODES, key=lambda mode: counts[mode])
    return {'ethos': counts['ethos'], 'pathos': counts['pathos'],
            'logos': counts['logos'], 'dominant': dominant, 'rows': len(rows)}
