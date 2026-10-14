"""Row 942, Neuroevolution: mutating supplied network topologies.

A neuroevolution step rewires the supplied networks: the 'grow' operator
adds one hidden node, 'prune' removes one, and a network is reported as
viable when its final hidden-node count stays inside the architecture
bound of two to eight.  evolve() folds the records per network in order
and lists which topologies remain viable after all mutations.

Input rows: (network 1-8, operator 'grow'|'prune').  Each network starts
at 3 hidden nodes.  Output:
{'total', 'grow', 'prune', 'final': {network: final count}, 'viable':
sorted names with final count inside 2-8, 'collapsed': sorted names
outside the bound}.  Reported: pruning twice from 3 collapses the
network to 1; growing past 8 collapses it too (six grows from 3 reach
9).
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
OPERATORS = ('grow', 'prune')
START_NODES = 3
MIN_NODES = 2
MAX_NODES = 8

SCOPE = 'PARTIAL: node-count mutation only; no weights or fitness evaluation'
NOT_CLAIMED = (
    'does not evolve connection weights',
    'does not implement NEAT-style speciation or crossover',
    'does not evaluate network fitness on any task',
    'does not mutate activation functions or learning rules',
)


def _check_name(network: Any, row: int, field: str) -> None:
    if not isinstance(network, str) or type(network) is not str:
        raise TypeError(
            f'row {row}: {field} must be str, got {type(network).__name__}')
    if not 1 <= len(network) <= MAX_NAME:
        raise ValueError(f'row {row}: {field} must be 1-8 chars')


def _check_operator(operator: Any, row: int) -> None:
    if not isinstance(operator, str) or type(operator) is not str:
        raise TypeError(
            f'row {row}: operator must be str, got {type(operator).__name__}')
    if operator not in OPERATORS:
        raise ValueError(
            f"row {row}: operator must be one of {OPERATORS}, got {operator!r}")


def evolve(rows: Any) -> dict:
    """Return the topology mutation summary for the supplied networks."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    nodes: dict = {}
    grow = 0
    prune = 0
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (network, operator) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        network, operator = row
        _check_name(network, index, 'network')
        _check_operator(operator, index)
        if operator == 'grow':
            grow += 1
        else:
            prune += 1
        level = nodes.get(network, START_NODES)
        nodes[network] = level + 1 if operator == 'grow' else level - 1
    viable = sorted(
        name for name, count in nodes.items() if MIN_NODES <= count <= MAX_NODES)
    collapsed = sorted(
        name for name, count in nodes.items() if not MIN_NODES <= count <= MAX_NODES)
    return {'total': len(rows), 'grow': grow, 'prune': prune,
            'final': dict(nodes), 'viable': viable, 'collapsed': collapsed}
