"""Row 457: Quality Control - Ensures standards.

PARTIAL: flags supplied integer measurements outside inclusive supplied
lower/upper bounds and reports the acceptance count. No certification,
sampling assurance, calibration or claim that real standards are met.
Caps of 1-30 measurements and values/bounds -1000 to 1000 are this
module's own choices, not a domain standard.
"""
MAX_SAMPLES = 30
LIMIT = 1000
NOT_CLAIMED = ('certification', 'sampling_assurance', 'calibration')


def inspect(values, lower, upper):
    if type(values) is not tuple or not 1 <= len(values) <= MAX_SAMPLES:
        raise ValueError('values: tuple of 1 to 30 measurements required')
    for i,value in enumerate(values):
        if type(value) is not int or not -LIMIT <= value <= LIMIT:
            raise ValueError(f'values[{i}]: whole number -1000 to 1000 required')
    for name,value in (('lower',lower),('upper',upper)):
        if type(value) is not int or not -LIMIT <= value <= LIMIT:
            raise ValueError(f'{name}: whole number -1000 to 1000 required')
    if lower > upper:
        raise ValueError('lower must not exceed upper')
    below = tuple(i for i in range(len(values)) if values[i] < lower)
    above = tuple(i for i in range(len(values)) if values[i] > upper)
    accepted = len(values) - len(below) - len(above)
    return {'tolerance_sample_validated': False, 'not_claimed': NOT_CLAIMED,
            'below_positions': below, 'above_positions': above,
            'accepted_count': accepted, 'all_in_bounds': accepted == len(values)}
