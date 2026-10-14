"""Row 986: Checkpoint Inhibitors - Unlocking immune response.

PARTIAL: compares supplied paired before/after abstract integer scores,
returning signed changes and positive-change positions. No immune
response, drug efficacy or clinical interpretation. Caps of 1-20 pairs
and abstract scores 0-100 are this module's own choices, not a standard.
"""
MAX_PAIRS = 20
MAX_SCORE = 100
NOT_CLAIMED = ('immune_response', 'drug_efficacy', 'clinical_interpretation')


def deltas(pairs):
    if type(pairs) is not tuple or not 1 <= len(pairs) <= MAX_PAIRS:
        raise ValueError('pairs: tuple of 1 to 20 score pairs required')
    for i,row in enumerate(pairs):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'pairs[{i}]: pair (before, after) required')
        for name,value in zip(('before','after'),row):
            if type(value) is not int or not 0 <= value <= MAX_SCORE:
                raise ValueError(f'pairs[{i}].{name}: whole number 0 to 100 required')
    changes = tuple(after - before for before,after in pairs)
    positives = tuple(i for i in range(len(changes)) if changes[i] > 0)
    return {'checkpoint_score_delta_validated': False, 'not_claimed': NOT_CLAIMED,
            'changes': changes, 'positive_positions': positives,
            'total_change': sum(changes), 'positive_count': len(positives)}
