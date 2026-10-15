import random
from collections import Counter
from fractions import Fraction

import pytest

from sugarcode.extra_doc import emotion_confusion1991 as mod

LAB = ('joy', 'sadness', 'anger', 'neutral')


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


class L(list):
    pass


class S(str):
    pass


def fs(f):
    f = Fraction(f)
    return f'{f.numerator}/{f.denominator}'


def _oracle(pairs):
    """Independent: one-vs-rest TP/FP/FN/TN counted from raw pairs with a Counter."""
    cnt = Counter((t, p) for t, p in pairs)
    matrix = [[cnt[(t, p)] for p in LAB] for t in LAB]
    prec, rec, f1 = {}, {}, []
    for c in LAB:
        tp = sum(1 for t, p in pairs if t == c and p == c)
        fp = sum(1 for t, p in pairs if t != c and p == c)
        fn = sum(1 for t, p in pairs if t == c and p != c)
        prec[c] = None if tp + fp == 0 else fs(Fraction(tp, tp + fp))
        rec[c] = None if tp + fn == 0 else fs(Fraction(tp, tp + fn))
        if tp + fp + fn:
            f1.append(Fraction(2 * tp, 2 * tp + fp + fn))
    wrong = sorted(((v, -(LAB.index(t) * 4 + LAB.index(p)), t, p) for (t, p), v in cnt.items() if t != p), reverse=True)
    return {'matrix': matrix, 'accuracy': fs(Fraction(sum(1 for t, p in pairs if t == p), len(pairs))),
            'precision': prec, 'recall': rec, 'macro_f1': fs(sum(f1) / len(f1)),
            'confused': [wrong[0][2], wrong[0][3], wrong[0][0]] if wrong else None}


def test_scope_and_constants():
    assert mod.SCOPE == 'PARTIAL: confusion-matrix scoring of supplied emotion labels, no recognition'
    assert mod.NOT_CLAIMED == ('recognising real emotion', 'audio, faces or text', 'model quality',
                               'dataset representativeness', 'production readiness')
    assert 'NOT_CLAIMED' in mod.__doc__
    assert (mod.MAX_PAIRS, mod.LABELS) == (60, LAB)


def test_worked_examples():
    r = mod.emotion_confusion([('joy', 'joy'), ('joy', 'sadness'), ('sadness', 'sadness'), ('anger', 'joy')])
    assert r['matrix'] == [[1, 1, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]]
    assert r['accuracy'] == '1/2'
    assert r['precision'] == {'joy': '1/2', 'sadness': '1/2', 'anger': None, 'neutral': None}
    assert r['recall'] == {'joy': '1/2', 'sadness': '1/1', 'anger': '0/1', 'neutral': None}
    assert r['macro_f1'] == '7/18' and r['confused'] == ['joy', 'sadness', 1]
    assert list(r['precision']) == list(LAB) and list(r) == ['matrix', 'accuracy', 'precision', 'recall', 'macro_f1', 'confused']
    # perfect
    r = mod.emotion_confusion((('neutral', 'neutral'),))
    assert r['accuracy'] == '1/1' and r['macro_f1'] == '1/1' and r['confused'] is None
    assert r['precision']['neutral'] == '1/1' and r['precision']['joy'] is None
    # tie among wrong pairs: earliest in matrix order (row major)
    r = mod.emotion_confusion([['anger', 'joy'], ['joy', 'anger']])
    assert r['confused'] == ['joy', 'anger', 1] and r['accuracy'] == '0/1' and r['macro_f1'] == '0/1'
    # larger count wins over earlier cell
    r = mod.emotion_confusion([('joy', 'anger'), ('neutral', 'sadness'), ('neutral', 'sadness')])
    assert r['confused'] == ['neutral', 'sadness', 2]


def test_randomized_against_counter_oracle():
    rng = random.Random(1991)
    for _ in range(1500):
        n = rng.randint(1, 60)
        pool = rng.choice([LAB, LAB[:2], LAB[1:], LAB[:1]])
        pairs = [(rng.choice(pool), rng.choice(pool)) for _ in range(n)]
        got = mod.emotion_confusion(pairs if rng.random() < .5 else [list(p) for p in pairs])
        assert got == _oracle(pairs)
        assert sum(map(sum, got['matrix'])) == n


def test_validation_messages_boundaries_and_order():
    ok = ('joy', 'joy')
    for bad in (None, 'ab', 5, {}, L([ok])):
        _raises(TypeError, 'pairs must be a list or tuple', mod.emotion_confusion, bad)
    _raises(ValueError, 'pairs must hold 1 to 60 pairs', mod.emotion_confusion, [])
    _raises(ValueError, 'pairs must hold 1 to 60 pairs', mod.emotion_confusion, [ok] * 61)
    assert sum(map(sum, mod.emotion_confusion([ok] * 60)['matrix'])) == 60
    for bad in (None, 'jo', ('joy',), ('joy', 'joy', 'joy'), 5):
        _raises(TypeError, 'pair 1: expected a (truth, predicted) pair', mod.emotion_confusion, [bad])
    _raises(TypeError, 'pair 2: expected a (truth, predicted) pair', mod.emotion_confusion, [ok, None])
    T = 'pair 2: truth must be one of joy, sadness, anger, neutral'
    P = 'pair 2: predicted must be one of joy, sadness, anger, neutral'
    for bad in ('Joy', 'JOY', 'joy ', ' joy', 'happy', '', None, 5, b'joy', 'sadness\u200b',
                '\u00c9', '\u0130', '\u212a', "'", 'joy\x00', 'joy\n', '\x7f', '\x1f'):
        _raises(ValueError, T, mod.emotion_confusion, [ok, (bad, 'joy')])
        _raises(ValueError, P, mod.emotion_confusion, [ok, ('joy', bad)])
    # str subclass: accepted only if exact str required -> rejected
    _raises(ValueError, T, mod.emotion_confusion, [ok, (S('joy'), 'joy')])
    _raises(ValueError, P, mod.emotion_confusion, [ok, ('joy', S('joy'))])
    for name in LAB:
        assert mod.emotion_confusion([(name, name)])['accuracy'] == '1/1'
    # order: container, count, shape, truth before predicted
    _raises(TypeError, 'pairs must be a list or tuple', mod.emotion_confusion, 'x')
    _raises(ValueError, 'pairs must hold 1 to 60 pairs', mod.emotion_confusion, [])
    _raises(TypeError, 'pair 1: expected a (truth, predicted) pair', mod.emotion_confusion, [None, ('x', 'y')])
    _raises(ValueError, 'pair 1: truth must be one of joy, sadness, anger, neutral', mod.emotion_confusion, [('x', 'y')])
    _raises(ValueError, 'pair 1: predicted must be one of joy, sadness, anger, neutral', mod.emotion_confusion, [('joy', 'y')])
