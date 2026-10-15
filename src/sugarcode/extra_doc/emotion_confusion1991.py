"""Row 1991, Emotion Recognition: exact scoring of supplied emotion predictions.

emotion_confusion(pairs): pairs is a list or tuple of 1 to 60 pairs
(truth, predicted), each a list or tuple of two labels from the fixed set
'joy', 'sadness', 'anger', 'neutral' (exact str). Exact Fraction arithmetic.
Reported: matrix (4 rows by 4 columns of counts, truth by row and predicted
by column in the order joy, sadness, anger, neutral), accuracy (correct /
total as 'n/d' in lowest terms), precision and recall (dicts keyed in that
label order; value 'n/d' or None when the denominator is 0), macro_f1 (the
mean over every label that occurs in any truth or prediction of
2*TP / (2*TP + FP + FN), as 'n/d'), confused (None when every pair is
correct, otherwise [truth, predicted, count] for the wrong pair with the
highest count, earliest in matrix order on ties).
Checks per pair in order: shape, truth, predicted.
NOT_CLAIMED: recognising real emotion, audio, faces or text, model quality,
dataset representativeness, production readiness.
"""
from fractions import Fraction

SCOPE = 'PARTIAL: confusion-matrix scoring of supplied emotion labels, no recognition'
NOT_CLAIMED = ('recognising real emotion', 'audio, faces or text', 'model quality',
               'dataset representativeness', 'production readiness')

MAX_PAIRS = 60
LABELS = ('joy', 'sadness', 'anger', 'neutral')


def _fs(f):
    return f'{f.numerator}/{f.denominator}'


def _ratio(num, den):
    return None if den == 0 else _fs(Fraction(num, den))


def emotion_confusion(pairs):
    if type(pairs) not in (list, tuple):
        raise TypeError('pairs must be a list or tuple')
    if not 1 <= len(pairs) <= MAX_PAIRS:
        raise ValueError('pairs must hold 1 to 60 pairs')
    k = len(LABELS)
    matrix = [[0] * k for _ in range(k)]
    for i, pair in enumerate(pairs, 1):
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise TypeError(f'pair {i}: expected a (truth, predicted) pair')
        truth, pred = pair
        if type(truth) is not str or truth not in LABELS:
            raise ValueError(f'pair {i}: truth must be one of joy, sadness, anger, neutral')
        if type(pred) is not str or pred not in LABELS:
            raise ValueError(f'pair {i}: predicted must be one of joy, sadness, anger, neutral')
        matrix[LABELS.index(truth)][LABELS.index(pred)] += 1
    total = len(pairs)
    correct = sum(matrix[c][c] for c in range(k))
    precision, recall, f1s = {}, {}, []
    for c, name in enumerate(LABELS):
        tp = matrix[c][c]
        row = sum(matrix[c])
        col = sum(matrix[r][c] for r in range(k))
        precision[name] = _ratio(tp, col)
        recall[name] = _ratio(tp, row)
        if row or col:
            f1s.append(Fraction(2 * tp, row + col))
    confused = None
    best = 0
    for r in range(k):
        for c in range(k):
            if r != c and matrix[r][c] > best:
                best = matrix[r][c]
                confused = [LABELS[r], LABELS[c], best]
    return {'matrix': matrix, 'accuracy': _fs(Fraction(correct, total)), 'precision': precision,
            'recall': recall, 'macro_f1': _fs(sum(f1s, Fraction(0)) / len(f1s)), 'confused': confused}
