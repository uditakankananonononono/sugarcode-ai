import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import text_to_image_generation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PR = 'row 1: prompt must be a string of 1 to 16 characters'
SA = 'row 1: sampler must be a string of 1 to 16 characters'
ST = 'row 1: steps must be a nonbool integer between 1 and 9'


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
    assert section == ('diffusion scheduling, sampler theory, '
                       'prompt design, image safety, production readiness.')
    assert mod.SCOPE == 'PARTIAL: step reducing over supplied counts'
    assert mod.NOT_CLAIMED == ('diffusion scheduling', 'sampler theory',
                               'prompt design', 'image safety',
                               'production readiness')


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def _expected(rows):
    divisors = {}
    for prompt, sampler, steps in rows:
        if sampler not in divisors:
            divisors[sampler] = steps
        else:
            divisors[sampler] = _gcd(divisors[sampler], steps)
    aligned = sorted(s for s in divisors if divisors[s] > 1)
    tightest = None
    for sampler in divisors:
        if tightest is None or divisors[sampler] > divisors[tightest]:
            tightest = sampler
    return {'total': len(rows), 'divisors': divisors,
            'aligned': aligned, 'tightest': tightest}


def _core(m):
    # fixed pins, oracle seeded with row number 1927
    assert m.reduce_steps([('p', 's1', 4), ('p', 's1', 8), ('p', 's2', 3),
                           ('p', 's2', 5), ('p', 's3', 6)]) == {
        'total': 5, 'divisors': {'s1': 4, 's2': 1, 's3': 6},
        'aligned': ['s1', 's3'], 'tightest': 's3'}
    # a single row is its own divisor
    assert m.reduce_steps([('p', 's', 5)]) == {
        'total': 1, 'divisors': {'s': 5}, 'aligned': ['s'], 'tightest': 's'}
    # coprime steps align nothing
    assert m.reduce_steps([('a', 'x', 2), ('a', 'x', 3)]) == {
        'total': 2, 'divisors': {'x': 1}, 'aligned': [], 'tightest': 'x'}
    # the tightest tie goes to the first supplied sampler
    r = m.reduce_steps([('p', 'a', 6), ('p', 'b', 9),
                        ('p', 'a', 3), ('p', 'b', 6)])
    assert r['divisors'] == {'a': 3, 'b': 3} and r['tightest'] == 'a'
    # a gcd of 1 stays 1 no matter what follows
    r = m.reduce_steps([('a', 'x', 2), ('a', 'x', 3), ('a', 'x', 9)])
    assert r['divisors'] == {'x': 1}
    # dicts keep first-touch order
    r = m.reduce_steps([('z', 'b', 7), ('a', 'a', 2)])
    assert r['divisors'] == {'b': 7, 'a': 2}
    # non-ASCII samplers follow the same rule
    r = m.reduce_steps([('p', 'Üser-9!', 6), ('p', 'q?7', 4), ('p', 'Üser-9!', 9)])
    assert r == {'total': 3, 'divisors': {'Üser-9!': 3, 'q?7': 4},
                 'aligned': ['q?7', 'Üser-9!'], 'tightest': 'q?7'}
    # pre-seed pin: fresh accumulators only
    assert m.reduce_steps([('p', 'a', 9), ('p', 'a', 6),
                           ('p', 'b', 5), ('p', 'b', 7)]) == {
        'total': 4, 'divisors': {'a': 3, 'b': 1},
        'aligned': ['a'], 'tightest': 'a'}
    rng = random.Random(1927)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.reduce_steps(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.reduce_steps, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.reduce_steps, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.reduce_steps, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.reduce_steps, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (prompt, sampler, steps) triple',
            m.reduce_steps, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.reduce_steps, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.reduce_steps, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PR, m.reduce_steps, [(1, 'b', 1)])
    _raises(ValueError, PR, m.reduce_steps, [('', 'b', 1)])
    _raises(ValueError, PR, m.reduce_steps, [('x' * 17, 'b', 1)])
    _raises(ValueError, SA, m.reduce_steps, [('a', 1, 1)])
    _raises(ValueError, SA, m.reduce_steps, [('a', '', 1)])
    _raises(ValueError, SA, m.reduce_steps, [('a', 'x' * 17, 1)])
    _raises(ValueError, ST, m.reduce_steps, [('a', 'b', '1')])
    _raises(ValueError, ST, m.reduce_steps, [('a', 'b', 0)])
    _raises(ValueError, ST, m.reduce_steps, [('a', 'b', 10)])
    _raises(ValueError, ST, m.reduce_steps, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: prompt must be a string of 1 to 16 characters',
            m.reduce_steps, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: steps must be a nonbool integer between 1 and 9',
            m.reduce_steps, [('a', 'b', 1), ('c', 'd', 0)])
    # prompt is validated before sampler, sampler before steps
    _raises(ValueError, PR, m.reduce_steps, [('x' * 17, '', 0)])
    _raises(ValueError, SA, m.reduce_steps, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.reduce_steps, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.reduce_steps((('a', 'b', 1),)) == m.reduce_steps([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.reduce_steps([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.reduce_steps([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.reduce_steps([('a', 'b', 1)] * 60)['total'] == 60
    assert m.reduce_steps([('a', 'b', 9)])['divisors'] == {'b': 9}
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
        _raises(TypeError, P, m.reduce_steps, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (prompt, sampler, steps) triple',
                m.reduce_steps, [K(('a', 'b', 1))])
    _raises(ValueError, PR, m.reduce_steps, [(S('a'), 'b', 1)])
    _raises(ValueError, SA, m.reduce_steps, [('a', S('b'), 1)])
    _raises(ValueError, ST, m.reduce_steps, [('a', 'b', I(1))])
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
    ('type(prompt) is not str', 'not isinstance(prompt, str)'),
    ('type(sampler) is not str', 'not isinstance(sampler, str)'),
    ('type(steps) is not int', 'not isinstance(steps, int)'),
    ('not 1 <= len(prompt) <= 16', 'not 1 <= len(prompt) <= 17'),
    ('not 1 <= len(sampler) <= 16', 'not 1 <= len(sampler) <= 17'),
    ('not 1 <= steps <= 9', 'not 1 <= steps <= 10'),
    ('        a, b = b, a % b', '        a, b = b, a + b'),
    ('            divisors[sampler] = _gcd(divisors[sampler], steps)',
     '            divisors[sampler] = _gcd(divisors[sampler], steps + 1)'),
    ('            divisors[sampler] = _gcd(divisors[sampler], steps)',
     '            divisors[sampler] = steps'),
    ('if divisors[s] > 1', 'if divisors[s] > 2'),
    ('if tightest is None or divisors[sampler] > divisors[tightest]:',
     'if tightest is None or divisors[sampler] < divisors[tightest]:'),
    ("'divisors': divisors", "'divisors': {}"),
    ("'aligned': aligned", "'aligned': []"),
    ("'tightest': tightest", "'tightest': None"),
    ("'total': len(rows)", "'total': len(divisors)"),
    ('        prompt, sampler, steps = row',
     '        sampler, prompt, steps = row'),
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
    assert mod.reduce_steps([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.reduce_steps([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.reduce_steps([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
