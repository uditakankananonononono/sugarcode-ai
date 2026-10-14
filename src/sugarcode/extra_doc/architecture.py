"""Row 1909, Title: Architecture

measure_skyline(rows): rows are (building, style, height)
triples; building and style strings of 1 to 16 characters;
height a nonbool integer between 1 and 9. Caps (checked before
any work): 1 to 60 rows. Reported: the total row count, the
peak (the highest height), the runner-up (the second-highest
distinct height, None when only one distinct height), the
chasers (the buildings at the runner-up height, sorted
alphabetically), for each style the row count, and the
dominant style (the most rows, first supplied on ties).

SCOPE: PARTIAL: skyline measuring over supplied heights
NOT_CLAIMED: structural engineering, urban planning,
preservation, building codes, production readiness.
"""

SCOPE = 'PARTIAL: skyline measuring over supplied heights'
NOT_CLAIMED = ('structural engineering', 'urban planning',
               'preservation', 'building codes', 'production readiness')


def measure_skyline(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (building, style, height) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        building, style, height = row
        if type(building) is not str or not 1 <= len(building) <= 16:
            raise ValueError(f'row {i}: building must be a string of 1 to 16 characters')
        if type(style) is not str or not 1 <= len(style) <= 16:
            raise ValueError(f'row {i}: style must be a string of 1 to 16 characters')
        if type(height) is not int or not 1 <= height <= 9:
            raise ValueError(f'row {i}: height must be a nonbool integer between 1 and 9')
    marks = {}
    styles = {}
    for building, style, height in rows:
        marks[height] = True
        if style not in styles:
            styles[style] = 0
        styles[style] += 1
    vals = sorted(marks, reverse=True)
    peak = vals[0]
    if len(vals) >= 2:
        runner_up = vals[1]
        chasers = sorted({building for building, style, height in rows
                          if height == runner_up})
    else:
        runner_up = None
        chasers = []
    dominant = None
    for style in styles:
        if dominant is None or styles[style] > styles[dominant]:
            dominant = style
    return {'total': len(rows),
            'peak': peak,
            'runner_up': runner_up,
            'chasers': chasers,
            'styles': styles,
            'dominant': dominant}
