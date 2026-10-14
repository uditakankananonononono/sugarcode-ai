"""Row607 Performance Testing - Measures speed.

SCOPED local wall-clock nanosecond measurements of a fixed integer sort workload.
No arbitrary callback, network, process, load service or cross-machine benchmark
claim. Timings are noisy; no performance guarantee or universal ranking.
"""
import time
from fractions import Fraction


def measure_sort(values,repetitions):
    """Values exact list1..256 ints+/-1,000,000; repetitions exact int1..32.
    Each repetition copies then sorts once; timings include copying/sorting.
    Return raw durations/min/max/exact mean and result, without global effects.
    """
    if type(values) is not list:
        raise TypeError('exact integer list required')
    if not 1<=len(values)<=256:
        raise ValueError('value count must be 1..256')
    if type(repetitions) is not int:
        raise TypeError('exact nonbool repetition integer required')
    if not 1<=repetitions<=32:
        raise ValueError('repetition count must be 1..32')
    for value in values:
        if type(value) is not int:
            raise TypeError('exact nonbool integer required')
        if not -1000000<=value<=1000000:
            raise ValueError('integer outside declared range')
    durations=[]
    result=None
    for _ in range(repetitions):
        start=time.perf_counter_ns()
        result=sorted(values)
        finish=time.perf_counter_ns()
        duration=finish-start
        if duration<0:
            raise RuntimeError('monotonic clock moved backward')
        durations.append(duration)
    return {'sorted_values':result,'durations_ns':durations,'minimum_ns':min(durations),
            'maximum_ns':max(durations),'mean_ns_fraction':str(Fraction(sum(durations),repetitions)),
            'repetitions':repetitions}
