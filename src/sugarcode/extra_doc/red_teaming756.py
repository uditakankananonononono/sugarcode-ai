"""Row 756: Red Teaming - Finds vulnerabilities.

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


def review_declared_test_failures(rows):
    """Rows: (test_id, supplied_severity1..10, failure_observed_bit,
    mitigation_verified_bit). Return unmitigated declared failures ranked
    severity descending then ID, and all declared observed failures. No attacks,
    exploitation, actual testing or vulnerability discovery/mitigation proof.
    Local supplied-results review only, no security assurance.
    """
    _rows(rows, 4)
    for test,severity,failure,mitigated in rows:
        _label(test)
        _integer(severity, 1, 10)
        _integer(failure, 0, 1)
        _integer(mitigated, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate test')
    open_findings=sorted((x for x in rows if x[2]==1 and x[3]==0),key=lambda x:(-x[1],x[0]))
    return {'open_findings':[(x[0],x[1]) for x in open_findings],
            'observed_failures':sorted(x[0] for x in rows if x[2]==1)}
