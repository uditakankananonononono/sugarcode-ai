"""Row 1009: Neurostimulation - Electrical brain stimulation.

PARTIAL: counts sign changes in supplied abstract signed integers,
ignoring zero entries, and reports net sum. This is not a stimulation
waveform, device protocol or medical tool. No electrical safety,
brain stimulation or treatment efficacy. Caps of 1-30 entries and
values -100 to 100 are this module's own choices.
"""
MAX_VALUES = 30
LIMIT = 100
NOT_CLAIMED = ('electrical_safety', 'brain_stimulation', 'treatment_efficacy')


def polarity(values):
    if type(values) is not tuple or not 1 <= len(values) <= MAX_VALUES:
        raise ValueError('values: tuple of 1 to 30 abstract values required')
    for i,value in enumerate(values):
        if type(value) is not int or not -LIMIT <= value <= LIMIT:
            raise ValueError(f'values[{i}]: whole number -100 to 100 required')
    signs = tuple(1 if value > 0 else -1 for value in values if value != 0)
    changes = tuple(i for i in range(1,len(signs)) if signs[i] != signs[i-1])
    return {'abstract_polarity_validated': False, 'not_claimed': NOT_CLAIMED,
            'nonzero_signs': signs, 'sign_change_positions': changes,
            'sign_change_count': len(changes), 'net': sum(values)}
