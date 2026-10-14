"""Row 764, Empathy: mirroring supplied emotional signals.

Feels with others by matching. Each row pairs a person name of 1 to
8 characters with an emotion of 'joy', 'sadness', 'anger', or 'fear'.
Reported: the four emotion counts, the mirrored count - adjacent
rows sharing the same emotion - and the row total. Caps (checked
before any work): 0 to 100 rows.
NOT_CLAIMED: real feelings, empathy training, clinical use, facial
recognition, sentiment analysis, counseling, production readiness.
"""
SCOPE = 'PARTIAL: signal matching over supplied rows, no real empathy'
NOT_CLAIMED = ('real feelings', 'empathy training', 'clinical use',
               'facial recognition', 'sentiment analysis', 'counseling',
               'production readiness')

MAX_ROWS = 100
MAX_PERSON = 8
EMOTIONS = ('joy', 'sadness', 'anger', 'fear')


def resonate(signals):
    if type(signals) not in (list, tuple):
        raise TypeError('signals must be a list or tuple')
    if len(signals) > MAX_ROWS:
        raise ValueError('signals must contain at most 100 rows')
    rows = []
    for row in signals:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each signal must be a (person, emotion) row')
        person, emotion = row
        if type(person) is not str or not 1 <= len(person) <= MAX_PERSON:
            raise ValueError('person must be a string of 1 to 8 characters')
        if type(emotion) is not str or emotion not in EMOTIONS:
            raise ValueError('emotion must be joy, sadness, anger, or fear')
        rows.append((person, emotion))
    counts = {'joy': 0, 'sadness': 0, 'anger': 0, 'fear': 0}
    for person, emotion in rows:
        counts[emotion] += 1
    mirrored = 0
    for index in range(1, len(rows)):
        if rows[index][1] == rows[index - 1][1]:
            mirrored += 1
    return {'joy': counts['joy'], 'sadness': counts['sadness'],
            'anger': counts['anger'], 'fear': counts['fear'],
            'mirrored': mirrored, 'total': len(rows)}
