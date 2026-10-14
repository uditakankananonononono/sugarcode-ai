"""Row 1896, Title: Interpretation Studies

gauge_clarity(rows): rows are (text, reader, clarity) triples;
text and reader strings of 1 to 16 characters; clarity a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
text the median clarity (the lower middle of its sorted
clarity values), the lucid texts (median at least 7, sorted
alphabetically), the murky texts (median at most 3, sorted
alphabetically), and the clearest text (the highest median,
first supplied on ties).

SCOPE: PARTIAL: clarity gauging over supplied readings
NOT_CLAIMED: hermeneutic method, authorial intent, reader
psychology, meaning determination, production readiness.
"""

SCOPE = 'PARTIAL: clarity gauging over supplied readings'
NOT_CLAIMED = ('hermeneutic method', 'authorial intent',
               'reader psychology', 'meaning determination',
               'production readiness')


def gauge_clarity(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (text, reader, clarity) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        text, reader, clarity = row
        if type(text) is not str or not 1 <= len(text) <= 16:
            raise ValueError(f'row {i}: text must be a string of 1 to 16 characters')
        if type(reader) is not str or not 1 <= len(reader) <= 16:
            raise ValueError(f'row {i}: reader must be a string of 1 to 16 characters')
        if type(clarity) is not int or not 1 <= clarity <= 9:
            raise ValueError(f'row {i}: clarity must be a nonbool integer between 1 and 9')
    readings = {}
    for text, reader, clarity in rows:
        if text not in readings:
            readings[text] = []
        readings[text].append(clarity)
    medians = {}
    for text in readings:
        vals = sorted(readings[text])
        medians[text] = vals[(len(vals) - 1) // 2]
    lucid = sorted(t for t in medians if medians[t] >= 7)
    murky = sorted(t for t in medians if medians[t] <= 3)
    clearest = None
    for text in medians:
        if clearest is None or medians[text] > medians[clearest]:
            clearest = text
    return {'total': len(rows),
            'medians': medians,
            'lucid': lucid,
            'murky': murky,
            'clearest': clearest}
