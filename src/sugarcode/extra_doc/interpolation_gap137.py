"""Row 137 Overfitting Detection - Prevents memorization of training data.

PARTIAL: exact leave-one-out interpolation error diagnostic on supplied points.
Input exact dict points and threshold. Points is an exact list of 2..6 exact
lists [x,y] of exact integers -3..3; x coordinates must be distinct. Threshold
is an exact integer 0..9. For each held-out point, predict y using the unique
polynomial of degree at most n-2 interpolating every other point. Full-data
interpolation training error is zero. Return predictions as rational pairs in
input order, loo_mse rational pair, training_mse [0,1], exceeds as loo_mse >
threshold boolean, claims three False booleans. Threshold is caller-chosen.
NOT_CLAIMED: actual overfitting detection, prevention, generalization guarantee.
"""
from fractions import Fraction
SCOPE = 'PARTIAL: exact supplied polynomial interpolation leave-one-out gap only'
NOT_CLAIMED = ('actual overfitting detection', 'prevention', 'generalization guarantee')


def diagnose(data):
    if type(data) is not dict or set(data) != {'points', 'threshold'}:
        raise ValueError('exact dict with points and threshold required')
    points = data['points']
    if type(points) is not list or not 2 <= len(points) <= 6:
        raise ValueError('points must be an exact list of 2..6 pairs')
    for row in points:
        if type(row) is not list or len(row) != 2:
            raise ValueError('points must contain exact two-value lists')
        for value in row:
            if type(value) is not int or not -3 <= value <= 3:
                raise ValueError('coordinates must be exact integers -3..3')
    if len({row[0] for row in points}) != len(points):
        raise ValueError('x coordinates must be distinct')
    threshold = data['threshold']
    if type(threshold) is not int or not 0 <= threshold <= 9:
        raise ValueError('threshold must be an exact integer 0..9')
    predictions = []
    for i, (x, _) in enumerate(points):
        prediction = Fraction(0)
        for j, (xj, yj) in enumerate(points):
            if j == i:
                continue
            basis = Fraction(1)
            for k, (xk, _) in enumerate(points):
                if k != i and k != j:
                    basis *= Fraction(x-xk, xj-xk)
            prediction += yj*basis
        predictions.append(prediction)
    mse = sum(((p-row[1])**2 for p, row in zip(predictions, points)), Fraction(0))/len(points)
    return {'predictions': [[p.numerator, p.denominator] for p in predictions], 'loo_mse': [mse.numerator, mse.denominator], 'training_mse': [0, 1], 'exceeds': mse > threshold, 'claims': [False, False, False]}
