"""Row 634, Dashboards: placing panels on a fixed-width grid.

panels is a list or tuple of 0 to 30 (title, width) pairs, placed in order from
left to right. A panel goes in the current row when it fits in the columns
left, otherwise it starts a new row at column 0. Rows are never reordered and
earlier gaps are never filled. Reported: the titles per row, each panel's
(title, row, column) placement with 0-based row and column, the number of
rows and the columns used in each row.
Caps (checked before any work): unique titles of 1 to 24 characters, widths
nonbool ints from 1 to 24 that do not exceed columns, columns a nonbool int
from 1 to 24 (default 12).
NOT_CLAIMED: rendering, data queries, refresh, responsive resizing, drag and
drop, user preferences, production readiness.
"""
SCOPE = 'PARTIAL: left-to-right panel placement on a fixed grid, nothing rendered'
NOT_CLAIMED = ('rendering', 'data queries', 'refresh', 'responsive resizing', 'drag and drop',
               'user preferences', 'production readiness')

MAX_PANELS = 30


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def layout_panels(panels, columns=12):
    if type(panels) not in (list, tuple):
        raise TypeError('panels must be a list or tuple')
    if len(panels) > MAX_PANELS:
        raise ValueError('panels must contain at most 30 entries')
    _int(columns, 1, 24, 'columns must be a nonbool integer between 1 and 24')
    titles = set()
    for p in panels:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise ValueError('each panel must be a (title, width) pair')
        title, width = p
        if type(title) is not str or not 1 <= len(title) <= 24:
            raise ValueError('panel titles must be strings of 1 to 24 characters')
        if title in titles:
            raise ValueError('duplicate panel title')
        titles.add(title)
        _int(width, 1, 24, 'width must be a nonbool integer between 1 and 24')
        if width > columns:
            raise ValueError('width must not exceed columns')
    rows, fill, placements = [], [], []
    for title, width in panels:
        if not rows or fill[-1] + width > columns:
            rows.append([])
            fill.append(0)
        placements.append((title, len(rows) - 1, fill[-1]))
        rows[-1].append(title)
        fill[-1] += width
    return {'rows': rows, 'placements': placements, 'row_count': len(rows), 'fill': fill}
