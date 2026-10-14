"""Row 460: Just-in-Time Production - Minimizes inventory.

PARTIAL: compares supplied arrival slots with consumption slots and
counts early/on-time/late deliveries. Early storage slots and late delay
slots are summed. No inventory optimization or real scheduling claim.
Caps of 1-20 pairs and integer slots 0-1000 are this module's choices.
"""
MAX_ROWS = 20
MAX_SLOT = 1000
NOT_CLAIMED = ('inventory_optimization', 'real_schedule', 'delivery_reliability')


def arrivals(rows):
    if type(rows) is not tuple or not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError('rows: tuple of 1 to 20 pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (arrival, consumption) required')
        for name,value in zip(('arrival','consumption'),row):
            if type(value) is not int or not 0 <= value <= MAX_SLOT:
                raise ValueError(f'rows[{i}].{name}: whole number 0 to 1000 required')
    early = tuple(i for i in range(len(rows)) if rows[i][0] < rows[i][1])
    late = tuple(i for i in range(len(rows)) if rows[i][0] > rows[i][1])
    storage = sum(rows[i][1] - rows[i][0] for i in early)
    delay = sum(rows[i][0] - rows[i][1] for i in late)
    return {'jit_arrivals_validated': False, 'not_claimed': NOT_CLAIMED,
            'early_positions': early, 'late_positions': late,
            'on_time_count': len(rows) - len(early) - len(late),
            'storage_slots': storage, 'delay_slots': delay}
