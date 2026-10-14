"""Row 938, Genetic Programming: evolving supplied programs.

Evolves programs. Each row pairs a program name of 1 to 8
characters with a fitness, an integer from 0 to 10.
Reported: the row total, the distinct program count, the
fitness sum, and evolved - the sorted programs whose latest
supplied fitness beats their first supplied fitness. Caps
(checked before any work): 0 to 100 rows.
NOT_CLAIMED: real genetic programming, evolutionary
computation, program synthesis, optimization, code generation,
production readiness.
"""
SCOPE = 'PARTIAL: fitness comparison over supplied rows, no real evolution'
NOT_CLAIMED = ('real genetic programming', 'evolutionary computation',
               'program synthesis', 'optimization', 'code generation',
               'production readiness')

MAX_ROWS = 100
MAX_NAME = 8
MAX_FITNESS = 10


def evolve(programs):
    """Compare first and latest fitness over named programs."""
    if type(programs) not in (list, tuple):
        raise TypeError('programs must be a list or tuple')
    if len(programs) > MAX_ROWS:
        raise ValueError('programs must contain at most 100 entries')
    rows = []
    for row in programs:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each row must be a (program, fitness) row')
        program, fitness = row
        if type(program) is not str or not 1 <= len(program) <= MAX_NAME:
            raise ValueError('program must be a string of 1 to 8 characters')
        if type(fitness) is not int or not 0 <= fitness <= MAX_FITNESS:
            raise ValueError('fitness must be an integer from 0 to 10')
        rows.append((program, fitness))
    firsts = {}
    lasts = {}
    for program, fitness in rows:
        if program not in firsts:
            firsts[program] = fitness
        lasts[program] = fitness
    evolved = sorted(p for p in lasts if lasts[p] > firsts[p])
    return {'total': len(rows), 'programs': len(lasts),
            'fitness': sum(fitness for program, fitness in rows),
            'evolved': evolved}
