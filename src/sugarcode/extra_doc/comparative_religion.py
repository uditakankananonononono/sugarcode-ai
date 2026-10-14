"""Row 1899, Title: Comparative Religion

compare_rituals(rows): rows are (tradition, ritual, frequency)
triples; tradition and ritual strings of 1 to 16 characters;
frequency a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row count,
for each tradition its modal frequency (the most repeated
frequency, the smallest value on ties), the canonical
traditions (a frequency repeated at least 3 times, sorted
alphabetically), the unrepeated traditions (at least 2 rows
with all frequencies distinct, sorted alphabetically), and the
typical tradition (the largest repeat count, first supplied on
ties).

SCOPE: PARTIAL: ritual comparison over supplied frequencies
NOT_CLAIMED: phenomenology, fieldwork, sacred texts,
anthropology of religion, production readiness.
"""

SCOPE = 'PARTIAL: ritual comparison over supplied frequencies'
NOT_CLAIMED = ('phenomenology', 'fieldwork', 'sacred texts',
               'anthropology of religion', 'production readiness')


def compare_rituals(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (tradition, ritual, frequency) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        tradition, ritual, frequency = row
        if type(tradition) is not str or not 1 <= len(tradition) <= 16:
            raise ValueError(f'row {i}: tradition must be a string of 1 to 16 characters')
        if type(ritual) is not str or not 1 <= len(ritual) <= 16:
            raise ValueError(f'row {i}: ritual must be a string of 1 to 16 characters')
        if type(frequency) is not int or not 1 <= frequency <= 9:
            raise ValueError(f'row {i}: frequency must be a nonbool integer between 1 and 9')
    hist = {}
    for tradition, ritual, frequency in rows:
        if tradition not in hist:
            hist[tradition] = {}
        hist[tradition][frequency] = hist[tradition].get(frequency, 0) + 1
    modes = {}
    for tradition in hist:
        best_value = None
        best_count = 0
        for frequency in sorted(hist[tradition]):
            if hist[tradition][frequency] > best_count:
                best_value = frequency
                best_count = hist[tradition][frequency]
        modes[tradition] = best_value
    canonical = sorted(t for t in hist if max(hist[t].values()) >= 3)
    unrepeated = sorted(t for t in hist if len(hist[t]) >= 2 and max(hist[t].values()) == 1)
    typical = None
    for tradition in hist:
        if typical is None or max(hist[tradition].values()) > max(hist[typical].values()):
            typical = tradition
    return {'total': len(rows),
            'modes': modes,
            'canonical': canonical,
            'unrepeated': unrepeated,
            'typical': typical}
