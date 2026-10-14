import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import computational_linguistics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PM = 'row 1: parser must be a string of 1 to 16 characters'
SM = 'row 1: sentence must be a string of 1 to 16 characters'
XM = 'row 1: score must be a nonbool integer between 1 and 9'


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
    assert section == ('grammar induction, parsing algorithms, treebank '
                       'validity, language understanding, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: parse scoring over supplied results'
    assert mod.NOT_CLAIMED == ('grammar induction', 'parsing algorithms',
                               'treebank validity', 'language understanding',
                               'production readiness')


def _expected(rows):
    solved = {}
    failed = {}
    for parser, sentence, score in rows:
        if parser not in solved:
            solved[parser] = {}
            failed[parser] = {}
        if score >= 7:
            solved[parser][sentence] = True
        if score <= 2:
            failed[parser][sentence] = True
    solves = {}
    failures = {}
    for parser in solved:
        solves[parser] = len(solved[parser])
        failures[parser] = len(failed[parser])
    sharp = sorted(parser for parser in failures if failures[parser] == 0)
    blunt = sorted(parser for parser in solves if solves[parser] == 0)
    best = None
    for parser in solves:
        if best is None:
            best = parser
        elif (solves[parser] > solves[best] or
              (solves[parser] == solves[best] and
               failures[parser] < failures[best])):
            best = parser
    return {'total': len(rows), 'solves': solves, 'failures': failures,
            'sharp': sharp, 'blunt': blunt, 'best': best}


def _core(m):
    # fixed pins, oracle seeded with row number 1893
    assert m.score_parses([('p1', 's1', 8), ('p1', 's2', 1),
                           ('p2', 's1', 7), ('p2', 's2', 7)]) == {
        'total': 4, 'solves': {'p1': 1, 'p2': 2},
        'failures': {'p1': 1, 'p2': 0},
        'sharp': ['p2'], 'blunt': [], 'best': 'p2'}
    # one middling row: sharp, blunt, and best at once
    assert m.score_parses([('p', 's', 5)]) == {
        'total': 1, 'solves': {'p': 0}, 'failures': {'p': 0},
        'sharp': ['p'], 'blunt': ['p'], 'best': 'p'}
    # boundary scores: 7 solves, 6 neither, 3 neither, 2 fails
    r = m.score_parses([('p', 'a', 7), ('p', 'b', 6), ('p', 'c', 3),
                        ('p', 'd', 2)])
    assert r['solves'] == {'p': 1} and r['failures'] == {'p': 1}
    # repeated solves of one sentence count once
    r = m.score_parses([('p', 's', 9), ('p', 's', 9)])
    assert r['solves'] == {'p': 1}
    # the same sentence can be both solved and failed across rows
    r = m.score_parses([('p', 's', 9), ('p', 's', 1)])
    assert r['solves'] == {'p': 1} and r['failures'] == {'p': 1}
    # equal solves: fewer failures breaks the tie
    r = m.score_parses([('p1', 's1', 8), ('p1', 's2', 1), ('p2', 's3', 9)])
    assert r['best'] == 'p2'
    # equal solves and failures: the first supplied stays best
    r = m.score_parses([('p1', 's', 8), ('p2', 't', 9)])
    assert r['best'] == 'p1'
    # more solves beats fewer failures
    r = m.score_parses([('p1', 'a', 8), ('p1', 'b', 8), ('p1', 'c', 1),
                        ('p2', 'd', 9)])
    assert r['best'] == 'p1'
    # dicts keep first-touch order
    r = m.score_parses([('z', 's', 1), ('a', 's', 2)])
    assert r['solves'] == {'z': 0, 'a': 0}
    # non-ASCII parsers and sentences follow the same rule
    r = m.score_parses([('Üser-9!', 'Ω-1', 9), ('q?7', 'Ω-1', 1)])
    assert r == {'total': 2, 'solves': {'Üser-9!': 1, 'q?7': 0},
                 'failures': {'Üser-9!': 0, 'q?7': 1}, 'sharp': ['Üser-9!'],
                 'blunt': ['q?7'], 'best': 'Üser-9!'}
    rng = random.Random(1893)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.score_parses(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.score_parses, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.score_parses, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.score_parses, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.score_parses, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (parser, sentence, score) triple',
            m.score_parses, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.score_parses, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.score_parses, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PM, m.score_parses, [(1, 'b', 1)])
    _raises(ValueError, PM, m.score_parses, [('', 'b', 1)])
    _raises(ValueError, PM, m.score_parses, [('x' * 17, 'b', 1)])
    _raises(ValueError, SM, m.score_parses, [('a', 1, 1)])
    _raises(ValueError, SM, m.score_parses, [('a', '', 1)])
    _raises(ValueError, SM, m.score_parses, [('a', 'x' * 17, 1)])
    _raises(ValueError, XM, m.score_parses, [('a', 'b', '1')])
    _raises(ValueError, XM, m.score_parses, [('a', 'b', 0)])
    _raises(ValueError, XM, m.score_parses, [('a', 'b', 10)])
    _raises(ValueError, XM, m.score_parses, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: parser must be a string of 1 to 16 characters',
            m.score_parses, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.score_parses, [('a', 'b', 1), ('c', 'd', 0)])
    # parser is validated before sentence, sentence before score
    _raises(ValueError, PM, m.score_parses, [('x' * 17, '', 0)])
    _raises(ValueError, SM, m.score_parses, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.score_parses, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.score_parses((('a', 'b', 1),)) == m.score_parses([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.score_parses([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.score_parses([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.score_parses([('a', 'b', 1)] * 60)['total'] == 60
    assert m.score_parses([('a', 'b', 9)])['solves'] == {'a': 1}
    # pre-seed pin: fresh accumulators only
    assert m.score_parses([('p', 'a', 9), ('q', 'b', 1), ('p', 'c', 8)]) == {
        'total': 3, 'solves': {'p': 2, 'q': 0}, 'failures': {'p': 0, 'q': 1},
        'sharp': ['p'], 'blunt': ['q'], 'best': 'p'}
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
        _raises(TypeError, P, m.score_parses, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (parser, sentence, score) triple',
                m.score_parses, [K(('a', 'b', 1))])
    _raises(ValueError, PM, m.score_parses, [(S('a'), 'b', 1)])
    _raises(ValueError, SM, m.score_parses, [('a', S('b'), 1)])
    _raises(ValueError, XM, m.score_parses, [('a', 'b', I(1))])
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
    ('type(parser) is not str', 'not isinstance(parser, str)'),
    ('type(sentence) is not str', 'not isinstance(sentence, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(parser) <= 16', 'not 1 <= len(parser) <= 17'),
    ('not 1 <= len(sentence) <= 16', 'not 1 <= len(sentence) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('        if score >= 7:', '        if score >= 8:'),
    ('        if score <= 2:', '        if score <= 1:'),
    ('if failures[parser] == 0', 'if failures[parser] == 1'),
    ('if solves[parser] == 0', 'if solves[parser] == 1'),
    ('solves[parser] > solves[best]', 'solves[parser] < solves[best]'),
    ('failures[parser] < failures[best]', 'failures[parser] > failures[best]'),
    ("'sharp': sharp", "'sharp': blunt"),
    ("'solves': solves", "'solves': failures"),
    ("'failures': failures", "'failures': solves"),
    ("'total': len(rows)", "'total': len(solves)"),
    ('        parser, sentence, score = row',
     '        sentence, parser, score = row'),
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
    assert mod.score_parses([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.score_parses([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.score_parses([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
