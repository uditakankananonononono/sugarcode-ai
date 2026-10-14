"""Row 958, Mechanical Metamaterials (PARTIAL: one exact structure rule).

Each supplied lattice is checked with two structure bars:
- 'coarse' when unit_cells < 100
- 'uniform_only' when gradients < 1

NOT_CLAIMED: this checks supplied lattice numbers against two structure bars. It does not say any property emerges, that 100 cells or 1 gradient are the right bars, or that any lattice bears load. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_lattices(lattices):
    if type(lattices) is not list:
        raise TypeError('lattices must be an exact list')
    if len(lattices) > 40:
        raise ValueError('lattice count must be at most 40')
    problems = []
    for i, item in enumerate(lattices):
        if type(item) is not tuple:
            raise TypeError('each lattice must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each lattice must have 3 items')
        name, unit_cells, gradients = item
        if type(name) is not str:
            raise TypeError('lattice must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('lattice must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('unit_cells', unit_cells, 1000000), ('gradients', gradients, 100)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if unit_cells < 100:
            problems.append((i, 'coarse'))
        if gradients < 1:
            problems.append((i, 'uniform_only'))
    return {'problems': sorted(problems),
            'lattices': sorted({x[0] for x in lattices}),
            'total': len(lattices)}
