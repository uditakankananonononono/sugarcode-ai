import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import popular_culture as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
ME = 'row 1: meme must be a string of 1 to 16 characters'
PF = 'row 1: platform must be a string of 1 to 16 characters'
HE = 'row 1: heat must be a nonbool integer between 1 and 9'


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
    assert section == ('meme provenance, platform algorithms, '
                       'monetization, demographics, production readiness.')
    assert mod.SCOPE == 'PARTIAL: trend chasing over supplied heats'
    assert mod.NOT_CLAIMED == ('meme provenance', 'platform algorithms',
                               'monetization', 'demographics',
                               'production readiness')


def _expected(rows):
    totals = {}
    for meme, platform, heat in rows:
        if meme not in totals:
            totals[meme] = 0
        totals[meme] += heat
    running = {}
    halftime = {}
    last_rows = {}
    for pos, (meme, platform, heat) in enumerate(rows, 1):
        if meme not in running:
            running[meme] = 0
        running[meme] += heat
        if meme not in halftime and running[meme] * 2 > totals[meme]:
            halftime[meme] = pos
        last_rows[meme] = pos
    quickest = None
    for meme in halftime:
        if quickest is None or halftime[meme] < halftime[quickest]:
            quickest = meme
    slow_burn = sorted(m for m in halftime if halftime[m] == last_rows[m])
    return {'total': len(rows), 'halftime': halftime,
            'quickest': quickest, 'slow_burn': slow_burn}


def _core(m):
    # fixed pins, oracle seeded with row number 1918
    assert m.chase_trends([('m1', 'x', 2), ('m2', 'y', 9),
                           ('m1', 'z', 2), ('m1', 'w', 1)]) == {
        'total': 4, 'halftime': {'m1': 3, 'm2': 2},
        'quickest': 'm2', 'slow_burn': ['m2']}
    # a lone row crosses its own halftime at once
    assert m.chase_trends([('m', 'p', 5)]) == {
        'total': 1, 'halftime': {'m': 1}, 'quickest': 'm', 'slow_burn': ['m']}
    # exactly half is not yet past half
    r = m.chase_trends([('x', 'a', 1), ('y', 'b', 2), ('x', 'c', 9)])
    assert r == {'total': 3, 'halftime': {'x': 3, 'y': 2},
                 'quickest': 'y', 'slow_burn': ['x', 'y']}
    # an even split crosses only on the later half
    r = m.chase_trends([('p', 'a', 2), ('p', 'b', 2)])
    assert r['halftime'] == {'p': 2}
    # dicts keep first-touch order
    r = m.chase_trends([('z', 'b', 1), ('a', 'a', 2)])
    assert r['halftime'] == {'z': 1, 'a': 2}
    # non-ASCII memes follow the same rule
    r = m.chase_trends([('Üser-9!', 'a', 4), ('q?7', 'b', 1), ('Üser-9!', 'c', 4)])
    assert r == {'total': 3, 'halftime': {'Üser-9!': 3, 'q?7': 2},
                 'quickest': 'q?7', 'slow_burn': ['q?7', 'Üser-9!']}
    # pre-seed pin: fresh accumulators only
    assert m.chase_trends([('p', 'a', 1), ('q', 'b', 2),
                           ('p', 'c', 3), ('q', 'd', 4)]) == {
        'total': 4, 'halftime': {'p': 3, 'q': 4},
        'quickest': 'p', 'slow_burn': ['p', 'q']}
    rng = random.Random(1918)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.chase_trends(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.chase_trends, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.chase_trends, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.chase_trends, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.chase_trends, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (meme, platform, heat) triple',
            m.chase_trends, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.chase_trends, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.chase_trends, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, ME, m.chase_trends, [(1, 'b', 1)])
    _raises(ValueError, ME, m.chase_trends, [('', 'b', 1)])
    _raises(ValueError, ME, m.chase_trends, [('x' * 17, 'b', 1)])
    _raises(ValueError, PF, m.chase_trends, [('a', 1, 1)])
    _raises(ValueError, PF, m.chase_trends, [('a', '', 1)])
    _raises(ValueError, PF, m.chase_trends, [('a', 'x' * 17, 1)])
    _raises(ValueError, HE, m.chase_trends, [('a', 'b', '1')])
    _raises(ValueError, HE, m.chase_trends, [('a', 'b', 0)])
    _raises(ValueError, HE, m.chase_trends, [('a', 'b', 10)])
    _raises(ValueError, HE, m.chase_trends, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: meme must be a string of 1 to 16 characters',
            m.chase_trends, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: heat must be a nonbool integer between 1 and 9',
            m.chase_trends, [('a', 'b', 1), ('c', 'd', 0)])
    # meme is validated before platform, platform before heat
    _raises(ValueError, ME, m.chase_trends, [('x' * 17, '', 0)])
    _raises(ValueError, PF, m.chase_trends, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.chase_trends, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.chase_trends((('a', 'b', 1),)) == m.chase_trends([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.chase_trends([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.chase_trends([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.chase_trends([('a', 'b', 1)] * 60)['total'] == 60
    assert m.chase_trends([('a', 'b', 9)])['halftime'] == {'a': 1}
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
        _raises(TypeError, P, m.chase_trends, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (meme, platform, heat) triple',
                m.chase_trends, [K(('a', 'b', 1))])
    _raises(ValueError, ME, m.chase_trends, [(S('a'), 'b', 1)])
    _raises(ValueError, PF, m.chase_trends, [('a', S('b'), 1)])
    _raises(ValueError, HE, m.chase_trends, [('a', 'b', I(1))])
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
    ('type(meme) is not str', 'not isinstance(meme, str)'),
    ('type(platform) is not str', 'not isinstance(platform, str)'),
    ('type(heat) is not int', 'not isinstance(heat, int)'),
    ('not 1 <= len(meme) <= 16', 'not 1 <= len(meme) <= 17'),
    ('not 1 <= len(platform) <= 16', 'not 1 <= len(platform) <= 17'),
    ('not 1 <= heat <= 9', 'not 1 <= heat <= 10'),
    ('        totals[meme] += heat', '        totals[meme] += 1'),
    ('        running[meme] += heat', '        running[meme] += 1'),
    ('if meme not in halftime and running[meme] * 2 > totals[meme]:',
     'if meme not in halftime and running[meme] * 2 >= totals[meme]:'),
    ('        last_rows[meme] = pos', '        last_rows[meme] = 0'),
    ('if quickest is None or halftime[meme] < halftime[quickest]:',
     'if quickest is None or halftime[meme] > halftime[quickest]:'),
    ('if halftime[m] == last_rows[m]', 'if halftime[m] != last_rows[m]'),
    ("'halftime': halftime", "'halftime': running"),
    ("'quickest': quickest", "'quickest': None"),
    ("'slow_burn': slow_burn", "'slow_burn': []"),
    ("'total': len(rows)", "'total': len(halftime)"),
    ('        meme, platform, heat = row',
     '        platform, meme, heat = row'),
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
    assert mod.chase_trends([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.chase_trends([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.chase_trends([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
