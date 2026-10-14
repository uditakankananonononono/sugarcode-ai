"""Row 1932, Title: Voice Cloning

split_fade(rows): rows are (sample, voice, gain)
triples; sample and voice strings of 1 to 16
characters; gain a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each voice the
front-minus-back drop (the sum of the first half of
its gain sequence minus the sum of the second half,
any middle gain counting toward the back), the
fading voices (a positive drop, sorted
alphabetically), and the steepest voice (the largest
drop among fading voices, first supplied on ties, or
None when no voice fades).

SCOPE: PARTIAL: split-half gain drop over supplied rows
NOT_CLAIMED: speaker similarity, prosody transfer,
artifact control, consent compliance, production
readiness.
"""

SCOPE = 'PARTIAL: split-half gain drop over supplied rows'
NOT_CLAIMED = ('speaker similarity', 'prosody transfer',
               'artifact control', 'consent compliance',
               'production readiness')


def split_fade(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (sample, voice, gain) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        sample, voice, gain = row
        if type(sample) is not str or not 1 <= len(sample) <= 16:
            raise ValueError(f'row {i}: sample must be a string of 1 to 16 characters')
        if type(voice) is not str or not 1 <= len(voice) <= 16:
            raise ValueError(f'row {i}: voice must be a string of 1 to 16 characters')
        if type(gain) is not int or not 1 <= gain <= 9:
            raise ValueError(f'row {i}: gain must be a nonbool integer between 1 and 9')
    seqs = {}
    for sample, voice, gain in rows:
        if voice not in seqs:
            seqs[voice] = []
        seqs[voice].append(gain)
    drops = {}
    for voice in seqs:
        seq = seqs[voice]
        half = len(seq) // 2
        drops[voice] = sum(seq[:half]) - sum(seq[half:])
    fading = sorted(v for v in drops if drops[v] > 0)
    steepest = None
    for voice in drops:
        if drops[voice] > 0 and (steepest is None or drops[voice] > drops[steepest]):
            steepest = voice
    return {'total': len(rows),
            'drops': drops,
            'fading': fading,
            'steepest': steepest}
