"""Row 829: Self-Assessment - Evaluates own work.

PARTIAL: counts supplied abstract binary self/observed pairs in four cells
and returns disagreement positions. Cap20 is a local choice. No assessment
truth, metacognitive validity or learner evaluation.
"""
NOT_CLAIMED = ('assessment_truth', 'metacognitive_validity', 'learner_evaluation')


def contingency(rows):
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ValueError('rows: tuple of 1 to 20 bit pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (self_bit, observed_bit) required')
        for j,value in enumerate(row):
            if type(value) is not int or value not in (0,1):
                raise ValueError(f'rows[{i}][{j}]: integer zero or one required')
    cells = tuple(sum(row == pair for row in rows) for pair in ((0,0),(0,1),(1,0),(1,1)))
    mismatch = tuple(i for i,(a,b) in enumerate(rows) if a != b)
    return {'abstract_self_contingency_validated': False, 'not_claimed': NOT_CLAIMED,
            'cells_00_01_10_11': cells, 'disagreement_positions': mismatch,
            'agreement_count': len(rows)-len(mismatch)}
