"""Row 1168: Pain Management.

PARTIAL: counts supplied abstract score reductions meeting a supplied
minimum reduction. No pain assessment, treatment advice or efficacy.
Caps of 1-20 pairs and abstract scores/minimum reduction 0-100 are
this module's own choices, not a clinical scale or standard.
"""
MAX_ROWS = 20
LIMIT = 100
NOT_CLAIMED = ('pain_assessment', 'treatment_advice', 'efficacy')


def reductions(pairs, minimum):
    if type(pairs) is not tuple or not 1 <= len(pairs) <= MAX_ROWS:
        raise ValueError('pairs: tuple of 1 to 20 pairs required')
    for i,row in enumerate(pairs):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'pairs[{i}]: pair (before, after) required')
        for name,value in zip(('before','after'),row):
            if type(value) is not int or not 0 <= value <= LIMIT:
                raise ValueError(f'pairs[{i}].{name}: whole number 0 to 100 required')
    if type(minimum) is not int or not 0 <= minimum <= LIMIT:
        raise ValueError('minimum: whole number 0 to 100 required')
    changes = tuple(before - after for before,after in pairs)
    positions = tuple(i for i in range(len(changes)) if changes[i] >= minimum)
    return {'abstract_score_reduction_validated': False, 'not_claimed': NOT_CLAIMED,
            'reductions': changes, 'meeting_positions': positions,
            'meeting_count': len(positions), 'total_reduction': sum(changes)}
