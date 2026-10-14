"""Row 860, Computational Thinking - Thinks algorithmically: binary search trace.

binary_probe takes values, a list or tuple of 1 to 12 nonbool ints from 0 to
99 in strictly ascending order, and target, a nonbool int from 0 to 99.
It runs binary search step by step: the range starts as the whole list, each
probe looks at the middle index (low plus high, halved, rounded down), and the
range then drops the probed index and everything on the wrong side of it.
Returns found (True when the target is in values), index (where it was found,
None when it was not), probes (the indices probed, in order), linear_probes
(how many a left to right scan would need: index plus 1 when found, else the
number of values) and saved (linear_probes minus the number of probes, which
can be negative).
Checks, in this order: values type, values size, each value, ascending order,
target.
NOT_CLAIMED: real computational thinking, algorithm choice, running time on
real inputs, learner skill, production readiness.
"""

SCOPE = 'PARTIAL: traces binary search probes on a supplied sorted list, no thinking is assessed'
NOT_CLAIMED = ('real computational thinking', 'algorithm choice', 'running time on real inputs',
               'learner skill', 'production readiness')


def _small(x):
    return type(x) is int and 0 <= x <= 99


def binary_probe(values, target):
    if type(values) not in (list, tuple):
        raise TypeError('values must be a list or tuple')
    if not 1 <= len(values) <= 12:
        raise ValueError('values must contain 1 to 12 entries')
    for v in values:
        if not _small(v):
            raise ValueError('each value must be a nonbool integer between 0 and 99')
    for i in range(1, len(values)):
        if values[i - 1] >= values[i]:
            raise ValueError('values must be strictly ascending')
    if not _small(target):
        raise ValueError('target must be a nonbool integer between 0 and 99')
    low, high = 0, len(values) - 1
    probes = []
    index = None
    while low <= high:
        mid = (low + high) // 2
        probes.append(mid)
        if values[mid] == target:
            index = mid
            break
        if values[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    linear = len(values) if index is None else index + 1
    return {'found': index is not None, 'index': index, 'probes': probes,
            'linear_probes': linear, 'saved': linear - len(probes)}
