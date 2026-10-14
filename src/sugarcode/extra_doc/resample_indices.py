"""Row 1023: Bootstrapping - Resamples for inference.

PARTIAL: constructs a supplied-index resample from supplied integer
values and reports its total and source-position usage counts. No
randomness, bootstrap inference or uncertainty estimate. Caps of 1-20
values in -1000 to 1000 and 1-30 supplied indices are this module's choices.
"""
MAX_VALUES = 20
MAX_INDICES = 30
LIMIT = 1000
NOT_CLAIMED = ('randomness', 'bootstrap_inference', 'uncertainty')


def resample(values, indices):
    if type(values) is not tuple or not 1 <= len(values) <= MAX_VALUES:
        raise ValueError('values: tuple of 1 to 20 entries required')
    if type(indices) is not tuple or not 1 <= len(indices) <= MAX_INDICES:
        raise ValueError('indices: tuple of 1 to 30 positions required')
    for i,value in enumerate(values):
        if type(value) is not int or not -LIMIT <= value <= LIMIT:
            raise ValueError(f'values[{i}]: whole number -1000 to 1000 required')
    for i,index in enumerate(indices):
        if type(index) is not int or not 0 <= index < len(values):
            raise ValueError(f'indices[{i}]: position 0 to values length minus 1 required')
    sampled = tuple(values[i] for i in indices)
    usage = tuple(sum(i == source for i in indices) for source in range(len(values)))
    return {'resample_indices_validated': False, 'not_claimed': NOT_CLAIMED,
            'sampled': sampled, 'total': sum(sampled), 'usage': usage,
            'unused_positions': tuple(i for i in range(len(usage)) if usage[i] == 0)}
