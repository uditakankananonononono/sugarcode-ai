"""Row 1084: Simultaneous Inference - Multiple comparisons.

PARTIAL: compares supplied millionth-scale p-values against a supplied
family cutoff divided by number of entries, using exact integer products.
No p-value generation, family error guarantee or inference validity.
Caps of 1-30 values and values/cutoff 0-1000000 are this module's choices.
"""
MAX_VALUES = 30
MILLION = 1000000
NOT_CLAIMED = ('pvalue_generation', 'family_error_guarantee', 'inference_validity')


def threshold(pvalues, family_cutoff):
    if type(pvalues) is not tuple or not 1 <= len(pvalues) <= MAX_VALUES:
        raise ValueError('pvalues: tuple of 1 to 30 scaled values required')
    for i,value in enumerate(pvalues):
        if type(value) is not int or not 0 <= value <= MILLION:
            raise ValueError(f'pvalues[{i}]: whole number 0 to 1000000 required')
    if type(family_cutoff) is not int or not 0 <= family_cutoff <= MILLION:
        raise ValueError('family_cutoff: whole number 0 to 1000000 required')
    n = len(pvalues)
    positions = tuple(i for i in range(n) if pvalues[i] * n <= family_cutoff)
    return {'family_threshold_validated': False, 'not_claimed': NOT_CLAIMED,
            'flagged_positions': positions, 'flagged_count': len(positions),
            'cutoff_floor': family_cutoff // n, 'cutoff_remainder': family_cutoff % n}
