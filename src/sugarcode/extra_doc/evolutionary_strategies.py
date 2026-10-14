"""Row 941, Evolutionary Strategies: mutating supplied strategies.

An evolutionary strategy perturbs each surviving parent with a mutation
operator drawn from the supplied record.  mutate() walks the records in
order, applying 'scale' by halving each parent's score and 'shift' by
adding one, and reports every strategy whose final mutated score stays
above zero along with those ending at zero or below.

Input rows: (strategy 1-8, operator 'scale'|'shift').  Each strategy
starts at score 4.  Output:
{'total', 'scale', 'shift', 'survivors': sorted names with final score
above 0, 'eliminated': sorted names with final score at 0 or below}.
Reported: the classification uses the final score only, so a strategy
that reaches 0 and is later shifted back above it is reported as a
survivor (three scales then a shift ends at 1); the order of operators
changes the outcome (scale,shift,scale = 2,3,1 survives; shift,scale,scale
= 5,2,1 and three scales = 0, eliminated).
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
OPERATORS = ('scale', 'shift')
START_SCORE = 4

SCOPE = 'PARTIAL: mutations only; recombination and selection pressure not modeled'
NOT_CLAIMED = (
    'does not sample real Gaussian perturbations',
    'does not implement (mu, lambda) or (mu + lambda) selection',
    'does not model strategy self-adaptation of step sizes',
    'does not run generations beyond the supplied records',
)


def _check_name(strategy: Any, row: int, field: str) -> None:
    if not isinstance(strategy, str) or type(strategy) is not str:
        raise TypeError(
            f'row {row}: {field} must be str, got {type(strategy).__name__}')
    if not 1 <= len(strategy) <= MAX_NAME:
        raise ValueError(f'row {row}: {field} must be 1-8 chars')


def _check_operator(operator: Any, row: int) -> None:
    if not isinstance(operator, str) or type(operator) is not str:
        raise TypeError(
            f'row {row}: operator must be str, got {type(operator).__name__}')
    if operator not in OPERATORS:
        raise ValueError(
            f"row {row}: operator must be one of {OPERATORS}, got {operator!r}")


def mutate(rows: Any) -> dict:
    """Return the mutation walk summary for the supplied strategy records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    scores: dict = {}
    scale = 0
    shift = 0
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (strategy, operator) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        strategy, operator = row
        _check_name(strategy, index, 'strategy')
        _check_operator(operator, index)
        if operator == 'scale':
            scale += 1
        else:
            shift += 1
        level = scores.get(strategy, START_SCORE)
        scores[strategy] = level // 2 if operator == 'scale' else level + 1
    survivors = sorted(name for name, value in scores.items() if value > 0)
    eliminated = sorted(name for name, value in scores.items() if value <= 0)
    return {'total': len(rows), 'scale': scale, 'shift': shift,
            'survivors': survivors, 'eliminated': eliminated}
