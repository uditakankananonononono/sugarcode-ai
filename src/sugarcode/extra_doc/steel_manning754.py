"""Row 754: Steel Manning - Best version of argument.

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


def choose_supplied_argument_version(rows):
    """Rows: (version_id, supplied_valid_premise_count, inference_gap_count,
    conclusion_support_count). Prefer fewest gaps then greatest support then
    greatest valid premises then ID. Caller assessments not independently
    checked. No argument rewriting/generation/validity proof or actual best
    opposing argument; best only within this declared finite scoring rubric.
    """
    _rows(rows, 4)
    for version,premises,gaps,support in rows:
        _label(version)
        _integer(premises, 0, 100)
        _integer(gaps, 0, 100)
        _integer(support, 0, 100)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate version')
    ranked=sorted(rows,key=lambda x:(x[2],-x[3],-x[1],x[0]))
    return {'ranked':[x[0] for x in ranked],'selected':ranked[0][0]}
