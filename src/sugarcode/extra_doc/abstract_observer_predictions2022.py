"""Row 2022: Second-Order Cybernetics.

PARTIAL: counts agreements of supplied binary observer predictions with a
supplied binary sequence, reporting each observer's exact error positions.
Local caps; no reflexivity, observer theory or epistemic validity claims.
"""
NOT_CLAIMED = ('reflexivity', 'observer_theory', 'epistemic_validity')


def audit(actual, predictions):
    if type(actual) is not tuple or not 1 <= len(actual) <= 20:
        raise ValueError('actual: tuple of 1 to 20 integer bits required')
    for j,value in enumerate(actual):
        if type(value) is not int or value not in (0,1):
            raise ValueError(f'actual[{j}]: integer zero or one required')
    if type(predictions) is not tuple or not 1 <= len(predictions) <= 10:
        raise ValueError('predictions: tuple of 1 to 10 sequences required')
    for i,row in enumerate(predictions):
        if type(row) is not tuple or len(row) != len(actual):
            raise ValueError(f'predictions[{i}]: tuple matching actual length required')
        for j,value in enumerate(row):
            if type(value) is not int or value not in (0,1):
                raise ValueError(f'predictions[{i}][{j}]: integer zero or one required')
    errors = tuple(tuple(j for j in range(len(actual)) if row[j] != actual[j]) for row in predictions)
    return {'abstract_observer_predictions_validated': False, 'not_claimed': NOT_CLAIMED,
            'error_positions': errors, 'correct_counts': tuple(len(actual)-len(e) for e in errors),
            'perfect_observers': tuple(i for i,e in enumerate(errors) if not e)}
