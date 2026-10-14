import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import large_language_models as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PR = 'row 1: prompt must be a string of 1 to 16 characters'
MO = 'row 1: model must be a string of 1 to 16 characters'
SC = 'row 1: score must be a nonbool integer between 1 and 9'


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
    assert section == ('training, alignment, evaluation design, '
                       'deployment safety, production readiness.')
    assert mod.SCOPE == 'PARTIAL: deficit weighing over supplied scores'
    assert mod.NOT_CLAIMED == ('training', 'alignment', 'evaluation design',
                               'deployment safety', 'production readiness')


def _expected(rows):
    prompt_max = {}
    for prompt, model, score in rows:
        if prompt not in prompt_max or score > prompt_max[prompt]:
            prompt_max[prompt] = score
    deficits = {}
    for prompt, model, score in rows:
        if model not in deficits:
            deficits[model] = 0
        deficits[model] += prompt_max[prompt] - score
    off_peak = sorted(m for m in deficits if deficits[m] > 0)
    sharpest = None
    for model in deficits:
        if sharpest is None or deficits[model] < deficits[sharpest]:
            sharpest = model
    return {'total': len(rows), 'deficits': deficits,
            'off_peak': off_peak, 'sharpest': sharpest}


def _core(m):
    # fixed pins, oracle seeded with row number 1924
    assert m.weigh_deficits([('p1', 'm1', 9), ('p1', 'm2', 5),
                             ('p2', 'm1', 3), ('p2', 'm2', 8)]) == {
        'total': 4, 'deficits': {'m1': 5, 'm2': 4},
        'off_peak': ['m1', 'm2'], 'sharpest': 'm2'}
    # a lone row sets its own prompt best
    assert m.weigh_deficits([('p', 'm', 5)]) == {
        'total': 1, 'deficits': {'m': 0}, 'off_peak': [], 'sharpest': 'm'}
    # every model at the prompt best means no off-peak
    assert m.weigh_deficits([('p', 'a', 9), ('p', 'b', 9)]) == {
        'total': 2, 'deficits': {'a': 0, 'b': 0},
        'off_peak': [], 'sharpest': 'a'}
    # deficits are measured per prompt, not globally
    r = m.weigh_deficits([('p', 'a', 9), ('q', 'b', 9), ('q', 'a', 1)])
    assert r == {'total': 3, 'deficits': {'a': 8, 'b': 0},
                 'off_peak': ['a'], 'sharpest': 'b'}
    # the sharpest tie goes to the first supplied model
    r = m.weigh_deficits([('p', 'a', 5), ('q', 'b', 5),
                          ('p', 'b', 6), ('q', 'a', 6)])
    assert r['deficits'] == {'a': 1, 'b': 1} and r['sharpest'] == 'a'
    # dicts keep first-touch order
    r = m.weigh_deficits([('z', 'b', 1), ('a', 'a', 2)])
    assert r['deficits'] == {'b': 0, 'a': 0}
    # a prompt whose best is below 9 keeps its own ceiling
    r = m.weigh_deficits([('p1', 'a', 3), ('p1', 'b', 4)])
    assert r['deficits'] == {'a': 1, 'b': 0} and r['sharpest'] == 'b'
    # non-ASCII models follow the same rule
    r = m.weigh_deficits([('p', 'Üser-9!', 7), ('p', 'q?7', 9),
                          ('q', 'Üser-9!', 9)])
    assert r == {'total': 3, 'deficits': {'Üser-9!': 2, 'q?7': 0},
                 'off_peak': ['Üser-9!'], 'sharpest': 'q?7'}
    # pre-seed pin: fresh accumulators only
    assert m.weigh_deficits([('p', 'a', 9), ('p', 'b', 2),
                             ('q', 'b', 9), ('q', 'a', 2)]) == {
        'total': 4, 'deficits': {'a': 7, 'b': 7},
        'off_peak': ['a', 'b'], 'sharpest': 'a'}
    rng = random.Random(1924)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.weigh_deficits(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_deficits, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_deficits, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_deficits, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_deficits, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (prompt, model, score) triple',
            m.weigh_deficits, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.weigh_deficits, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.weigh_deficits, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PR, m.weigh_deficits, [(1, 'b', 1)])
    _raises(ValueError, PR, m.weigh_deficits, [('', 'b', 1)])
    _raises(ValueError, PR, m.weigh_deficits, [('x' * 17, 'b', 1)])
    _raises(ValueError, MO, m.weigh_deficits, [('a', 1, 1)])
    _raises(ValueError, MO, m.weigh_deficits, [('a', '', 1)])
    _raises(ValueError, MO, m.weigh_deficits, [('a', 'x' * 17, 1)])
    _raises(ValueError, SC, m.weigh_deficits, [('a', 'b', '1')])
    _raises(ValueError, SC, m.weigh_deficits, [('a', 'b', 0)])
    _raises(ValueError, SC, m.weigh_deficits, [('a', 'b', 10)])
    _raises(ValueError, SC, m.weigh_deficits, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: prompt must be a string of 1 to 16 characters',
            m.weigh_deficits, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.weigh_deficits, [('a', 'b', 1), ('c', 'd', 0)])
    # prompt is validated before model, model before score
    _raises(ValueError, PR, m.weigh_deficits, [('x' * 17, '', 0)])
    _raises(ValueError, MO, m.weigh_deficits, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_deficits, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.weigh_deficits((('a', 'b', 1),)) == m.weigh_deficits([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.weigh_deficits([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.weigh_deficits([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.weigh_deficits([('a', 'b', 1)] * 60)['total'] == 60
    assert m.weigh_deficits([('a', 'b', 9)])['deficits'] == {'b': 0}
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
        _raises(TypeError, P, m.weigh_deficits, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (prompt, model, score) triple',
                m.weigh_deficits, [K(('a', 'b', 1))])
    _raises(ValueError, PR, m.weigh_deficits, [(S('a'), 'b', 1)])
    _raises(ValueError, MO, m.weigh_deficits, [('a', S('b'), 1)])
    _raises(ValueError, SC, m.weigh_deficits, [('a', 'b', I(1))])
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
    ('type(model) is not str', 'not isinstance(model, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(prompt) <= 16', 'not 1 <= len(prompt) <= 17'),
    ('not 1 <= len(model) <= 16', 'not 1 <= len(model) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('if prompt not in prompt_max or score > prompt_max[prompt]:',
     'if prompt not in prompt_max or score < prompt_max[prompt]:'),
    ('        deficits[model] += prompt_max[prompt] - score',
     '        deficits[model] += prompt_max[prompt]'),
    ('        deficits[model] += prompt_max[prompt] - score',
     '        deficits[model] += prompt_max[prompt] + score'),
    ('if deficits[m] > 0', 'if deficits[m] > 1'),
    ('if sharpest is None or deficits[model] < deficits[sharpest]:',
     'if sharpest is None or deficits[model] > deficits[sharpest]:'),
    ("'deficits': deficits", "'deficits': prompt_max"),
    ("'off_peak': off_peak", "'off_peak': []"),
    ("'sharpest': sharpest", "'sharpest': None"),
    ("'total': len(rows)", "'total': len(deficits)"),
    ('        prompt, model, score = row',
     '        model, prompt, score = row'),
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
    assert mod.weigh_deficits([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.weigh_deficits([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.weigh_deficits([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
