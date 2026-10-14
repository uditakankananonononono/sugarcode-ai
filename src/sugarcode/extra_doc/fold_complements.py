"""Row 1080: Cross-Fitting - Avoid overfitting.

PARTIAL: lists held-out and complementary training positions for supplied
fold assignments. No fitting, overfitting prevention or estimate validity.
Caps of 2-30 assignments and 2-8 folds are this module's own choices.
Each fold must have at least one assigned position.
"""
MAX_ROWS = 30
MAX_FOLDS = 8
NOT_CLAIMED = ('model_fitting', 'overfitting_prevention', 'estimate_validity')


def complements(assignments, folds):
    if type(assignments) is not tuple or not 2 <= len(assignments) <= MAX_ROWS:
        raise ValueError('assignments: tuple of 2 to 30 fold indices required')
    if type(folds) is not int or not 2 <= folds <= MAX_FOLDS:
        raise ValueError('folds: whole number 2 to 8 required')
    for i,value in enumerate(assignments):
        if type(value) is not int or not 0 <= value < folds:
            raise ValueError(f'assignments[{i}]: fold index 0 to folds minus 1 required')
    held = tuple(tuple(i for i in range(len(assignments)) if assignments[i] == f) for f in range(folds))
    for f,positions in enumerate(held):
        if not positions:
            raise ValueError(f'folds[{f}]: at least one held-out position required')
    training = tuple(tuple(i for i in range(len(assignments)) if assignments[i] != f) for f in range(folds))
    return {'fold_complements_validated': False, 'not_claimed': NOT_CLAIMED,
            'held_positions': held, 'training_positions': training,
            'held_counts': tuple(len(p) for p in held)}
