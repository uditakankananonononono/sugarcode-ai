"""Row 1876, Title: Psychoanalytic Criticism

analyze_drives(rows): rows are (text, drive, intensity) triples;
text and drive strings of 1 to 16 characters; intensity a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to 60
rows. Reported: the total row count, for each drive the number of
appearances, for each drive the total intensity, the most frequent
drive (the most appearances, first supplied on ties), the rarest
drive (the fewest appearances, first supplied on ties), and the
drives appearing exactly once, sorted alphabetically.

SCOPE: PARTIAL: drive tallying over supplied readings
NOT_CLAIMED: the unconscious, repression mechanics, clinical
validity, Freudian orthodoxy, production readiness.
"""

SCOPE = 'PARTIAL: drive tallying over supplied readings'
NOT_CLAIMED = ('the unconscious', 'repression mechanics',
               'clinical validity', 'Freudian orthodoxy',
               'production readiness')


def analyze_drives(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (text, drive, intensity) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        text, drive, intensity = row
        if type(text) is not str or not 1 <= len(text) <= 16:
            raise ValueError(f'row {i}: text must be a string of 1 to 16 characters')
        if type(drive) is not str or not 1 <= len(drive) <= 16:
            raise ValueError(f'row {i}: drive must be a string of 1 to 16 characters')
        if type(intensity) is not int or not 1 <= intensity <= 9:
            raise ValueError(f'row {i}: intensity must be a nonbool integer between 1 and 9')
    appearances = {}
    energy = {}
    for text, drive, intensity in rows:
        if drive not in appearances:
            appearances[drive] = 0
        appearances[drive] += 1
        if drive not in energy:
            energy[drive] = 0
        energy[drive] += intensity
    most_frequent = None
    for drive in appearances:
        if most_frequent is None or appearances[drive] > appearances[most_frequent]:
            most_frequent = drive
    rarest = None
    for drive in appearances:
        if rarest is None or appearances[drive] < appearances[rarest]:
            rarest = drive
    fleeting = sorted(drive for drive in appearances if appearances[drive] == 1)
    return {'total': len(rows),
            'appearances': appearances,
            'energy': energy,
            'most_frequent': most_frequent,
            'rarest': rarest,
            'fleeting': fleeting}
