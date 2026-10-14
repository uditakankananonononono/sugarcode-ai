import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import corpus_linguistics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TK = 'row 1: token must be a string of 1 to 16 characters'
GR = 'row 1: genre must be a string of 1 to 16 characters'
FQ = 'row 1: frequency must be a nonbool integer between 1 and 9'


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def test_disclaimer_text_exact():
    section = ' '.join(mod.__doc__.split('NOT_CLAIMED:', 1)[1].split())
    assert section == ('tokenization, concordance generation, '
                       'part-of-speech tagging, statistical significance, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: corpus tallying over supplied frequencies'
    assert mod.NOT_CLAIMED == ('tokenization', 'concordance generation',
                               'part-of-speech tagging',
                               'statistical significance',
                               'production readiness')


def _expected(rows):
    totals = {}
    best = {}
    leader = None
    for token, genre, frequency in rows:
        if genre not in totals:
            totals[genre] = 0
        totals[genre] += frequency
        if leader is None and totals[genre] >= 20:
            leader = genre
        if token not in best or frequency > best[token]:
            best[token] = frequency
    frontrunners = sorted(g for g in totals if totals[g] >= 20)
    richest = None
    for token in best:
        if richest is None or best[token] > best[richest]:
            richest = token
    return {'total': len(rows), 'totals': totals, 'leader': leader,
            'frontrunners': frontrunners, 'richest': richest}


def _core(m):
    # fixed pins, oracle seeded with row number 1894
    assert m.analyze_corpus([('water', 'news', 5), ('hund', 'news', 7),
                             ('water', 'blog', 9), ('hund', 'blog', 1)]) == {
        'total': 4, 'totals': {'news': 12, 'blog': 10}, 'leader': None,
        'frontrunners': [], 'richest': 'water'}
    # one row: no genre can lead
    assert m.analyze_corpus([('t', 'g', 5)]) == {
        'total': 1, 'totals': {'g': 5}, 'leader': None,
        'frontrunners': [], 'richest': 't'}
    # the leader is the first genre whose running total reaches 20
    r = m.analyze_corpus([('a', 'blog', 9), ('b', 'blog', 9), ('c', 'blog', 9),
                          ('d', 'news', 9), ('e', 'news', 9)])
    assert r == {'total': 5, 'totals': {'blog': 27, 'news': 18},
                 'leader': 'blog', 'frontrunners': ['blog'], 'richest': 'a'}
    # the same multiset reordered can crown a different leader
    r = m.analyze_corpus([('d', 'news', 9), ('e', 'news', 9), ('f', 'news', 9),
                          ('a', 'blog', 9), ('b', 'blog', 9)])
    assert r == {'total': 5, 'totals': {'news': 27, 'blog': 18},
                 'leader': 'news', 'frontrunners': ['news'], 'richest': 'd'}
    # frontrunners are sorted alphabetically, not by first touch
    r = m.analyze_corpus([('a', 'zz', 9), ('b', 'zz', 9), ('c', 'zz', 9),
                          ('d', 'aa', 9), ('e', 'aa', 9), ('f', 'aa', 9)])
    assert r['leader'] == 'zz' and r['frontrunners'] == ['aa', 'zz']
    # a final total of exactly 20 fronts, 19 does not
    r = m.analyze_corpus([('a', 'g', 9), ('b', 'g', 9), ('c', 'g', 2)])
    assert r['totals'] == {'g': 20} and r['frontrunners'] == ['g']
    r = m.analyze_corpus([('a', 'g', 9), ('b', 'g', 9), ('c', 'g', 1)])
    assert r['totals'] == {'g': 19} and r['frontrunners'] == []
    assert r['leader'] is None
    # the richest tie goes to the first supplied token
    assert m.analyze_corpus([('x', 'g', 9), ('y', 'h', 9)])['richest'] == 'x'
    # peak frequency per token, not first frequency
    r = m.analyze_corpus([('b', 'h', 9), ('a', 'g', 1), ('a', 'g', 9)])
    assert r['richest'] == 'b'
    r = m.analyze_corpus([('a', 'g', 1), ('a', 'g', 9), ('b', 'h', 9)])
    assert r['richest'] == 'a'
    # dicts keep first-touch order
    r = m.analyze_corpus([('z', 'b', 1), ('a', 'a', 2)])
    assert r['totals'] == {'b': 1, 'a': 2}
    # non-ASCII tokens and genres follow the same rule
    r = m.analyze_corpus([('Üser-9!', 'Ω-1', 9), ('Üser-9!', 'Ω-1', 9),
                          ('x.y,z', 'Ω-1', 9)])
    assert r == {'total': 3, 'totals': {'Ω-1': 27}, 'leader': 'Ω-1',
                 'frontrunners': ['Ω-1'], 'richest': 'Üser-9!'}
    rng = random.Random(1894)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.analyze_corpus(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.analyze_corpus, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.analyze_corpus, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.analyze_corpus, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.analyze_corpus, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (token, genre, frequency) triple',
            m.analyze_corpus, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.analyze_corpus, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.analyze_corpus, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TK, m.analyze_corpus, [(1, 'b', 1)])
    _raises(ValueError, TK, m.analyze_corpus, [('', 'b', 1)])
    _raises(ValueError, TK, m.analyze_corpus, [('x' * 17, 'b', 1)])
    _raises(ValueError, GR, m.analyze_corpus, [('a', 1, 1)])
    _raises(ValueError, GR, m.analyze_corpus, [('a', '', 1)])
    _raises(ValueError, GR, m.analyze_corpus, [('a', 'x' * 17, 1)])
    _raises(ValueError, FQ, m.analyze_corpus, [('a', 'b', '1')])
    _raises(ValueError, FQ, m.analyze_corpus, [('a', 'b', 0)])
    _raises(ValueError, FQ, m.analyze_corpus, [('a', 'b', 10)])
    _raises(ValueError, FQ, m.analyze_corpus, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: token must be a string of 1 to 16 characters',
            m.analyze_corpus, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: frequency must be a nonbool integer between 1 and 9',
            m.analyze_corpus, [('a', 'b', 1), ('c', 'd', 0)])
    # token is validated before genre, genre before frequency
    _raises(ValueError, TK, m.analyze_corpus, [('x' * 17, '', 0)])
    _raises(ValueError, GR, m.analyze_corpus, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.analyze_corpus, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.analyze_corpus((('a', 'b', 1),)) == m.analyze_corpus([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.analyze_corpus([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.analyze_corpus([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.analyze_corpus([('a', 'b', 1)] * 60)['total'] == 60
    assert m.analyze_corpus([('a', 'b', 9)])['totals'] == {'b': 9}
    # pre-seed pin: fresh accumulators only
    assert m.analyze_corpus([('p', 'news', 9), ('q', 'news', 9),
                             ('r', 'blog', 5)]) == {
        'total': 3, 'totals': {'news': 18, 'blog': 5}, 'leader': None,
        'frontrunners': [], 'richest': 'p'}
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def _sym(m):
    P = 'rows must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, P, m.analyze_corpus, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (token, genre, frequency) triple',
                m.analyze_corpus, [K(('a', 'b', 1))])
    _raises(ValueError, TK, m.analyze_corpus, [(S('a'), 'b', 1)])
    _raises(ValueError, GR, m.analyze_corpus, [('a', S('b'), 1)])
    _raises(ValueError, FQ, m.analyze_corpus, [('a', 'b', I(1))])
    return True


def battery(m):
    _core(m)
    _late(m)
    _sym(m)
    return True


MUTANTS = [
    ('type(rows) not in (list, tuple)', 'not isinstance(rows, (list, tuple))'),
    ('not 1 <= len(rows) <= 60', 'not 1 <= len(rows) <= 61'),
    ('not 1 <= len(rows) <= 60', 'not 0 <= len(rows) <= 60'),
    ('type(row) not in (list, tuple)', 'not isinstance(row, (list, tuple))'),
    ('len(row) != 3', 'len(row) != 2'),
    ('type(token) is not str', 'not isinstance(token, str)'),
    ('type(genre) is not str', 'not isinstance(genre, str)'),
    ('type(frequency) is not int', 'not isinstance(frequency, int)'),
    ('not 1 <= len(token) <= 16', 'not 1 <= len(token) <= 17'),
    ('not 1 <= len(genre) <= 16', 'not 1 <= len(genre) <= 17'),
    ('not 1 <= frequency <= 9', 'not 1 <= frequency <= 10'),
    ('        totals[genre] += frequency', '        totals[genre] += 1'),
    ('if leader is None and totals[genre] >= 20:',
     'if leader is None and totals[genre] >= 21:'),
    ('if leader is None and totals[genre] >= 20:',
     'if leader is not None and totals[genre] >= 20:'),
    ('if totals[g] >= 20', 'if totals[g] > 20'),
    ('if token not in best or frequency > best[token]:',
     'if token not in best or frequency < best[token]:'),
    ('if richest is None or best[token] > best[richest]:',
     'if richest is None or best[token] < best[richest]:'),
    ("'totals': totals", "'totals': best"),
    ("'frontrunners': frontrunners", "'frontrunners': []"),
    ("'total': len(rows)", "'total': len(totals)"),
    ('        token, genre, frequency = row',
     '        genre, token, frequency = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True


def test_gap_pin_exact_cap_acceptance():
    # gap sweep: exact-cap 16-char labels accepted in each label
    # position, and on a late row
    assert mod.analyze_corpus([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.analyze_corpus([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.analyze_corpus([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
