"""Row 1082: Post-Selection Inference - Valid after selection.

PARTIAL: reports supplied score margins for supplied selected positions,
and flags selected scores below a supplied threshold. No post-selection
inference, significance or selection-bias correction. Caps of 1-30 scores
in -1000 to 1000, 1-30 selected indices and threshold -1000 to 1000
are this module's own choices. Duplicate indices remain duplicated.
"""
MAX_VALUES = 30
LIMIT = 1000
NOT_CLAIMED = ('post_selection_inference', 'significance', 'selection_bias_correction')


def margins(scores, selected, threshold):
    if type(scores) is not tuple or not 1 <= len(scores) <= MAX_VALUES:
        raise ValueError('scores: tuple of 1 to 30 values required')
    if type(selected) is not tuple or not 1 <= len(selected) <= MAX_VALUES:
        raise ValueError('selected: tuple of 1 to 30 positions required')
    for i,value in enumerate(scores):
        if type(value) is not int or not -LIMIT <= value <= LIMIT:
            raise ValueError(f'scores[{i}]: whole number -1000 to 1000 required')
    for i,index in enumerate(selected):
        if type(index) is not int or not 0 <= index < len(scores):
            raise ValueError(f'selected[{i}]: position 0 to scores length minus 1 required')
    if type(threshold) is not int or not -LIMIT <= threshold <= LIMIT:
        raise ValueError('threshold: whole number -1000 to 1000 required')
    deltas = tuple(scores[i] - threshold for i in selected)
    below = tuple(i for i in range(len(deltas)) if deltas[i] < 0)
    return {'selected_score_margin_validated': False, 'not_claimed': NOT_CLAIMED,
            'margins': deltas, 'below_positions': below, 'all_meet': not below}
