"""Row 1003, Connectomics: reading a node's shared strand.

A node holds together when its strengths share a common factor,
not when they merely cluster.  map() folds every strength a node
receives into their greatest common divisor, then reports the
nodes reduced to a single strand.

Input rows: (node 1-8, strength int 0-10).  A unit is a node
whose greatest common divisor is 1.
Output: {'total', 'cores': {node: greatest common divisor of
its strengths}, 'units': sorted nodes reduced to 1}.
Reported: strengths 2, 4 reduce to 2; 3, 5 reduce to 1 and
read as a unit; 4, 6 reduce to 2; 0, 5 reduce to 5;
0, 0 reduce to 0; a lone strength reduces to itself;
6, 9, 3 reduce to 3; 6, 10, 3 reduce to 1 and read as a unit.
"""

import math
from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_STRENGTH = 0
MAX_STRENGTH = 10

SCOPE = 'PARTIAL: connection bookkeeping only; no graph topology modeled'
NOT_CLAIMED = (
    'does not model direction of connections',
    'does not weight strengths by record order',
    'does not measure distance between nodes',
    'does not compare nodes against each other',
)


def _check_name(node: Any, row: int) -> None:
    if not isinstance(node, str) or type(node) is not str:
        raise TypeError(
            f'row {row}: node must be str, got {type(node).__name__}')
    if not 1 <= len(node) <= MAX_NAME:
        raise ValueError(f'row {row}: node must be 1-8 chars')


def _check_strength(strength: Any, row: int) -> None:
    if type(strength) is not int:
        raise TypeError(
            f'row {row}: strength must be int, got {type(strength).__name__}')
    if not MIN_STRENGTH <= strength <= MAX_STRENGTH:
        raise ValueError(
            f'row {row}: strength must be {MIN_STRENGTH}-{MAX_STRENGTH}, got {strength}')


def map(rows: Any) -> dict:
    """Return the common-divisor summary for the supplied strength records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (node, strength) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        node, strength = row
        _check_name(node, index)
        _check_strength(strength, index)
        values.setdefault(node, []).append(strength)
    cores = {}
    for node, vals in values.items():
        core = 0
        for strength in vals:
            core = math.gcd(core, strength)
        cores[node] = core
    units = sorted(node for node, core in cores.items() if core == 1)
    return {'total': len(rows), 'cores': cores, 'units': units}
