"""Row 1888, Title: Sociolinguistics

track_variants(rows): rows are (speaker, variant, frequency)
triples; speaker and variant strings of 1 to 16 characters;
frequency a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row count,
the shifters (speakers whose latest supplied variant differs
from their first, sorted alphabetically), the stable speakers
(every supplied row using one variant, sorted alphabetically),
for each variant the total frequency, and the prestige variant
(the largest total frequency, first supplied on ties).

SCOPE: PARTIAL: variant tracking over supplied frequencies
NOT_CLAIMED: speech communities, social class, register,
accommodation theory, production readiness.
"""

SCOPE = 'PARTIAL: variant tracking over supplied frequencies'
NOT_CLAIMED = ('speech communities', 'social class', 'register',
               'accommodation theory', 'production readiness')


def track_variants(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (speaker, variant, frequency) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        speaker, variant, frequency = row
        if type(speaker) is not str or not 1 <= len(speaker) <= 16:
            raise ValueError(f'row {i}: speaker must be a string of 1 to 16 characters')
        if type(variant) is not str or not 1 <= len(variant) <= 16:
            raise ValueError(f'row {i}: variant must be a string of 1 to 16 characters')
        if type(frequency) is not int or not 1 <= frequency <= 9:
            raise ValueError(f'row {i}: frequency must be a nonbool integer between 1 and 9')
    first = {}
    latest = {}
    variants_of = {}
    total = {}
    for speaker, variant, frequency in rows:
        if speaker not in first:
            first[speaker] = variant
            variants_of[speaker] = {}
        latest[speaker] = variant
        variants_of[speaker][variant] = True
        if variant not in total:
            total[variant] = 0
        total[variant] += frequency
    shifters = sorted(speaker for speaker in first
                      if latest[speaker] != first[speaker])
    stable = sorted(speaker for speaker in variants_of
                    if len(variants_of[speaker]) == 1)
    prestige = None
    for variant in total:
        if prestige is None or total[variant] > total[prestige]:
            prestige = variant
    return {'total': len(rows),
            'shifters': shifters,
            'stable': stable,
            'frequency': total,
            'prestige': prestige}
