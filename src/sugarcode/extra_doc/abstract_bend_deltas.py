"""Row 946: Soft Robotics - Flexible robots.

PARTIAL: computes differences between adjacent supplied abstract segment
values and counts direction reversals. Caps are module-local choices with
no physical units. No robot control, material behavior or safety claims.
"""
NOT_CLAIMED = ('robot_control', 'material_behavior', 'physical_safety')


def bends(values):
    if type(values) is not tuple or not 2 <= len(values) <= 30:
        raise ValueError('values: tuple of 2 to 30 integers required')
    for i,value in enumerate(values):
        if type(value) is not int or not -100 <= value <= 100:
            raise ValueError(f'values[{i}]: whole number -100 to 100 required')
    deltas = tuple(values[i]-values[i-1] for i in range(1,len(values)))
    reversals = tuple(i for i in range(1,len(deltas)) if deltas[i]*deltas[i-1] < 0)
    return {'abstract_bend_deltas_validated': False, 'not_claimed': NOT_CLAIMED,
            'deltas': deltas, 'reversal_positions': reversals,
            'variation': sum(abs(value) for value in deltas)}
