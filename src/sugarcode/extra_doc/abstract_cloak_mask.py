"""Row 955: Cloaking Technology - Invisibility.

PARTIAL: Computes a supplied bit mask on supplied abstract integer values.
Caps are module-local choices without physical units. No physical
validity or production readiness claimed.
"""
NOT_CLAIMED = ('physical_invisibility', 'physical_validity', 'production_readiness')


def evaluate(rows):
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ValueError('rows: tuple of 1 to 20 integer pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (value, mask) required')
        value,mask = row
        if type(value) is not int or not 0 <= value <= 100:
            raise ValueError(f'rows[{i}].value: whole number 0 to 100 required')
        if type(mask) is not int or not mask in (0,1):
            raise ValueError(f'rows[{i}].mask: integer zero or one required')
    visible = tuple(value if mask == 1 else 0 for value,mask in rows)
    hidden = tuple(i for i,(_,mask) in enumerate(rows) if mask == 0)
    return {'abstract_cloak_mask_validated': False, 'not_claimed': NOT_CLAIMED,
            'visible_values': visible, 'hidden_positions': hidden, 'visible_total': sum(visible)}
