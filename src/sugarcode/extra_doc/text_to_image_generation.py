"""Row 1927, Title: Text-to-Image Generation

reduce_steps(rows): rows are (prompt, sampler, steps)
triples; prompt and sampler strings of 1 to 16
characters; steps a nonbool integer between 1 and 9. Caps
(checked before any work): 1 to 60 rows. Reported: the
total row count, for each sampler the greatest common
divisor of its steps, the aligned samplers (a divisor
above 1, sorted alphabetically), and the tightest sampler
(the largest divisor, first supplied on ties).

SCOPE: PARTIAL: step reducing over supplied counts
NOT_CLAIMED: diffusion scheduling, sampler theory,
prompt design, image safety, production readiness.
"""

SCOPE = 'PARTIAL: step reducing over supplied counts'
NOT_CLAIMED = ('diffusion scheduling', 'sampler theory',
               'prompt design', 'image safety', 'production readiness')


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def reduce_steps(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (prompt, sampler, steps) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        prompt, sampler, steps = row
        if type(prompt) is not str or not 1 <= len(prompt) <= 16:
            raise ValueError(f'row {i}: prompt must be a string of 1 to 16 characters')
        if type(sampler) is not str or not 1 <= len(sampler) <= 16:
            raise ValueError(f'row {i}: sampler must be a string of 1 to 16 characters')
        if type(steps) is not int or not 1 <= steps <= 9:
            raise ValueError(f'row {i}: steps must be a nonbool integer between 1 and 9')
    divisors = {}
    for prompt, sampler, steps in rows:
        if sampler not in divisors:
            divisors[sampler] = steps
        else:
            divisors[sampler] = _gcd(divisors[sampler], steps)
    aligned = sorted(s for s in divisors if divisors[s] > 1)
    tightest = None
    for sampler in divisors:
        if tightest is None or divisors[sampler] > divisors[tightest]:
            tightest = sampler
    return {'total': len(rows),
            'divisors': divisors,
            'aligned': aligned,
            'tightest': tightest}
