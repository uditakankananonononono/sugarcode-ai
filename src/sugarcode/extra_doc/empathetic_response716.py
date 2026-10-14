"""Row 716: Empathetic Response - Acknowledges feelings.

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


def build_acknowledgement_templates(rows):
    """Rows: (turn_id, caller_feeling_code0=frustrated/1=sad/2=excited,
    advice_requested_bit). Return explicit tentative acknowledgement plus ask
    permission before advice when not requested. Fixed template fixture, no
    emotion inference, actual conversation delivery or empathy demonstrated.
    Caller label remains tentative; templates do not assert inferred feelings.
    """
    _rows(rows, 3)
    for turn,feeling,advice in rows:
        _label(turn)
        _integer(feeling, 0, 2)
        _integer(advice, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate turn')
    labels=('frustrated','sad','excited')
    templates=[]
    for turn,feeling,advice in sorted(rows):
        acknowledgement='It sounds like you may be '+labels[feeling]+'.'
        next_step='What would help most?' if advice==1 else 'Would you like ideas, or would you rather I listen?'
        templates.append((turn,acknowledgement,next_step))
    return {'templates':templates}
