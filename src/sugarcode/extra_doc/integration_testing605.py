"""Row 605: Integration Testing - Tests combinations.

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


def exercise_composition(rows):
    """Rows: (case_id, input_value, multiplier, offset, expected_output).
    Exercise a fixed multiply component followed by an add component and
    compare exact expected values. Declarative bounded integration fixture,
    not arbitrary-service integration, network or external component testing.
    """
    _rows(rows, 5)
    for case, value, multiplier, offset, expected in rows:
        _label(case)
        for operand in (value,multiplier,offset):
            _integer(operand, -1000, 1000)
        _integer(expected, -2000000, 2000000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate case')
    def multiply(value,multiplier):
        return value*multiplier
    def add(value,offset):
        return value+offset
    results=[]
    for case,value,multiplier,offset,expected in sorted(rows):
        intermediate=multiply(value,multiplier)
        actual=add(intermediate,offset)
        results.append((case,intermediate,actual,expected,actual==expected))
    return {'cases':results,'failed':sum(not x[4] for x in results)}
