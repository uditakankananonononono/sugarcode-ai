"""Row 1928, Title: Text-to-Video Generation

mirror_frames(rows): rows are (clip, engine, frames)
triples; clip and engine strings of 1 to 16 characters;
frames a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row
count, for each engine its frame sequence length, the
mirrored engines (whose own frame sequence reads the
same backwards, sorted alphabetically), and the longest
mirror (the most rows among mirrored engines, first
supplied on ties, or None when no engine mirrors).

SCOPE: PARTIAL: frame mirroring over supplied counts
NOT_CLAIMED: temporal coherence, motion modeling,
rendering cost, content policy, production readiness.
"""

SCOPE = 'PARTIAL: frame mirroring over supplied counts'
NOT_CLAIMED = ('temporal coherence', 'motion modeling',
               'rendering cost', 'content policy',
               'production readiness')


def mirror_frames(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (clip, engine, frames) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        clip, engine, frames = row
        if type(clip) is not str or not 1 <= len(clip) <= 16:
            raise ValueError(f'row {i}: clip must be a string of 1 to 16 characters')
        if type(engine) is not str or not 1 <= len(engine) <= 16:
            raise ValueError(f'row {i}: engine must be a string of 1 to 16 characters')
        if type(frames) is not int or not 1 <= frames <= 9:
            raise ValueError(f'row {i}: frames must be a nonbool integer between 1 and 9')
    seqs = {}
    for clip, engine, frames in rows:
        if engine not in seqs:
            seqs[engine] = []
        seqs[engine].append(frames)
    lengths = {}
    mirrored = []
    for engine in seqs:
        seq = seqs[engine]
        lengths[engine] = len(seq)
        if seq == seq[::-1]:
            mirrored.append(engine)
    longest = None
    for engine in mirrored:
        if longest is None or lengths[engine] > lengths[longest]:
            longest = engine
    return {'total': len(rows),
            'lengths': lengths,
            'mirrored': sorted(mirrored),
            'longest': longest}
