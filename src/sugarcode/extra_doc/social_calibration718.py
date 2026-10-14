"""Row 718: Social Calibration - Adjusts to context.

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


def select_context_register(rows):
    """Rows: (message_id, caller_work_context_bit, sensitive_topic_bit,
    informal_opt_in_bit). Fixed register rubric: sensitive always careful;
    otherwise informal only opted in and nonwork, else neutral. No context
    inference, real audience taste/social skill or appropriateness guarantee.
    Caller supplied context and preferences, advisory register labels only.
    """
    _rows(rows, 4)
    for message,work,sensitive,informal in rows:
        _label(message)
        _integer(work, 0, 1)
        _integer(sensitive, 0, 1)
        _integer(informal, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate message')
    registers=[]
    for message,work,sensitive,informal in sorted(rows):
        if sensitive==1:
            register='careful'
        elif work==0 and informal==1:
            register='informal'
        else:
            register='neutral'
        registers.append((message,register))
    return {'registers':registers}
