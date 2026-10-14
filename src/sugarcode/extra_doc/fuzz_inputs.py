"""Row 602, Fuzzing (bounded scope: one exact step of a fuzzer): a repeatable stream of pseudo-random test inputs.

fuzz_inputs(seed, count, low, high) runs a fixed 32-bit linear congruential generator from the state `seed`:
    state = (1664525 * state + 1013904223) mod 2**32        (the first output uses the state after one step)
and turns each state into an integer from low to high (both included) as low + (state >> 8) mod (high - low + 1).
The same seed always gives the same inputs, and a longer run starts with the shorter run. It returns:
  values       the `count` integers;
  final_state  the generator state after the last step, so a run can be continued by passing it as the next seed.
The small modulo bias of this mapping is part of the definition, not a flaw to correct.
Caps: seed is a nonbool int from 0 to 4294967295; count from 1 to 1000; low and high nonbool ints from -1000000 to
1000000 with low not above high.
Order of checks: seed, count, low, high (type, then range, each in that order), then low against high, and only then
any generation.

NOT_CLAIMED: this makes inputs only. It does not run a program under test, measure coverage, minimise a failing
input, detect a crash, or say anything about the quality of the randomness or whether it finds bugs. It is not secure
randomness. No clinical or wet-lab claim.
"""
A = 1664525
C = 1013904223
M = 2 ** 32


def _int(v, what, low, high):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')
    if not low <= v <= high:
        raise ValueError(what + ' must be between %d and %d' % (low, high))
    return v


def fuzz_inputs(seed, count, low, high):
    s = _int(seed, 'seed', 0, M - 1)
    n = _int(count, 'count', 1, 1000)
    lo = _int(low, 'low', -1000000, 1000000)
    hi = _int(high, 'high', -1000000, 1000000)
    if lo > hi:
        raise ValueError('low must not exceed high')
    span = hi - lo + 1
    out = []
    for _ in range(n):
        s = (A * s + C) % M
        out.append(lo + (s >> 8) % span)
    return {'values': out, 'final_state': s}
