import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import rhetoric as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


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
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
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


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingI(int):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: appeal counting over supplied rows, no real rhetoric'
    assert len(mod.NOT_CLAIMED) >= 4 and 'delivery' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_TEXT, mod.MODES) == (100, 60, ('ethos', 'pathos', 'logos'))


def _oracle(rows):
    """Independent: three counters, dominant by scanning canonical order."""
    ethos = 0
    pathos = 0
    logos = 0
    for text, mode in rows:
        if mode == 'ethos':
            ethos += 1
        elif mode == 'pathos':
            pathos += 1
        else:
            logos += 1
    dominant = None
    if rows:
        best = ethos
        dominant = 'ethos'
        if pathos > best:
            best = pathos
            dominant = 'pathos'
        if logos > best:
            dominant = 'logos'
    return {'ethos': ethos, 'pathos': pathos, 'logos': logos,
            'dominant': dominant, 'rows': len(rows)}


def _core(m):
    assert m.profile([('a', 'ethos'), ('b', 'pathos'), ('c', 'ethos')]) == {
        'ethos': 2, 'pathos': 1, 'logos': 0, 'dominant': 'ethos', 'rows': 3}
    # a pathos/logos tie breaks to pathos (canonical order, ethos absent)
    assert m.profile([('a', 'logos'), ('b', 'pathos')])['dominant'] == 'pathos'
    # an ethos/logos tie breaks to ethos
    assert m.profile([('a', 'logos'), ('b', 'ethos')])['dominant'] == 'ethos'
    # logos leads outright
    assert m.profile([('a', 'logos'), ('b', 'logos'), ('c', 'ethos')])['dominant'] == 'logos'
    # empty profiles have no dominant mode
    assert m.profile([]) == {'ethos': 0, 'pathos': 0, 'logos': 0,
                             'dominant': None, 'rows': 0}
    # the text does not affect the counts
    assert m.profile([('long text here', 'ethos'), ('x', 'ethos')])['ethos'] == 2
    # tuples accepted at every level
    assert m.profile((('a', 'ethos'),))['rows'] == 1
    rng = random.Random(748)
    for _ in range(400):
        rows = [('t%d' % n, rng.choice(['ethos', 'pathos', 'logos']))
                for n in range(rng.randint(0, 12))]
        assert m.profile(rows) == _oracle(rows)


def _late(m):
    APP = 'appeals must be a list or tuple'
    CAP = 'appeals must contain at most 100 rows'
    ROW = 'each appeal must be a (text, mode) row'
    TXT = 'text must be a string of 1 to 60 characters'
    MOD = 'mode must be ethos, pathos, or logos'
    good = [('a', 'ethos')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, APP, m.profile, bad)
    _raises(TypeError, APP, m.profile, L(good * 101))           # subclass refused before the cap
    _raises(ValueError, CAP, m.profile, good * 101)
    assert m.profile(good * 100)['rows'] == 100
    for bad in ('ae', 5, None, ('a',), ('a', 'ethos', 'x'), ()):
        _raises(ValueError, ROW, m.profile, [bad])
        _raises(ValueError, ROW, m.profile, [('a', 'ethos'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.profile, [K(('a', 'ethos'))])
    for bad in ('', 'x' * 61, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, TXT, m.profile, [(bad, 'ethos')])
        _raises(ValueError, TXT, m.profile, [('a', 'ethos'), (bad, 'logos')])
    for bad in ('', 'ETHOS', 'ethos ', 'logic', None, 5, S('ethos'), LyingS('ethos'), I(0)):
        _raises(ValueError, MOD, m.profile, [('a', bad)])
        _raises(ValueError, MOD, m.profile, [('a', 'ethos'), ('b', bad)])
    assert m.profile([('x' * 60, 'logos')])['logos'] == 1
    # order: container, cap, rows (shape, text, mode)
    _raises(TypeError, APP, m.profile, L(good))
    _raises(ValueError, CAP, m.profile, [('a', 'maybe')] * 101)
    _raises(ValueError, ROW, m.profile, [('a', 'ethos', 'x')])
    _raises(ValueError, TXT, m.profile, [(S('a'), 'ethos')])
    _raises(ValueError, MOD, m.profile, [('a', S('ethos'))])
    # the first bad row reports first
    _raises(ValueError, TXT, m.profile, [(5, 'maybe'), ('a', 'ethos', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    appeals = [('a', 'ethos'), ('b', 'pathos')]
    assert mod.profile(appeals)['dominant'] == 'ethos'
    assert appeals == [('a', 'ethos'), ('b', 'pathos')]
    assert mod.profile(appeals)['rows'] == 2


MUTANTS = [
    ("    if type(appeals) not in (list, tuple):", "    if not isinstance(appeals, (list, tuple)):"),
    ("    if len(appeals) > MAX_ROWS:", "    if len(appeals) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:",
     "        if not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT:"),
    ("not 1 <= len(text) <= MAX_TEXT", "not 1 <= len(text) < MAX_TEXT"),
    ("MAX_TEXT = 60", "MAX_TEXT = 61"),
    ("        if type(mode) is not str or mode not in MODES:",
     "        if not isinstance(mode, str) or mode not in MODES:"),
    ("mode not in MODES", "mode not in MODES[:2]"),
    ("MODES = ('ethos', 'pathos', 'logos')", "MODES = ('ethos', 'pathos')"),
    ("    counts = {'ethos': 0, 'pathos': 0, 'logos': 0}",
     "    counts = {'ethos': 1, 'pathos': 0, 'logos': 0}"),
    ("        counts[mode] += 1", "        counts[mode] += 2"),
    ("        counts[mode] += 1", "        counts['ethos'] += 1"),
    ("        dominant = max(MODES, key=lambda mode: counts[mode])",
     "        dominant = min(MODES, key=lambda mode: counts[mode])"),
    ("        dominant = max(MODES, key=lambda mode: counts[mode])",
     "        dominant = max(reversed(MODES), key=lambda mode: counts[mode])"),
    ("    if rows:\n        dominant", "    if len(rows) > 1:\n        dominant"),
    ("    for text, mode in rows:\n        counts[mode] += 1",
     "    for text, mode in rows[1:]:\n        counts[mode] += 1"),
    ("            'logos': counts['logos'], 'dominant': dominant, 'rows': len(rows)}",
     "            'logos': counts['logos'], 'dominant': dominant, 'rows': len(rows) + 1}"),
    ("'appeals must be a list or tuple'", "'appeals must be a sequence'"),
    ("'appeals must contain at most 100 rows'", "'appeals must contain at most 99 rows'"),
    ("'each appeal must be a (text, mode) row'", "'each appeal must be a (text, mode) tuple'"),
    ("'text must be a string of 1 to 60 characters'", "'text must be a string of 1 to 59 characters'"),
    ("'mode must be ethos, pathos, or logos'", "'mode must be ethos or pathos'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
