import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import semantic_versioning as mod

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
    assert mod.SCOPE == 'PARTIAL: rule-based version bumping over supplied changes, no real release management'
    assert len(mod.NOT_CLAIMED) >= 4 and 'git tags' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_COMPONENT, mod.MAX_CHANGES) == (100, 100)


def _oracle(version, changes):
    """Independent: rebuild each step from the rule definitions."""
    major, minor, patch = version
    versions = []
    for change in changes:
        if change == 'breaking':
            major += 1
            minor = 0
            patch = 0
        elif change == 'feature':
            minor += 1
            patch = 0
        else:
            patch += 1
        versions.append((major, minor, patch))
    return {'versions': versions, 'final': (major, minor, patch)}


def _core(m):
    # fix bumps patch only
    assert m.bump((1, 2, 3), ['fix']) == {'versions': [(1, 2, 4)], 'final': (1, 2, 4)}
    # feature bumps minor and resets patch
    assert m.bump((1, 2, 3), ['feature']) == {'versions': [(1, 3, 0)], 'final': (1, 3, 0)}
    # breaking bumps major and resets both
    assert m.bump((1, 2, 3), ['breaking']) == {'versions': [(2, 0, 0)], 'final': (2, 0, 0)}
    # resets cascade through a chain
    assert m.bump((1, 2, 3), ['fix', 'feature', 'fix', 'breaking']) == {
        'versions': [(1, 2, 4), (1, 3, 0), (1, 3, 1), (2, 0, 0)], 'final': (2, 0, 0)}
    # no changes: the version stands
    assert m.bump([0, 0, 0], []) == {'versions': [], 'final': (0, 0, 0)}
    # a feature after breaking starts from the reset line
    assert m.bump((3, 0, 0), ['breaking', 'feature'])['final'] == (4, 1, 0)
    # tuples accepted for both arguments
    assert m.bump((1, 0, 0), ('fix', 'fix'))['final'] == (1, 0, 2)
    # bumped components may pass the input cap
    assert m.bump((100, 100, 100), ['fix', 'feature', 'breaking'])['final'] == (101, 0, 0)
    rng = random.Random(700)
    for _ in range(400):
        version = (rng.randint(0, 20), rng.randint(0, 20), rng.randint(0, 20))
        changes = [rng.choice(['breaking', 'feature', 'fix']) for _ in range(rng.randint(0, 12))]
        assert m.bump(version, changes) == _oracle(version, changes)


def _late(m):
    VER = 'version must be a list or tuple'
    ROW = 'version must be a (major, minor, patch) row'
    COMP = 'version components must be nonbool integers between 0 and 100'
    CHG = 'changes must be a list or tuple'
    CAP = 'changes must contain at most 100 rows'
    KIND = 'changes must be the strings breaking, feature, or fix'
    good = (1, 2, 3)
    for bad in ('123', None, 5, {}, L([1, 2, 3]), T((1, 2, 3)), L(), T()):
        _raises(TypeError, VER, m.bump, bad, [])
    for bad in ((1, 2), (1, 2, 3, 4), ()):
        _raises(ValueError, ROW, m.bump, bad, [])
    for bad in (-1, 101, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, COMP, m.bump, (bad, 2, 3), [])
        _raises(ValueError, COMP, m.bump, (1, bad, 3), [])
        _raises(ValueError, COMP, m.bump, (1, 2, bad), [])
    assert m.bump((0, 0, 0), [])['final'] == (0, 0, 0)
    assert m.bump((100, 100, 100), [])['final'] == (100, 100, 100)
    for bad in ('ab', None, 5, {}, L(['fix']), T(['fix']), L(), T()):
        _raises(TypeError, CHG, m.bump, good, bad)
    _raises(TypeError, CHG, m.bump, good, L(['fix'] * 101))      # subclass refused before the cap
    _raises(ValueError, CAP, m.bump, good, ['fix'] * 101)
    assert m.bump(good, ['fix'] * 100)['final'] == (1, 2, 103)
    for bad in ('', 'major', 'feat', 'Fix', None, 5, b'fix', S('fix'), LyingS('fix'), ('fix',)):
        _raises(ValueError, KIND, m.bump, good, [bad])
        _raises(ValueError, KIND, m.bump, good, ['fix', bad])
    # order: version container, shape, components, changes container, cap, change strings
    _raises(TypeError, VER, m.bump, L([1, 2, 3]), L(['fix']))
    _raises(ValueError, ROW, m.bump, (1, 2), L(['fix']))
    _raises(ValueError, COMP, m.bump, (I(1), 2, 3), L(['fix']))
    _raises(ValueError, COMP, m.bump, (1, 2, I(3)), ['bogus'])
    _raises(TypeError, CHG, m.bump, good, L(['bogus'] * 101))
    _raises(ValueError, CAP, m.bump, good, ['bogus'] * 101)


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    changes = ['fix', 'feature']
    r = mod.bump([1, 2, 3], changes)
    r['versions'].append((9, 9, 9))
    assert changes == ['fix', 'feature']
    assert mod.bump([1, 2, 3], changes)['final'] == (1, 3, 0)


MUTANTS = [
    ("    if type(version) not in (list, tuple):", "    if not isinstance(version, (list, tuple)):"),
    ("    if len(version) != 3:", "    if len(version) < 3:"),
    ("        if type(component) is not int or not 0 <= component <= MAX_COMPONENT:",
     "        if not isinstance(component, int) or not 0 <= component <= MAX_COMPONENT:"),
    ("not 0 <= component <= MAX_COMPONENT", "not 1 <= component <= MAX_COMPONENT"),
    ("not 0 <= component <= MAX_COMPONENT", "not 0 <= component < MAX_COMPONENT"),
    ("MAX_COMPONENT = 100", "MAX_COMPONENT = 101"),
    ("    if type(changes) not in (list, tuple):", "    if not isinstance(changes, (list, tuple)):"),
    ("    if len(changes) > MAX_CHANGES:", "    if len(changes) >= MAX_CHANGES:"),
    ("MAX_CHANGES = 100", "MAX_CHANGES = 101"),
    ("        if type(change) is not str or change not in ('breaking', 'feature', 'fix'):",
     "        if not isinstance(change, str) or change not in ('breaking', 'feature', 'fix'):"),
    ("or change not in ('breaking', 'feature', 'fix')",
     "or change not in ('breaking', 'feature')"),
    ("        if change == 'breaking':", "        if change == 'feature':"),
    ("        elif change == 'feature':", "        elif change == 'breaking':"),
    ("            major, minor, patch = major + 1, 0, 0", "            major, minor, patch = major + 1, minor, 0"),
    ("            major, minor, patch = major + 1, 0, 0", "            major, minor, patch = major + 1, 0, patch"),
    ("            minor, patch = minor + 1, 0", "            minor, patch = minor + 1, patch"),
    ("            patch = patch + 1", "            patch = patch + 2"),
    ("        versions.append((major, minor, patch))", "        versions.append((major, minor, patch + 1))"),
    ("    major, minor, patch = version", "    major, minor, patch = sorted(version)"),
    ("    return {'versions': versions, 'final': (major, minor, patch)}",
     "    return {'versions': versions, 'final': (major, minor, patch + 1)}"),
    ("    return {'versions': versions, 'final': (major, minor, patch)}",
     "    return {'versions': versions, 'final': versions[-1] if versions else version}"),
    ("'version must be a list or tuple'", "'version must be a sequence'"),
    ("'version must be a (major, minor, patch) row'", "'version must be a (major, minor, patch) tuple'"),
    ("'version components must be nonbool integers between 0 and 100'",
     "'version components must be integers between 0 and 100'"),
    ("'changes must be a list or tuple'", "'changes must be a sequence'"),
    ("'changes must contain at most 100 rows'", "'changes must contain at most 99 rows'"),
    ("'changes must be the strings breaking, feature, or fix'",
     "'changes must be the strings breaking, feature, or patch'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
