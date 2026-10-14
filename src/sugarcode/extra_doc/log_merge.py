"""Row 632, Log Aggregation: merging per-source log streams into one timeline.

streams is a list or tuple of 1 to 8 (source, entries) pairs. entries is a list
or tuple of 0 to 20 (time, message) pairs whose times do not decrease within
the stream. The merged log is ordered by time; entries with equal times keep
the order of their sources in streams, then their order within the stream.
Only the first limit merged entries are returned (limit defaults to 50) and
truncated says whether any were cut. Reported: merged (time, source, message)
triples, the entry count per source and the total before truncation.
Caps (checked before any work): unique source names of 1 to 16 characters,
times nonbool ints from 0 to 1000000, messages strings of 1 to 40 characters,
limit a nonbool int from 1 to 160.
NOT_CLAIMED: parsing real logs, clock skew correction, deduplication, storage,
search, retention, production readiness.
"""
SCOPE = 'PARTIAL: time-ordered merge of supplied log streams, no real logs or storage'
NOT_CLAIMED = ('parsing real logs', 'clock skew correction', 'deduplication', 'storage',
               'search', 'retention', 'production readiness')

MAX_STREAMS = 8
MAX_ENTRIES = 20


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def merge_logs(streams, limit=50):
    if type(streams) not in (list, tuple):
        raise TypeError('streams must be a list or tuple')
    if not 1 <= len(streams) <= MAX_STREAMS:
        raise ValueError('streams must contain between 1 and 8 entries')
    _int(limit, 1, 160, 'limit must be a nonbool integer between 1 and 160')
    names = set()
    for s in streams:
        if type(s) not in (list, tuple) or len(s) != 2:
            raise ValueError('each stream must be a (source, entries) pair')
        source, entries = s
        if type(source) is not str or not 1 <= len(source) <= 16:
            raise ValueError('source names must be strings of 1 to 16 characters')
        if source in names:
            raise ValueError('duplicate source name')
        names.add(source)
        if type(entries) not in (list, tuple):
            raise ValueError('entries must be a list or tuple')
        if len(entries) > MAX_ENTRIES:
            raise ValueError('entries must contain at most 20 items')
        last = 0
        for e in entries:
            if type(e) not in (list, tuple) or len(e) != 2:
                raise ValueError('each entry must be a (time, message) pair')
            t, msg = e
            _int(t, 0, 1000000, 'time must be a nonbool integer between 0 and 1000000')
            if type(msg) is not str or not 1 <= len(msg) <= 40:
                raise ValueError('messages must be strings of 1 to 40 characters')
            if t < last:
                raise ValueError('times must not decrease within a stream')
            last = t
    tagged = [(t, si, ei, source, msg)
              for si, (source, entries) in enumerate(streams)
              for ei, (t, msg) in enumerate(entries)]
    tagged.sort(key=lambda x: (x[0], x[1], x[2]))
    merged = [(t, source, msg) for t, _, _, source, msg in tagged[:limit]]
    return {'merged': merged, 'counts': {source: len(entries) for source, entries in streams},
            'total': len(tagged), 'truncated': len(tagged) > limit}
