"""Row 717: Emotional Intelligence - Reads and responds to emotions.

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


def review_response_signals(rows):
    """Rows: (turn_id, caller_distress_bit, acknowledgement_bit,
    permission_before_advice_bit). Supplied checklist flags distress turns
    missing acknowledgement or permission. NO reading/inference of emotions,
    actual emotional intelligence, crisis triage or appropriate-response proof.
    Caller classifications unverified; advisory missing-elements report only.
    """
    _rows(rows, 4)
    for turn,distress,ack,permission in rows:
        _label(turn)
        _integer(distress, 0, 1)
        _integer(ack, 0, 1)
        _integer(permission, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate turn')
    gaps=[]
    for turn,distress,ack,permission in sorted(rows):
        missing=[]
        if distress==1 and ack==0:
            missing.append('acknowledgement')
        if distress==1 and permission==0:
            missing.append('permission_before_advice')
        gaps.append((turn,missing))
    return {'turns':gaps,'turns_with_gaps':sum(bool(x[1]) for x in gaps)}
