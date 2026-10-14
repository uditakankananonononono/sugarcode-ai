"""Row 1925, Title: Multimodal AI

climb_ladders(rows): rows are (stream, encoder, depth)
triples; stream and encoder strings of 1 to 16
characters; depth a nonbool integer between 1 and 9. Caps
(checked before any work): 1 to 60 rows. Reported: the
total row count, for each stream its span (the number of
distinct depths it uses), the ladders (streams whose
distinct depths are consecutive, sorted alphabetically),
and the tallest ladder (the largest span among ladders,
first supplied on ties, or None when no stream is a
ladder).

SCOPE: PARTIAL: ladder climbing over supplied depths
NOT_CLAIMED: encoder design, fusion strategy, training
data, latency, production readiness.
"""

SCOPE = 'PARTIAL: ladder climbing over supplied depths'
NOT_CLAIMED = ('encoder design', 'fusion strategy', 'training data',
               'latency', 'production readiness')


def climb_ladders(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (stream, encoder, depth) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        stream, encoder, depth = row
        if type(stream) is not str or not 1 <= len(stream) <= 16:
            raise ValueError(f'row {i}: stream must be a string of 1 to 16 characters')
        if type(encoder) is not str or not 1 <= len(encoder) <= 16:
            raise ValueError(f'row {i}: encoder must be a string of 1 to 16 characters')
        if type(depth) is not int or not 1 <= depth <= 9:
            raise ValueError(f'row {i}: depth must be a nonbool integer between 1 and 9')
    depths = {}
    for stream, encoder, depth in rows:
        if stream not in depths:
            depths[stream] = {}
        depths[stream][depth] = True
    spans = {}
    ladders = []
    for stream in depths:
        low = min(depths[stream])
        high = max(depths[stream])
        spans[stream] = len(depths[stream])
        if high - low == spans[stream] - 1:
            ladders.append(stream)
    tallest = None
    for stream in ladders:
        if tallest is None or spans[stream] > spans[tallest]:
            tallest = stream
    return {'total': len(rows),
            'spans': spans,
            'ladders': sorted(ladders),
            'tallest': tallest}
