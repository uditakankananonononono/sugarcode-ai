"""Row 715: Active Listening - Understands deeply.

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


def review_reflection_checklist(rows):
    """Rows: (turn_id, supplied_key_point_count, reflected_point_count,
    clarification_requested_bit). Report exact reflection coverage and missing
    points. Supplied counts not independently derived from language/transcripts;
    no actual listening, comprehension, paraphrase accuracy or deep understanding.
    Zero key points yields coverage None, not fabricated perfect understanding.
    """
    _rows(rows, 4)
    for turn,total,reflected,clarify in rows:
        _label(turn)
        _integer(total, 0, 100)
        _integer(reflected, 0, 100)
        _integer(clarify, 0, 1)
        if reflected>total:
            raise ValueError('reflections exceed key points')
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate turn')
    from fractions import Fraction as F
    turns=[]
    for turn,total,reflected,clarify in sorted(rows):
        turns.append((turn,str(F(reflected,total)) if total else None,total-reflected,bool(clarify)))
    return {'turns':turns,'missing_points':sum(x[2] for x in turns)}
