"""Row 596: Embedded Systems - Programs microcontrollers.

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


def simulate_register_writes(rows):
    """Rows: (step_id, prior_register_byte, mask_byte, supplied_value_byte).
    Simulate an independent 8-bit masked write for each row:
    preserve unmasked bits and replace masked bits. No hardware programming,
    volatile memory, timing, interrupts, register-map or device connection.
    """
    _rows(rows, 4)
    for step, prior, mask, value in rows:
        _label(step)
        _integer(prior, 0, 255)
        _integer(mask, 0, 255)
        _integer(value, 0, 255)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate step')
    return {'writes':[(step,(prior & (255^mask)) | (value & mask))
                      for step,prior,mask,value in sorted(rows)]}
