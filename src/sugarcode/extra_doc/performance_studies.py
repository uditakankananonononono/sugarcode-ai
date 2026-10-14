"""Row 1914, Title: Performance Studies

break_records(rows): rows are (act, troupe, energy) triples;
act and troupe strings of 1 to 16 characters; energy a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for
each troupe its breaks (rows whose energy strictly tops
every earlier row of that same troupe; a first row never
counts), the quiet troupes (no breaks, sorted
alphabetically), and the chaser (the most breaks, first
supplied on ties).

SCOPE: PARTIAL: record breaking over supplied energies
NOT_CLAIMED: acting theory, stagecraft, direction,
casting, production readiness.
"""

SCOPE = 'PARTIAL: record breaking over supplied energies'
NOT_CLAIMED = ('acting theory', 'stagecraft', 'direction',
               'casting', 'production readiness')


def break_records(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (act, troupe, energy) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        act, troupe, energy = row
        if type(act) is not str or not 1 <= len(act) <= 16:
            raise ValueError(f'row {i}: act must be a string of 1 to 16 characters')
        if type(troupe) is not str or not 1 <= len(troupe) <= 16:
            raise ValueError(f'row {i}: troupe must be a string of 1 to 16 characters')
        if type(energy) is not int or not 1 <= energy <= 9:
            raise ValueError(f'row {i}: energy must be a nonbool integer between 1 and 9')
    peaks = {}
    breaks = {}
    for act, troupe, energy in rows:
        if troupe not in peaks:
            peaks[troupe] = energy
            breaks[troupe] = 0
        elif energy > peaks[troupe]:
            peaks[troupe] = energy
            breaks[troupe] += 1
    quiet = sorted(t for t in breaks if breaks[t] == 0)
    chaser = None
    for troupe in breaks:
        if chaser is None or breaks[troupe] > breaks[chaser]:
            chaser = troupe
    return {'total': len(rows),
            'breaks': breaks,
            'quiet': quiet,
            'chaser': chaser}
