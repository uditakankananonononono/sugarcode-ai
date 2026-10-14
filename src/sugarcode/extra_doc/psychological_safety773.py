"""Row 773: Psychological Safety - Enables risk-taking.

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


def review_declared_feedback_conditions(rows):
    """Rows: (session_id, dissent_invited_bit, retaliation_reported_bit,
    confidential_route_available_bit). Flag supplied checklist concerns, not
    infer safety from people/text. No psychological safety measurement, risk
    taking encouragement or workplace/legal/clinical safety certification.
    Absence of flags is not proof participants feel safe.
    """
    _rows(rows, 4)
    for session,dissent,retaliation,route in rows:
        _label(session)
        _integer(dissent, 0, 1)
        _integer(retaliation, 0, 1)
        _integer(route, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate session')
    reviews=[]
    for session,dissent,retaliation,route in sorted(rows):
        concerns=[]
        if dissent==0:
            concerns.append('dissent_not_invited')
        if retaliation==1:
            concerns.append('retaliation_reported')
        if route==0:
            concerns.append('confidential_route_missing')
        reviews.append((session,concerns))
    return {'reviews':reviews,'sessions_with_concerns':sum(bool(x[1]) for x in reviews)}
