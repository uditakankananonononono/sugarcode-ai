"""Row 1893, Title: Computational Linguistics

score_parses(rows): rows are (parser, sentence, score) triples;
parser and sentence strings of 1 to 16 characters; score a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
parser the number of sentences it solved at score at least 7,
for each parser the number of sentences it failed at score at
most 2, the sharp parsers (no failures, sorted alphabetically),
the blunt parsers (no solves, sorted alphabetically), and the
best parser (the most solves, first supplied on ties; ties
broken by fewer failures, then by first supplied).

SCOPE: PARTIAL: parse scoring over supplied results
NOT_CLAIMED: grammar induction, parsing algorithms, treebank
validity, language understanding, production readiness.
"""

SCOPE = 'PARTIAL: parse scoring over supplied results'
NOT_CLAIMED = ('grammar induction', 'parsing algorithms',
               'treebank validity', 'language understanding',
               'production readiness')


def score_parses(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (parser, sentence, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        parser, sentence, score = row
        if type(parser) is not str or not 1 <= len(parser) <= 16:
            raise ValueError(f'row {i}: parser must be a string of 1 to 16 characters')
        if type(sentence) is not str or not 1 <= len(sentence) <= 16:
            raise ValueError(f'row {i}: sentence must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    solved = {}
    failed = {}
    for parser, sentence, score in rows:
        if parser not in solved:
            solved[parser] = {}
            failed[parser] = {}
        if score >= 7:
            solved[parser][sentence] = True
        if score <= 2:
            failed[parser][sentence] = True
    solves = {}
    failures = {}
    for parser in solved:
        solves[parser] = len(solved[parser])
        failures[parser] = len(failed[parser])
    sharp = sorted(parser for parser in failures if failures[parser] == 0)
    blunt = sorted(parser for parser in solves if solves[parser] == 0)
    best = None
    for parser in solves:
        if best is None:
            best = parser
        elif (solves[parser] > solves[best] or
              (solves[parser] == solves[best] and
               failures[parser] < failures[best])):
            best = parser
    return {'total': len(rows),
            'solves': solves,
            'failures': failures,
            'sharp': sharp,
            'blunt': blunt,
            'best': best}
