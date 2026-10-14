"""Row 1916, Title: Theater Studies

stage_peaks(rows): rows are (play, house, seats) triples;
play and house strings of 1 to 16 characters; seats a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Rows are counted from 1. Reported:
the total row count, for each house the row of its first
peak (the earliest row reaching its best seats), the
earliest house (the smallest peak row, first supplied on
ties), and the closers (houses peaking on their own final
row, sorted alphabetically).

SCOPE: PARTIAL: peak staging over supplied seats
NOT_CLAIMED: dramaturgy, set design, ticketing,
casting, production readiness.
"""

SCOPE = 'PARTIAL: peak staging over supplied seats'
NOT_CLAIMED = ('dramaturgy', 'set design', 'ticketing',
               'casting', 'production readiness')


def stage_peaks(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (play, house, seats) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        play, house, seats = row
        if type(play) is not str or not 1 <= len(play) <= 16:
            raise ValueError(f'row {i}: play must be a string of 1 to 16 characters')
        if type(house) is not str or not 1 <= len(house) <= 16:
            raise ValueError(f'row {i}: house must be a string of 1 to 16 characters')
        if type(seats) is not int or not 1 <= seats <= 9:
            raise ValueError(f'row {i}: seats must be a nonbool integer between 1 and 9')
    peaks = {}
    peak_rows = {}
    last_rows = {}
    for pos, (play, house, seats) in enumerate(rows, 1):
        if house not in peaks:
            peaks[house] = seats
            peak_rows[house] = pos
        elif seats > peaks[house]:
            peaks[house] = seats
            peak_rows[house] = pos
        last_rows[house] = pos
    earliest = None
    for house in peak_rows:
        if earliest is None or peak_rows[house] < peak_rows[earliest]:
            earliest = house
    closers = sorted(h for h in peak_rows if peak_rows[h] == last_rows[h])
    return {'total': len(rows),
            'peak_rows': peak_rows,
            'earliest': earliest,
            'closers': closers}
