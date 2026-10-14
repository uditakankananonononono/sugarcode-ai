"""Row 1892, Title: Comparative Linguistics

match_cognates(rows): rows are (word, language, score) triples;
word and language strings of 1 to 16 characters; score a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to
60 rows. Reported: the total row count, for each word the
number of distinct scores it received, the uniform words
(exactly one distinct score, sorted alphabetically), the varied
words (at least 3 distinct scores, sorted alphabetically), for
each word the total score, and the firmest word (the largest
total score, first supplied on ties).

SCOPE: PARTIAL: cognate matching over supplied scores
NOT_CLAIMED: genetic relatedness, proto-languages, borrowing
detection, regular correspondence, production readiness.
"""

SCOPE = 'PARTIAL: cognate matching over supplied scores'
NOT_CLAIMED = ('genetic relatedness', 'proto-languages',
               'borrowing detection', 'regular correspondence',
               'production readiness')


def match_cognates(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (word, language, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        word, language, score = row
        if type(word) is not str or not 1 <= len(word) <= 16:
            raise ValueError(f'row {i}: word must be a string of 1 to 16 characters')
        if type(language) is not str or not 1 <= len(language) <= 16:
            raise ValueError(f'row {i}: language must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    marks = {}
    strength = {}
    for word, language, score in rows:
        if word not in marks:
            marks[word] = {}
            strength[word] = 0
        marks[word][score] = True
        strength[word] += score
    distinct = {}
    for word in marks:
        distinct[word] = len(marks[word])
    uniform = sorted(word for word in distinct if distinct[word] == 1)
    varied = sorted(word for word in distinct if distinct[word] >= 3)
    firmest = None
    for word in strength:
        if firmest is None or strength[word] > strength[firmest]:
            firmest = word
    return {'total': len(rows),
            'distinct': distinct,
            'uniform': uniform,
            'varied': varied,
            'strength': strength,
            'firmest': firmest}
