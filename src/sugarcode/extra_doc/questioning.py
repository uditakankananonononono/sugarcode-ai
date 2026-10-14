"""Row 740, Questioning: classifying supplied questions by first word.

Elicits information by shape. Each question is a string of 1 to 80
characters. Its first word is the first whitespace-delimited token,
lowercased. A question is open when its first word is one of what,
why, how, when, where, who, which, or whose; closed when it is one of
is, are, was, were, do, does, did, can, could, will, would, shall,
should, have, has, may, might, or must; and other otherwise,
including questions with no words at all.
Reported: one label per question in order and the three counts.
Caps (checked before any work): 0 to 100 questions.
NOT_CLAIMED: language parsing, intent detection, dialogue management,
pedagogy, question generation, grammar beyond the first word,
production readiness.
"""
SCOPE = 'PARTIAL: first-word question classification over supplied strings, no real language parsing'
NOT_CLAIMED = ('language parsing', 'intent detection', 'dialogue management',
               'pedagogy', 'question generation', 'grammar beyond the first word',
               'production readiness')

MAX_QUESTIONS = 100
MAX_QUESTION = 80
OPENERS = ('what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose')
CLOSERS = ('is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'will',
           'would', 'shall', 'should', 'have', 'has', 'may', 'might', 'must')


def classify(questions):
    if type(questions) not in (list, tuple):
        raise TypeError('questions must be a list or tuple')
    if len(questions) > MAX_QUESTIONS:
        raise ValueError('questions must contain at most 100 rows')
    for question in questions:
        if type(question) is not str or not 1 <= len(question) <= MAX_QUESTION:
            raise ValueError('questions must be strings of 1 to 80 characters')
    results = []
    for question in questions:
        tokens = question.split()
        first = tokens[0].lower() if tokens else ''
        if first in OPENERS:
            results.append('open')
        elif first in CLOSERS:
            results.append('closed')
        else:
            results.append('other')
    return {'results': results,
            'open': sum(1 for r in results if r == 'open'),
            'closed': sum(1 for r in results if r == 'closed'),
            'other': sum(1 for r in results if r == 'other')}
