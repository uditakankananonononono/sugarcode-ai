"""Row 1902, Title: Psychology of Religion

probe_subjects(rows): rows are (subject, experience, intensity)
triples; subject and experience strings of 1 to 16 characters;
intensity a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row count,
for each subject its gap (the highest distinct intensity minus
the second-highest distinct intensity, 0 when only one
distinct intensity), the spiked subjects (gap at least 5,
sorted alphabetically), the level subjects (at least 2 rows
with a gap of at most 1, sorted alphabetically), and the
sharpest subject (the largest gap, first supplied on ties).

SCOPE: PARTIAL: subject probing over supplied intensities
NOT_CLAIMED: clinical diagnosis, mystical experience,
attachment theory, measurement validity, production readiness.
"""

SCOPE = 'PARTIAL: subject probing over supplied intensities'
NOT_CLAIMED = ('clinical diagnosis', 'mystical experience',
               'attachment theory', 'measurement validity',
               'production readiness')


def probe_subjects(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (subject, experience, intensity) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        subject, experience, intensity = row
        if type(subject) is not str or not 1 <= len(subject) <= 16:
            raise ValueError(f'row {i}: subject must be a string of 1 to 16 characters')
        if type(experience) is not str or not 1 <= len(experience) <= 16:
            raise ValueError(f'row {i}: experience must be a string of 1 to 16 characters')
        if type(intensity) is not int or not 1 <= intensity <= 9:
            raise ValueError(f'row {i}: intensity must be a nonbool integer between 1 and 9')
    marks = {}
    counts = {}
    for subject, experience, intensity in rows:
        if subject not in marks:
            marks[subject] = {}
            counts[subject] = 0
        marks[subject][intensity] = True
        counts[subject] += 1
    gaps = {}
    for subject in marks:
        vals = sorted(marks[subject], reverse=True)
        if len(vals) >= 2:
            gaps[subject] = vals[0] - vals[1]
        else:
            gaps[subject] = 0
    spiked = sorted(s for s in gaps if gaps[s] >= 5)
    level = sorted(s for s in gaps if counts[s] >= 2 and gaps[s] <= 1)
    sharpest = None
    for subject in gaps:
        if sharpest is None or gaps[subject] > gaps[sharpest]:
            sharpest = subject
    return {'total': len(rows),
            'gaps': gaps,
            'spiked': spiked,
            'level': level,
            'sharpest': sharpest}
