import random
import re
import pytest
from sugarcode.extra_doc.persuasive_writing import check_copy as cc

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


KEYWORD = re.compile(r"[a-z0-9]+")
ABS = {'always', 'never', 'guaranteed', 'best', 'perfect', 'unbeatable'}


def oracle(sentences):
    probs, you, ques, words = [], 0, 0, 0
    for i, s in enumerate(sentences):
        keys = KEYWORD.findall(s.lower())
        words += len(s.split())
        if len(s.split()) > 24:
            probs.append((i, 'too_long'))
        if len(ABS.intersection(keys)) > 0:
            probs.append((i, 'absolute_claim'))
        if 'you' in keys or 'your' in keys:
            you += 1
        if len(s) > 0 and s[-1] == '?':
            ques += 1
    return {'problems': sorted(probs), 'you': you, 'questions': ques, 'words': words}


def test_hand_cases():
    assert cc([]) == {'problems': [], 'you': 0, 'questions': 0, 'words': 0}
    assert cc(['You always win.']) == {'problems': [(0, 'absolute_claim')], 'you': 1, 'questions': 0, 'words': 3}
    assert cc(['Why wait?'])['questions'] == 1
    assert cc(['why wait? '])['questions'] == 0                   # trailing space, so no '?' ending
    assert cc(['ALWAYS on sale.'])['problems'] == [(0, 'absolute_claim')]
    assert cc(['The (best) price; guaranteed!'])['problems'] == [(0, 'absolute_claim')]
    assert cc(['a ' * 23 + 'b'])['problems'] == []
    assert cc(['a ' * 24 + 'b'])['problems'] == [(0, 'too_long')]
    assert cc(['Your call, you decide'])['you'] == 1               # one sentence, counted once
    assert cc(['You go.', 'Your turn.'])['you'] == 2
    assert cc(['best best best'])['problems'] == [(0, 'absolute_claim')]   # once per sentence
    assert cc(['unbeaten rivals'])['problems'] == []               # not the table word
    assert cc(['x' * 200])['words'] == 1


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(7110 + part)
    seen, clean = set(), 0
    bag = ['you', 'your', 'always', 'Never', 'GUARANTEED', 'best', 'perfect', 'unbeatable',
           'unbeaten', 'we', 'it', '(best)', 'sale,', 'now!', 'why?', 'a', 'the']
    for _ in range(60):
        sents = []
        for _ in range(rnd.randint(0, 6)):
            if rnd.random() < 0.25:
                n, pool = rnd.randint(25, 45), ('a', 'the', 'it', 'we', 'you')
            else:
                n, pool = rnd.choice((1, 2, 3, rnd.randint(4, 16))), bag
            s = ' '.join(rnd.choice(pool) for _ in range(n))
            if rnd.random() < 0.3:
                s += '?'
            sents.append(s)
        r = cc(sents)
        assert r == oracle(sents)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 2 and clean > 5


def test_limits_accepted():
    sents = ['word ' * 23 + 'end'] * 40
    r = cc(sents)
    assert r == {'problems': [], 'you': 0, 'questions': 0, 'words': 960}
    cc(['x' * 200, 'y'])


def err(exc, msg, sentences):
    with pytest.raises(exc) as e:
        cc(sentences)
    assert str(e.value) == msg


SL = 'sentence length must be 1 to 200 characters'
ST = 'each sentence must be an exact string'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}, 5):
        err(T, 'sentences must be an exact list', bad)
    err(V, 'sentence count must be at most 40', ['ok'] * 41)
    for bad in (None, 5, b'a', StrSub('a'), ['a'], ('a',)):
        err(T, ST, [bad])
    for bad in ('', 'x' * 201):
        err(V, SL, [bad])


def _order(err):
    err(T, 'sentences must be an exact list', 'x')
    err(V, 'sentence count must be at most 40', [None] * 41)
    err(T, ST, [None, ''])
    err(V, SL, ['', None])
    err(T, ST, ['ok', 5])
    err(V, SL, ['ok', ''])
    err(V, SL, ['ok', 'x' * 201])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,t', _collect(_pins))
def test_pin(exc, msg, t):
    err(exc, msg, t)


@pytest.mark.parametrize('exc,msg,t', _collect(_order))
def test_order(exc, msg, t):
    err(exc, msg, t)
