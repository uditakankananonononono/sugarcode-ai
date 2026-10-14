import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import comparative_linguistics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
WM = 'row 1: word must be a string of 1 to 16 characters'
LM = 'row 1: language must be a string of 1 to 16 characters'
SM = 'row 1: score must be a nonbool integer between 1 and 9'


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
    assert section == ('genetic relatedness, proto-languages, borrowing '
                       'detection, regular correspondence, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: cognate matching over supplied scores'
    assert mod.NOT_CLAIMED == ('genetic relatedness', 'proto-languages',
                               'borrowing detection',
                               'regular correspondence',
                               'production readiness')


def _expected(rows):
    marks = {}
    strength = {}
    for word, language, score in rows:
        if word not in marks:
            marks[word] = {}
            strength[word] = 0
        marks[word][score] = True
        strength[word] += score
    distinct = {}
    for word in marks:
        distinct[word] = len(marks[word])
    uniform = sorted(word for word in distinct if distinct[word] == 1)
    varied = sorted(word for word in distinct if distinct[word] >= 3)
    firmest = None
    for word in strength:
        if firmest is None or strength[word] > strength[firmest]:
            firmest = word
    return {'total': len(rows), 'distinct': distinct, 'uniform': uniform,
            'varied': varied, 'strength': strength, 'firmest': firmest}


def _core(m):
    # fixed pins, oracle seeded with row number 1892
    assert m.match_cognates([('water', 'eng', 5), ('water', 'deu', 5),
                             ('water', 'swe', 9), ('hund', 'deu', 7)]) == {
        'total': 4, 'distinct': {'water': 2, 'hund': 1},
        'uniform': ['hund'], 'varied': [],
        'strength': {'water': 19, 'hund': 7}, 'firmest': 'water'}
    # one row: the only word is uniform
    assert m.match_cognates([('w', 'l', 5)]) == {
        'total': 1, 'distinct': {'w': 1}, 'uniform': ['w'], 'varied': [],
        'strength': {'w': 5}, 'firmest': 'w'}
    # repeated scores do not add distinctness
    r = m.match_cognates([('w', 'a', 4), ('w', 'b', 4), ('w', 'c', 4)])
    assert r['distinct'] == {'w': 1} and r['uniform'] == ['w']
    # three distinct scores is varied, two is neither
    r = m.match_cognates([('w', 'a', 1), ('w', 'b', 5), ('w', 'c', 9)])
    assert r['distinct'] == {'w': 3} and r['varied'] == ['w']
    r = m.match_cognates([('w', 'a', 1), ('w', 'b', 9)])
    assert r['varied'] == [] and r['uniform'] == []
    # the same language can attest different scores
    r = m.match_cognates([('w', 'l', 1), ('w', 'l', 9)])
    assert r['distinct'] == {'w': 2}
    # the firmest tie goes to the first supplied
    r = m.match_cognates([('a', 'l', 5), ('b', 'l', 5)])
    assert r['firmest'] == 'a'
    # strength piles up across languages
    r = m.match_cognates([('w', 'a', 2), ('w', 'b', 3)])
    assert r['strength'] == {'w': 5}
    # dicts keep first-touch order
    r = m.match_cognates([('z', 'l', 1), ('a', 'l', 2)])
    assert r['strength'] == {'z': 1, 'a': 2}
    # non-ASCII words and languages follow the same rule
    r = m.match_cognates([('Üser-9!', 'Ω-1', 9), ('Üser-9!', 'q?7', 1)])
    assert r == {'total': 2, 'distinct': {'Üser-9!': 2}, 'uniform': [],
                 'varied': [], 'strength': {'Üser-9!': 10},
                 'firmest': 'Üser-9!'}
    rng = random.Random(1892)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.match_cognates(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.match_cognates, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.match_cognates, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.match_cognates, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.match_cognates, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (word, language, score) triple',
            m.match_cognates, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.match_cognates, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.match_cognates, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, WM, m.match_cognates, [(1, 'b', 1)])
    _raises(ValueError, WM, m.match_cognates, [('', 'b', 1)])
    _raises(ValueError, WM, m.match_cognates, [('x' * 17, 'b', 1)])
    _raises(ValueError, LM, m.match_cognates, [('a', 1, 1)])
    _raises(ValueError, LM, m.match_cognates, [('a', '', 1)])
    _raises(ValueError, LM, m.match_cognates, [('a', 'x' * 17, 1)])
    _raises(ValueError, SM, m.match_cognates, [('a', 'b', '1')])
    _raises(ValueError, SM, m.match_cognates, [('a', 'b', 0)])
    _raises(ValueError, SM, m.match_cognates, [('a', 'b', 10)])
    _raises(ValueError, SM, m.match_cognates, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: word must be a string of 1 to 16 characters',
            m.match_cognates, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.match_cognates, [('a', 'b', 1), ('c', 'd', 0)])
    # word is validated before language, language before score
    _raises(ValueError, WM, m.match_cognates, [('x' * 17, '', 0)])
    _raises(ValueError, LM, m.match_cognates, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.match_cognates, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.match_cognates((('a', 'b', 1),)) == m.match_cognates([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.match_cognates([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.match_cognates([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.match_cognates([('a', 'b', 1)] * 60)['total'] == 60
    assert m.match_cognates([('a', 'b', 9)])['strength'] == {'a': 9}
    # pre-seed pin: fresh accumulators only
    assert m.match_cognates([('p', 'a', 1), ('p', 'b', 9), ('q', 'c', 5)]) == {
        'total': 3, 'distinct': {'p': 2, 'q': 1}, 'uniform': ['q'],
        'varied': [], 'strength': {'p': 10, 'q': 5}, 'firmest': 'p'}
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
        _raises(TypeError, P, m.match_cognates, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (word, language, score) triple',
                m.match_cognates, [K(('a', 'b', 1))])
    _raises(ValueError, WM, m.match_cognates, [(S('a'), 'b', 1)])
    _raises(ValueError, LM, m.match_cognates, [('a', S('b'), 1)])
    _raises(ValueError, SM, m.match_cognates, [('a', 'b', I(1))])
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
    ('type(word) is not str', 'not isinstance(word, str)'),
    ('type(language) is not str', 'not isinstance(language, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(word) <= 16', 'not 1 <= len(word) <= 17'),
    ('not 1 <= len(language) <= 16', 'not 1 <= len(language) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('        strength[word] += score', '        strength[word] += 1'),
    ('if distinct[word] == 1', 'if distinct[word] == 2'),
    ('if distinct[word] >= 3', 'if distinct[word] >= 4'),
    ('if firmest is None or strength[word] > strength[firmest]:',
     'if firmest is None or strength[word] < strength[firmest]:'),
    ("'uniform': uniform", "'uniform': varied"),
    ("'distinct': distinct", "'distinct': strength"),
    ("'strength': strength", "'strength': distinct"),
    ("'total': len(rows)", "'total': len(strength)"),
    ('        word, language, score = row',
     '        language, word, score = row'),
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
    assert mod.match_cognates([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.match_cognates([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.match_cognates([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
