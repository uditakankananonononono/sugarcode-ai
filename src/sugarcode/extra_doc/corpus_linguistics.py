"""Row 1894, Title: Corpus Linguistics

analyze_corpus(rows): rows are (token, genre, frequency) triples;
token and genre strings of 1 to 16 characters; frequency a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
genre the total frequency, the leader (the first genre whose
running total reaches 20, None when none does), the
frontrunners (genres whose final total is at least 20, sorted
alphabetically), and the richest token (the largest peak
frequency, first supplied on ties).

SCOPE: PARTIAL: corpus tallying over supplied frequencies
NOT_CLAIMED: tokenization, concordance generation, part-of-speech
tagging, statistical significance, production readiness.
"""

SCOPE = 'PARTIAL: corpus tallying over supplied frequencies'
NOT_CLAIMED = ('tokenization', 'concordance generation',
               'part-of-speech tagging', 'statistical significance',
               'production readiness')


def analyze_corpus(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (token, genre, frequency) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        token, genre, frequency = row
        if type(token) is not str or not 1 <= len(token) <= 16:
            raise ValueError(f'row {i}: token must be a string of 1 to 16 characters')
        if type(genre) is not str or not 1 <= len(genre) <= 16:
            raise ValueError(f'row {i}: genre must be a string of 1 to 16 characters')
        if type(frequency) is not int or not 1 <= frequency <= 9:
            raise ValueError(f'row {i}: frequency must be a nonbool integer between 1 and 9')
    totals = {}
    best = {}
    leader = None
    for token, genre, frequency in rows:
        if genre not in totals:
            totals[genre] = 0
        totals[genre] += frequency
        if leader is None and totals[genre] >= 20:
            leader = genre
        if token not in best or frequency > best[token]:
            best[token] = frequency
    frontrunners = sorted(g for g in totals if totals[g] >= 20)
    richest = None
    for token in best:
        if richest is None or best[token] > best[richest]:
            richest = token
    return {'total': len(rows),
            'totals': totals,
            'leader': leader,
            'frontrunners': frontrunners,
            'richest': richest}
