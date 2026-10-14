"""Row 1081: Sample Splitting - Honest estimation.

PARTIAL: partitions supplied integer rows by every kth index, sending
indices divisible by k to holdout and the rest to training. No honest
estimation guarantee, randomization or generalization evidence. Caps
of 2-30 values in -1000 to 1000 and k 2-10 are this module's choices.
"""
MAX_VALUES = 30
LIMIT = 1000
MAX_PERIOD = 10
NOT_CLAIMED = ('honest_estimation', 'randomization', 'generalization')


def split(values, period):
    if type(values) is not tuple or not 2 <= len(values) <= MAX_VALUES:
        raise ValueError('values: tuple of 2 to 30 entries required')
    for i,value in enumerate(values):
        if type(value) is not int or not -LIMIT <= value <= LIMIT:
            raise ValueError(f'values[{i}]: whole number -1000 to 1000 required')
    if type(period) is not int or not 2 <= period <= MAX_PERIOD:
        raise ValueError('period: whole number 2 to 10 required')
    holdout_positions = tuple(i for i in range(len(values)) if i % period == 0)
    training_positions = tuple(i for i in range(len(values)) if i % period != 0)
    return {'sample_partition_validated': False, 'not_claimed': NOT_CLAIMED,
            'holdout_positions': holdout_positions, 'training_positions': training_positions,
            'holdout_values': tuple(values[i] for i in holdout_positions),
            'training_values': tuple(values[i] for i in training_positions)}
