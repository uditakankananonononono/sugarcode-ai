"""Row 1010: Transcranial Magnetic Stimulation - Magnetic brain stimulation.

PARTIAL: checks gaps between supplied abstract increasing integer slots
against a supplied minimum. No device protocol, magnetic stimulation,
medical scheduling or treatment claim. Caps of 2-30 slots in 0-1000
and minimum gap 1-1000 are this module's own choices.
"""
MAX_SLOTS = 30
LIMIT = 1000
NOT_CLAIMED = ('device_protocol', 'magnetic_stimulation', 'treatment')


def spacing(slots, minimum_gap):
    if type(slots) is not tuple or not 2 <= len(slots) <= MAX_SLOTS:
        raise ValueError('slots: tuple of 2 to 30 abstract slots required')
    for i,value in enumerate(slots):
        if type(value) is not int or not 0 <= value <= LIMIT:
            raise ValueError(f'slots[{i}]: whole number 0 to 1000 required')
    if type(minimum_gap) is not int or not 1 <= minimum_gap <= LIMIT:
        raise ValueError('minimum_gap: whole number 1 to 1000 required')
    for i in range(1,len(slots)):
        if slots[i] <= slots[i-1]:
            raise ValueError(f'slots[{i}]: slots must strictly increase')
    gaps = tuple(slots[i] - slots[i-1] for i in range(1,len(slots)))
    short = tuple(i for i in range(len(gaps)) if gaps[i] < minimum_gap)
    return {'abstract_slot_spacing_validated': False, 'not_claimed': NOT_CLAIMED,
            'gaps': gaps, 'short_gap_positions': short,
            'all_spaced': not short, 'span': slots[-1] - slots[0]}
