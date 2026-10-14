"""Row 775: Diversity - Values differences.

Bounded planning aid over caller supplied rows. No external actions, persistence,
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


def summarize_declared_perspectives(rows):
    """Rows: (participant_id, self_declared_perspective_label,
    contribution_included_bit). Count supplied perspective labels and included
    contributions. Labels arbitrary, not inferred protected traits or identity.
    No valuing differences, inclusion quality or diversity adequacy assessment.
    """
    _rows(rows, 3)
    for participant,perspective,included in rows:
        _label(participant)
        _label(perspective)
        _integer(included, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate participant')
    perspectives=[]
    for perspective in sorted({x[1] for x in rows}):
        members=[x for x in rows if x[1]==perspective]
        perspectives.append((perspective,len(members),sum(x[2] for x in members)))
    return {'perspectives':perspectives,'distinct_labels':len(perspectives)}
