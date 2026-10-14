"""Row 772: Trust Building - Creates confidence.

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


def review_declared_commitments(rows):
    """Rows: (commitment_id, due_bit, completed_bit, status_disclosed_bit).
    Flag supplied due incomplete commitments and undisclosed incomplete ones.
    No confidence/trust assessment, identity verification or actual followthrough;
    completed bit remains a caller assertion, not proof of earned trust.
    """
    _rows(rows, 4)
    for commitment,due,complete,disclosed in rows:
        _label(commitment)
        _integer(due, 0, 1)
        _integer(complete, 0, 1)
        _integer(disclosed, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate commitment')
    overdue=sorted(c for c,due,done,_ in rows if due==1 and done==0)
    undisclosed=sorted(c for c,_,done,disclosed in rows if done==0 and disclosed==0)
    return {'overdue':overdue,'undisclosed_incomplete':undisclosed,
            'completed_count':sum(x[2] for x in rows)}
