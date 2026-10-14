import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import release_notes as mod

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
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __ne__(self, o): return False
    def __eq__(self, o): return True
    __hash__ = int.__hash__


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: entry grouping and title formatting over supplied data, no real release tooling'
    assert len(mod.NOT_CLAIMED) >= 4 and 'git tags' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_COMPONENT, mod.MAX_ENTRIES, mod.MAX_TEXT) == (100, 100, 40)


def _oracle(version, entries):
    """Independent: three explicit loops, title from parts."""
    major, minor, patch = version
    breaking = []
    features = []
    fixes = []
    for kind, text in entries:
        if kind == 'breaking':
            breaking.append(text)
        elif kind == 'feature':
            features.append(text)
        else:
            fixes.append(text)
    title = 'Release ' + str(major) + '.' + str(minor) + '.' + str(patch)
    return {'title': title, 'breaking': breaking, 'features': features, 'fixes': fixes,
            'upgrade_required': len(breaking) > 0}


def _core(m):
    # groups split by kind, supplied order kept inside each list
    assert m.draft((1, 2, 3), [('fix', 'f1'), ('breaking', 'b1'), ('feature', 'x1'),
                               ('fix', 'f2')]) == {
        'title': 'Release 1.2.3', 'breaking': ['b1'], 'features': ['x1'],
        'fixes': ['f1', 'f2'], 'upgrade_required': True}
    # no entries: empty lists, no upgrade
    assert m.draft([0, 1, 0], []) == {'title': 'Release 0.1.0', 'breaking': [],
                                      'features': [], 'fixes': [], 'upgrade_required': False}
    # upgrade_required follows the breaking list exactly
    assert m.draft((2, 0, 0), [('feature', 'x')])['upgrade_required'] is False
    assert m.draft((2, 0, 0), [('breaking', 'b')])['upgrade_required'] is True
    # multi-digit components render without padding
    assert m.draft((10, 20, 100), [])['title'] == 'Release 10.20.100'
    # tuples accepted at every level
    assert m.draft((1, 0, 0), (('fix', 'f'),))['fixes'] == ['f']
    rng = random.Random(702)
    for _ in range(400):
        version = (rng.randint(0, 20), rng.randint(0, 20), rng.randint(0, 20))
        entries = [(rng.choice(['breaking', 'feature', 'fix']), 't%d' % rng.randint(0, 99))
                   for _ in range(rng.randint(0, 12))]
        assert m.draft(version, entries) == _oracle(version, entries)


def _late(m):
    VER = 'version must be a list or tuple'
    ROW = 'version must be a (major, minor, patch) row'
    COMP = 'version components must be nonbool integers between 0 and 100'
    ENT = 'entries must be a list or tuple'
    CAP = 'entries must contain at most 100 rows'
    EROW = 'each entry must be a (kind, text) row'
    KIND = 'kind must be the string breaking, feature, or fix'
    TXT = 'text must be a string of 1 to 40 characters'
    good = (1, 2, 3)
    entries = [('fix', 'f')]
    for bad in ('123', None, 5, {}, L([1, 2, 3]), T((1, 2, 3)), L(), T()):
        _raises(TypeError, VER, m.draft, bad, [])
    for bad in ((1, 2), (1, 2, 3, 4), ()):
        _raises(ValueError, ROW, m.draft, bad, [])
    for bad in (-1, 101, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, COMP, m.draft, (bad, 2, 3), [])
        _raises(ValueError, COMP, m.draft, (1, bad, 3), [])
        _raises(ValueError, COMP, m.draft, (1, 2, bad), [])
    assert m.draft((0, 0, 0), [])['title'] == 'Release 0.0.0'
    assert m.draft((100, 100, 100), [])['title'] == 'Release 100.100.100'
    for bad in ('ab', None, 5, {}, L(entries), T(entries), L(), T()):
        _raises(TypeError, ENT, m.draft, good, bad)
    _raises(TypeError, ENT, m.draft, good, L(entries * 101))     # subclass refused before the cap
    _raises(ValueError, CAP, m.draft, good, entries * 101)
    assert len(m.draft(good, entries * 100)['fixes']) == 100
    for K in (L, T):
        for bad in (K(('fix', 'f')), K(('fix',))):
            _raises(ValueError, EROW, m.draft, good, [bad])
    for bad in ('fixf', 5, None, ('fix',), ('fix', 'f', 'x'), ()):
        _raises(ValueError, EROW, m.draft, good, [bad])
        _raises(ValueError, EROW, m.draft, good, [('fix', 'f'), bad])
    for bad in ('', 'bug', 'Fix', None, 5, b'fix', S('fix'), LyingS('fix'), ('fix',)):
        _raises(ValueError, KIND, m.draft, good, [(bad, 'f')])
        _raises(ValueError, KIND, m.draft, good, [('fix', 'f'), (bad, 'g')])
    for bad in ('', 'x' * 41, None, 5, b'f', S('f'), LyingS('f'), I(1)):
        _raises(ValueError, TXT, m.draft, good, [('fix', bad)])
        _raises(ValueError, TXT, m.draft, good, [('fix', 'f'), ('fix', bad)])
    assert m.draft(good, [('fix', 'x' * 40)])['fixes'] == ['x' * 40]
    # order: version container, shape, components, entries container, cap, rows (shape, kind, text)
    _raises(TypeError, VER, m.draft, L([1, 2, 3]), L(entries))
    _raises(ValueError, ROW, m.draft, (1, 2), L(entries))
    _raises(ValueError, COMP, m.draft, (1, 2, I(3)), L(entries))
    _raises(TypeError, ENT, m.draft, good, L(entries * 101))
    _raises(ValueError, CAP, m.draft, good, [('bogus', 5)] * 101)
    _raises(ValueError, EROW, m.draft, good, [('fix', 'f', 'x')])
    _raises(ValueError, KIND, m.draft, good, [(S('fix'), 'f')])
    _raises(ValueError, TXT, m.draft, good, [('fix', S('f'))])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    entries = [('fix', 'f1'), ('breaking', 'b1')]
    r = mod.draft([1, 2, 3], entries)
    r['fixes'].append('bogus')
    assert entries == [('fix', 'f1'), ('breaking', 'b1')]
    assert mod.draft([1, 2, 3], entries)['fixes'] == ['f1']


MUTANTS = [
    ("    if type(version) not in (list, tuple):", "    if not isinstance(version, (list, tuple)):"),
    ("    if len(version) != 3:", "    if len(version) < 3:"),
    ("        if type(component) is not int or not 0 <= component <= MAX_COMPONENT:",
     "        if not isinstance(component, int) or not 0 <= component <= MAX_COMPONENT:"),
    ("not 0 <= component <= MAX_COMPONENT", "not 1 <= component <= MAX_COMPONENT"),
    ("MAX_COMPONENT = 100", "MAX_COMPONENT = 101"),
    ("    if type(entries) not in (list, tuple):", "    if not isinstance(entries, (list, tuple)):"),
    ("    if len(entries) > MAX_ENTRIES:", "    if len(entries) >= MAX_ENTRIES:"),
    ("MAX_ENTRIES = 100", "MAX_ENTRIES = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(kind) is not str or kind not in ('breaking', 'feature', 'fix'):",
     "        if not isinstance(kind, str) or kind not in ('breaking', 'feature', 'fix'):"),
    ("or kind not in ('breaking', 'feature', 'fix')", "or kind not in ('breaking', 'feature')"),
    ("        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:",
     "        if not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT:"),
    ("not 1 <= len(text) <= MAX_TEXT", "not 1 <= len(text) < MAX_TEXT"),
    ("MAX_TEXT = 40", "MAX_TEXT = 41"),
    ("    breaking = [text for kind, text in rows if kind == 'breaking']",
     "    breaking = [text for kind, text in rows if kind == 'feature']"),
    ("    features = [text for kind, text in rows if kind == 'feature']",
     "    features = [text for kind, text in rows]"),
    ("    fixes = [text for kind, text in rows if kind == 'fix']",
     "    fixes = [text for kind, text in rows if kind != 'fix']"),
    ("    return {'title': 'Release %d.%d.%d' % (major, minor, patch),",
     "    return {'title': 'Release %d.%d.%d' % (major, minor, patch + 1),"),
    ("    return {'title': 'Release %d.%d.%d' % (major, minor, patch),",
     "    return {'title': 'release %d.%d.%d' % (major, minor, patch),"),
    ("    return {'title': 'Release %d.%d.%d' % (major, minor, patch),",
     "    return {'title': 'Release %d.%d' % (major, minor),"),
    ("            'upgrade_required': len(breaking) > 0}",
     "            'upgrade_required': len(breaking) >= 0}"),
    ("            'upgrade_required': len(breaking) > 0}",
     "            'upgrade_required': len(breaking) > 1}"),
    ("'version must be a list or tuple'", "'version must be a sequence'"),
    ("'version components must be nonbool integers between 0 and 100'",
     "'version components must be integers between 0 and 100'"),
    ("'entries must be a list or tuple'", "'entries must be a sequence'"),
    ("'entries must contain at most 100 rows'", "'entries must contain at most 99 rows'"),
    ("'kind must be the string breaking, feature, or fix'",
     "'kind must be the string breaking or feature'"),
    ("'text must be a string of 1 to 40 characters'", "'text must be a string of 1 to 39 characters'"),
    ("'each entry must be a (kind, text) row'", "'each entry must be a (kind, text) tuple'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
