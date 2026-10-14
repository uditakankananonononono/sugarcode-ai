"""Row 1889, Title: Psycholinguistics

measure_priming(rows): rows are (subject, stimulus, reaction)
triples; subject and stimulus strings of 1 to 16 characters;
reaction a nonbool integer between 1 and 9. Caps (checked before
any work): 1 to 60 rows. Reported: the total row count, for each
subject the peak reaction to any stimulus, for each subject the
sorted stimuli priming them (a peak reaction of at least 8 to
that stimulus), the numb subjects (primed by nothing, sorted
alphabetically), and the most sensitive subject (the most
primed stimuli, first supplied on ties, or None when no
subject is primed).

SCOPE: PARTIAL: priming measurement over supplied reactions
NOT_CLAIMED: lexical access, reaction-time validity, language
acquisition, the mental lexicon, production readiness.
"""

SCOPE = 'PARTIAL: priming measurement over supplied reactions'
NOT_CLAIMED = ('lexical access', 'reaction-time validity',
               'language acquisition', 'the mental lexicon',
               'production readiness')


def measure_priming(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (subject, stimulus, reaction) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        subject, stimulus, reaction = row
        if type(subject) is not str or not 1 <= len(subject) <= 16:
            raise ValueError(f'row {i}: subject must be a string of 1 to 16 characters')
        if type(stimulus) is not str or not 1 <= len(stimulus) <= 16:
            raise ValueError(f'row {i}: stimulus must be a string of 1 to 16 characters')
        if type(reaction) is not int or not 1 <= reaction <= 9:
            raise ValueError(f'row {i}: reaction must be a nonbool integer between 1 and 9')
    per_pair = {}
    order = {}
    for subject, stimulus, reaction in rows:
        if subject not in per_pair:
            per_pair[subject] = {}
            order[subject] = True
        if stimulus not in per_pair[subject]:
            per_pair[subject][stimulus] = reaction
        elif reaction > per_pair[subject][stimulus]:
            per_pair[subject][stimulus] = reaction
    peak = {}
    primed = {}
    numb = []
    for subject in per_pair:
        best = None
        hits = []
        for stimulus in per_pair[subject]:
            if best is None or per_pair[subject][stimulus] > best:
                best = per_pair[subject][stimulus]
            if per_pair[subject][stimulus] >= 8:
                hits.append(stimulus)
        peak[subject] = best
        if hits:
            primed[subject] = sorted(hits)
        else:
            numb.append(subject)
    sensitive = None
    for subject in primed:
        if sensitive is None or len(primed[subject]) > len(primed[sensitive]):
            sensitive = subject
    return {'total': len(rows),
            'peak': peak,
            'primed': primed,
            'numb': sorted(numb),
            'sensitive': sensitive}
