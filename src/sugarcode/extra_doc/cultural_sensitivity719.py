"""Row 719: Cultural Sensitivity - Respects differences.

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


def review_explicit_preferences(rows):
    """Rows: (interaction_id, caller_preferred_style0..2,
    proposed_style0..2, preference_confirmed_bit). Check only explicit supplied
    individual preference alignment, never infer from cultural identity.
    Unconfirmed preference needs confirmation; confirmed mismatch needs change.
    No cultural classification, sensitivity assessment or respect demonstrated.
    """
    _rows(rows, 4)
    for interaction,preferred,proposed,confirmed in rows:
        _label(interaction)
        _integer(preferred, 0, 2)
        _integer(proposed, 0, 2)
        _integer(confirmed, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate interaction')
    reviews=[]
    for interaction,preferred,proposed,confirmed in sorted(rows):
        if confirmed==0:
            status='confirm_preference'
        elif preferred!=proposed:
            status='change_to_confirmed_preference'
        else:
            status='matches_confirmed_preference'
        reviews.append((interaction,status))
    return {'reviews':reviews}
