"""Row 456: Manufacturing Planning - Schedules production.

PARTIAL: splits a supplied integer unit count into consecutive full
batches and a final partial batch, computing fixed per-batch finish slots.
No machine assignment, real-time schedule or production feasibility.
Caps of 1-10000 units, batch size 1-1000 and fixed duration 1-100
are this module's own choices, not a domain standard.
"""
MAX_UNITS = 10000
MAX_BATCH = 1000
MAX_DURATION = 100
NOT_CLAIMED = ('machine_assignment', 'real_schedule', 'feasibility')


def batches(units, batch_size, duration):
    for name,value,cap in (('units',units,MAX_UNITS), ('batch_size',batch_size,MAX_BATCH),
                           ('duration',duration,MAX_DURATION)):
        if type(value) is not int or not 1 <= value <= cap:
            raise ValueError(f'{name}: whole number 1 to {cap} required')
    full, partial = divmod(units, batch_size)
    sizes = (batch_size,) * full + ((partial,) if partial else ())
    finishes = tuple((i + 1) * duration for i in range(len(sizes)))
    return {'production_batches_validated': False, 'not_claimed': NOT_CLAIMED,
            'sizes': sizes, 'finish_slots': finishes,
            'batch_count': len(sizes), 'total_duration': len(sizes) * duration}
