"""Row 604: Unit Testing - Tests components.

SCOPED planning aid over caller supplied rows. No external actions, persistence,
capability development evidence, organization quality, or optimal policy claim.
Explicit import only; 1..32 tuple rows. Labels are lowercase ASCII identifiers.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _integer(value, low, high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low <= value <= high:
        raise ValueError('integer outside declared range')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')


def compare_results(rows):
    """Rows: (test_id, actual_integer, expected_integer), +/-1,000,000.
    Compare supplied scalar results with exact expectations; no target code is
    executed. A reporting harness only, not general test runner or coverage.
    """
    _rows(rows, 3)
    for test,actual,expected in rows:
        _label(test)
        _integer(actual, -1000000, 1000000)
        _integer(expected, -1000000, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate test')
    results=[(test,actual==expected,actual,expected) for test,actual,expected in sorted(rows)]
    return {'results':results,'passed':sum(x[1] for x in results),
            'failed':sum(not x[1] for x in results)}
