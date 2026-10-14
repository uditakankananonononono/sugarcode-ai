"""Row 1903, Title: Anthropology of Religion

record_rites(rows): rows are (tribe, rite, duration) triples;
tribe and rite strings of 1 to 16 characters; duration a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, the number
of records (rows whose duration beats every earlier row), the
holders (the record-setting rites in record order), the
longest rite (the final record holder), for each tribe the
total duration, and the enduring tribe (the largest total,
first supplied on ties).

SCOPE: PARTIAL: rite recording over supplied durations
NOT_CLAIMED: participant observation, cultural relativism,
kinship systems, fieldwork ethics, production readiness.
"""

SCOPE = 'PARTIAL: rite recording over supplied durations'
NOT_CLAIMED = ('participant observation', 'cultural relativism',
               'kinship systems', 'fieldwork ethics',
               'production readiness')


def record_rites(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (tribe, rite, duration) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        tribe, rite, duration = row
        if type(tribe) is not str or not 1 <= len(tribe) <= 16:
            raise ValueError(f'row {i}: tribe must be a string of 1 to 16 characters')
        if type(rite) is not str or not 1 <= len(rite) <= 16:
            raise ValueError(f'row {i}: rite must be a string of 1 to 16 characters')
        if type(duration) is not int or not 1 <= duration <= 9:
            raise ValueError(f'row {i}: duration must be a nonbool integer between 1 and 9')
    records = 0
    holders = []
    best = 0
    totals = {}
    for tribe, rite, duration in rows:
        if duration > best:
            records += 1
            holders.append(rite)
            best = duration
        if tribe not in totals:
            totals[tribe] = 0
        totals[tribe] += duration
    enduring = None
    for tribe in totals:
        if enduring is None or totals[tribe] > totals[enduring]:
            enduring = tribe
    return {'total': len(rows),
            'records': records,
            'holders': holders,
            'longest': holders[-1],
            'totals': totals,
            'enduring': enduring}
