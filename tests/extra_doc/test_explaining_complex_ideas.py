import random
import re
import pytest
from sugarcode.extra_doc.explaining_complex_ideas import check_explainer as ce

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


KEYWORD = re.compile(r"[a-z0-9_]+")


def oracle(sentences, terms):
    probs = []
    first = {}
    for i, s in enumerate(sentences):
        keys = KEYWORD.findall(s.lower())
        if len(s.split()) > 30:
            probs.append((i, 'too_long'))
        hit = set()
        for t in terms:
            if t in keys:
                hit.add(t)
                if t not in first:
                    first[t] = i
        if len(hit) >= 3:
            probs.append((i, 'packed'))
    unexp = []
    for t in first:
        s = sentences[first[t]]
        if s.find('(') == -1 and 'means' not in KEYWORD.findall(s.lower()) and 'called' not in KEYWORD.findall(s.lower()):
            unexp.append(t)
    return {'problems': sorted(probs), 'unexplained': sorted(unexp),
            'first_use': {t: first[t] for t in sorted(first)}}


def test_hand_cases():
    assert ce([], []) == {'problems': [], 'unexplained': [], 'first_use': {}}
    r = ce(['Photosynthesis means turning light to sugar.', 'The chlorophyll does it.'],
           ['photosynthesis', 'chlorophyll'])
    assert r == {'problems': [], 'unexplained': ['chlorophyll'],
                 'first_use': {'chlorophyll': 1, 'photosynthesis': 0}}
    assert ce(['The chlorophyll (a pigment) does it.'], ['chlorophyll'])['unexplained'] == []
    assert ce(['A thing called chlorophyll does it.'], ['chlorophyll'])['unexplained'] == []
    assert ce(['CHLOROPHYLL does it.'], ['chlorophyll'])['first_use'] == {'chlorophyll': 0}
    assert ce(['chlorophyll, again'], ['chlorophyll'])['unexplained'] == ['chlorophyll']   # keyword, but no marker
    assert ce(['the chlorophylls do it'], ['chlorophyll'])['first_use'] == {}              # plural is not the term
    assert ce(['a ' * 29 + 'b'], [])['problems'] == []
    assert ce(['a ' * 30 + 'b'], [])['problems'] == [(0, 'too_long')]
    assert ce(['mitosis meiosis cytokinesis'], ['mitosis', 'meiosis', 'cytokinesis'])['problems'] == [(0, 'packed')]
    assert ce(['mitosis meiosis x'], ['mitosis', 'meiosis', 'cytokinesis'])['problems'] == []
    r = ce(['x chlorophyll', 'chlorophyll means green'], ['chlorophyll'])     # first use wins, even if later explained
    assert r['unexplained'] == ['chlorophyll'] and r['first_use'] == {'chlorophyll': 0}
    assert ce(['x', 'chlorophyll means green'], ['chlorophyll'])['unexplained'] == []
    assert ce(['x' * 300], [])['problems'] == []


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(7350 + part)
    terms = ['mitosis', 'meiosis', 'cytokinesis', 'chlorophyll', 'neuron', 'axon']
    bag = terms + ['means', 'called', 'the', 'a', 'cell', '(note)', 'splits,', 'fast!', 'why?']
    seen, clean = set(), 0
    for _ in range(60):
        sents = []
        for _ in range(rnd.randint(0, 7)):
            if rnd.random() < 0.25:
                n, pool = rnd.randint(31, 45), ('a', 'the', 'cell', 'it', 'we')
            else:
                n, pool = rnd.choice((1, 2, 3, rnd.randint(4, 14))), bag
            s = ' '.join(rnd.choice(pool) for _ in range(n))
            sents.append(s)
        use = [t for t in terms if rnd.random() < 0.7]
        r = ce(sents, use)
        assert r == oracle(sents, use)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 2 and clean > 5


def test_limits_accepted():
    sents = ['word ' * 29 + 'end'] * 60
    terms = ['t' + str(i) for i in range(20)]
    r = ce(sents, terms)
    assert r == {'problems': [], 'unexplained': [], 'first_use': {}}
    assert r['first_use'] == {}
    ce(['x' * 300], ['a' * 24])


def err(exc, msg, sentences, terms):
    with pytest.raises(exc) as e:
        ce(sentences, terms)
    assert str(e.value) == msg


SL = 'sentence length must be 1 to 300 characters'
ST = 'each sentence must be an exact string'
TM = 'term must be 1 to 24 lowercase identifier characters'
TT = 'each term must be an exact string'
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
NS = (None, 5, b'a', StrSub('a'))


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}, 5):
        err(T, 'sentences must be an exact list', bad, [])
    err(V, 'sentence count must be at most 60', ['ok'] * 61, [])
    for bad in (None, 5, b'a', StrSub('a'), ['a'], ('a',)):
        err(T, ST, [bad], [])
    for bad in ('', 'x' * 301):
        err(V, SL, [bad], [])
    for bad in (None, (), 'ab', ListSub([]), {}, 5):
        err(T, 'terms must be an exact list', [], bad)
    err(V, 'term count must be at most 20', [], ['a'] * 21)
    for bad in NS:
        err(T, TT, [], [bad])
    for bad in BAD:
        err(V, TM, [], [bad])


def _order(err):
    err(T, 'sentences must be an exact list', 'x', None)
    err(V, 'sentence count must be at most 60', [None] * 61, [None])
    err(T, ST, [None, ''], [None])
    err(V, SL, ['', None], [None])
    err(T, 'terms must be an exact list', ['ok'], None)
    err(V, 'term count must be at most 20', ['ok'], [None] * 21)
    err(T, TT, ['ok'], [None, 'A'])
    err(V, TM, ['ok'], ['A', None])
    err(T, ST, [5], None)
    err(V, TM, ['ok'], ['bad term'])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,s,t', _collect(_pins))
def test_pin(exc, msg, s, t):
    err(exc, msg, s, t)


@pytest.mark.parametrize('exc,msg,s,t', _collect(_order))
def test_order(exc, msg, s, t):
    err(exc, msg, s, t)
