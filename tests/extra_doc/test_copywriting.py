import random
import re
import pytest
from sugarcode.extra_doc.copywriting import check_copy as cc

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


CAPS = {'subject': 60, 'headline': 30, 'button': 20, 'post': 280}


def oracle(blocks):
    probs, ch, chars = [], {}, 0
    for i, (c, t) in enumerate(blocks):
        if len(t) > CAPS[c]:
            probs.append((i, 'over_cap'))
        n = 0
        for x in t:
            if x == '!':
                n += 1
        if n >= 2:
            probs.append((i, 'hype'))
        if any(re.fullmatch(r'[A-Z]{4,}', w) for w in t.split()):
            probs.append((i, 'shouting'))
        ch[c] = ch.get(c, 0) + 1
        chars += len(t)
    return {'problems': sorted(probs), 'channels': {k: ch[k] for k in sorted(ch)}, 'chars': chars}


def test_hand_cases():
    assert cc([]) == {'problems': [], 'channels': {}, 'chars': 0}
    assert cc([('subject', 'Hello there')]) == {'problems': [], 'channels': {'subject': 1}, 'chars': 11}
    assert cc([('headline', 'x' * 30)])['problems'] == []
    assert cc([('headline', 'x' * 31)])['problems'] == [(0, 'over_cap')]
    assert cc([('button', 'x' * 20)])['problems'] == []
    assert cc([('button', 'x' * 21)])['problems'] == [(0, 'over_cap')]
    assert cc([('post', 'x' * 280)])['problems'] == []
    assert cc([('post', 'x' * 281)])['problems'] == [(0, 'over_cap')]
    assert cc([('subject', 'x' * 60)])['problems'] == []
    assert cc([('subject', 'x' * 61)])['problems'] == [(0, 'over_cap')]
    assert cc([('subject', 'Hi!')])['problems'] == []
    assert cc([('subject', 'Hi! There!')])['problems'] == [(0, 'hype')]
    assert cc([('subject', 'FREE shipping today')])['problems'] == [(0, 'shouting')]
    assert cc([('subject', 'Free shipping today')])['problems'] == []
    assert cc([('subject', 'SALE')])['problems'] == [(0, 'shouting')]
    assert cc([('subject', 'ZZZZ')])['problems'] == [(0, 'shouting')]
    assert cc([('subject', 'ZEALOUS')])['problems'] == [(0, 'shouting')]
    assert cc([('subject', 'ΑΒΓΔ')])['problems'] == []                 # Greek uppercase is not A-Z
    assert cc([('subject', 'ＡＢＣＤ')])['problems'] == []               # fullwidth is not A-Z
    assert cc([('subject', 'ABC is here')])['problems'] == []          # 3 letters, under the 4-letter floor
    assert cc([('subject', 'ÉÉÉÉ')])['problems'] == []                 # the rule is ASCII A-Z only
    assert cc([('subject', 'ÄÄÄÄ Ä')])['problems'] == []
    assert cc([('subject', 'AB1C defg')])['problems'] == []            # digits are not all-caps words
    assert cc([('button', 'BUY NOW CLICK HERE!!')])['problems'] == [(0, 'hype'), (0, 'shouting')]


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4060 + part)
    seen, clean = set(), 0
    words = ['hi', 'FREE', 'sale', 'NOW', 'AB1C', 'ok!', 'yes', 'DEAL', 'go', 'ABC',
                   'ÉÉÉÉ', 'ÄÄ', 'FRE3', 'NÖW', 'A.B.C', 'X123', '!!!!', 'GrÉÁT', 'ZZZZ', 'ΑΒΓΔ', 'ＡＢＣＤ']
    for _ in range(60):
        blocks = []
        for _ in range(rnd.randint(0, 6)):
            c = rnd.choice(list(CAPS))
            t = ' '.join(rnd.choice(words) for _ in range(rnd.randint(1, 40)))
            if rnd.random() < 0.3:
                t += '!!'
            blocks.append((c, t[:300] if len(t) > 300 else t))
        r = cc(blocks)
        assert r == oracle(blocks)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 3 and clean >= 2


def test_limits_accepted():
    blocks = [('post', 'x' * 280)] * 20
    r = cc(blocks)
    assert r == {'problems': [], 'channels': {'post': 20}, 'chars': 5600}
    cc([('subject', 'x' * 60), ('button', 'y' * 20)])
    cc([('button', 'x' * 300)])['problems'] == [(0, 'over_cap')]


def err(exc, msg, blocks):
    with pytest.raises(exc) as e:
        cc(blocks)
    assert str(e.value) == msg


CV = 'channel must be one of: button, headline, post, subject'
TL = 'text length must be 1 to 300 characters'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'blocks must be an exact list', bad)
    err(V, 'block count must be at most 20', [('post', 'x')] * 21)
    for bad in (None, ['post', 'x'], 'ab', TupleSub(('post', 'x')), 5):
        err(T, 'each block must be an exact tuple', [bad])
    for bad in ((), ('post',), ('post', 'x', 1)):
        err(V, 'each block must have 2 items', [bad])
    for bad in (None, 5, b'post', StrSub('post')):
        err(T, 'channel must be an exact string', [(bad, 'x')])
    for bad in ('', 'Story', 'SUBJECT', 'é', 'ｓ'):
        err(V, CV, [(bad, 'x')])
    for bad in (None, 5, b'x', StrSub('x')):
        err(T, 'text must be an exact string', [('post', bad)])
    for bad in ('', 'x' * 301):
        err(V, TL, [('post', bad)])


def _order(err):
    err(T, 'blocks must be an exact list', 'x')
    err(V, 'block count must be at most 20', [None] * 21)
    err(T, 'each block must be an exact tuple', [None, ('post',)])
    err(V, 'each block must have 2 items', [('post',), None])
    err(T, 'channel must be an exact string', [(5, 5)])
    err(V, CV, [('Story', 5)])
    err(T, 'text must be an exact string', [('post', 5)])
    err(V, TL, [('post', '')])
    err(T, 'channel must be an exact string', [('post', 'x'), (5, 5)])
    err(T, 'text must be an exact string', [('post', 'x'), ('post', 5)])


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


DISCLAIMER = ('NOT_CLAIMED: this checks caps and surface markers on supplied text. It does not say the copy converts, '
              'that the caps fit every brand, or that shouting never works. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.copywriting as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')
