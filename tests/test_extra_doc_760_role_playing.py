import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import role_playing as mod

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
    assert mod.SCOPE == 'PARTIAL: cast assignment over supplied rows, no real role play'
    assert len(mod.NOT_CLAIMED) >= 4 and 'acting' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME) == (50, 8)


def _core(m):
    assert m.assign([('hero', 'amy'), ('villain', 'bo')]) == {
        'cast': [('hero', 'amy'), ('villain', 'bo')], 'size': 2}
    assert m.assign([]) == {'cast': [], 'size': 0}
    # the cast keeps the given order, unsorted
    assert m.assign([('zz', 'a'), ('aa', 'b')])['cast'] == [('zz', 'a'), ('aa', 'b')]
    # one actor may hold many roles - no wait, one role each; a single row works
    assert m.assign([('narrator', 'cy')])['size'] == 1
    # a name may be both a role and an actor on different rows
    assert m.assign([('lead', 'sam'), ('sam', 'jo')])['size'] == 2
    # tuples accepted at every level
    assert m.assign((('hero', 'amy'),))['size'] == 1
    rng = random.Random(760)
    for _ in range(400):
        n = rng.randint(0, 8)
        roles = rng.sample(['r%d' % k for k in range(12)], n)
        actors = rng.sample(['a%d' % k for k in range(12)], n)
        rows = list(zip(roles, actors))
        assert m.assign(rows) == {'cast': rows, 'size': n}


def _late(m):
    RLS = 'roles must be a list or tuple'
    CAP = 'roles must contain at most 50 rows'
    ROW = 'each role must be a (role, actor) row'
    ROL = 'role must be a string of 1 to 8 characters'
    ACT = 'actor must be a string of 1 to 8 characters'
    DRR = 'each role may appear only once'
    DRA = 'each actor may play only one role'
    good = [('hero', 'amy')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, RLS, m.assign, bad)
    _raises(TypeError, RLS, m.assign, L(good * 51))             # subclass refused before the cap
    _raises(ValueError, CAP, m.assign, [('r%d' % n, 'a%d' % n) for n in range(51)])
    assert m.assign([('r%d' % n, 'a%d' % n) for n in range(50)])['size'] == 50
    for bad in ('ha', 5, None, ('hero',), ('hero', 'amy', 'x'), ()):
        _raises(ValueError, ROW, m.assign, [bad])
        _raises(ValueError, ROW, m.assign, [('hero', 'amy'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.assign, [K(('hero', 'amy'))])
    for bad in ('', 'x' * 9, None, 5, b'h', S('hero'), LyingS('hero'), I(1)):
        _raises(ValueError, ROL, m.assign, [(bad, 'amy')])
        _raises(ValueError, ROL, m.assign, [('hero', 'amy'), (bad, 'bo')])
    for bad in ('', 'x' * 9, None, 5, b'a', S('amy'), LyingS('amy'), I(1)):
        _raises(ValueError, ACT, m.assign, [('hero', bad)])
        _raises(ValueError, ACT, m.assign, [('hero', 'amy'), ('villain', bad)])
    assert m.assign([('x' * 8, 'y' * 8)])['size'] == 1
    assert m.assign([('x', 'y')])['size'] == 1                   # single-character names accepted
    _raises(ValueError, DRR, m.assign, [('hero', 'amy'), ('hero', 'bo')])
    _raises(ValueError, DRA, m.assign, [('hero', 'amy'), ('villain', 'amy')])
    _raises(ValueError, DRR, m.assign, [('hero', 'amy'), ('villain', 'bo'), ('hero', 'cy')])
    # order: container, cap, rows (shape, role, actor), then duplicates
    _raises(TypeError, RLS, m.assign, L(good))
    _raises(ValueError, CAP, m.assign, [('hero', 'amy')] * 51)
    _raises(ValueError, ROW, m.assign, [('hero', 'amy', 'x')])
    _raises(ValueError, ROL, m.assign, [(S('hero'), 'amy')])
    _raises(ValueError, ACT, m.assign, [('hero', S('amy'))])
    _raises(ValueError, ROL, m.assign, [('', ''), ('', '')])     # rows before duplicates
    _raises(ValueError, DRA, m.assign, [('hero', 'amy'), ('hero2', 'amy')])
    # an actor duplicate on an earlier row beats a role duplicate on a later one
    _raises(ValueError, DRA, m.assign, [('a', 'x'), ('b', 'x'), ('a', 'y')])
    # the first bad row reports first
    _raises(ValueError, ROL, m.assign, [(5, 6), ('hero', 'amy', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    roles = [('hero', 'amy'), ('villain', 'bo')]
    r = mod.assign(roles)
    r['cast'].append(('bogus', 'xx'))
    assert roles == [('hero', 'amy'), ('villain', 'bo')]
    assert mod.assign(roles)['cast'] == [('hero', 'amy'), ('villain', 'bo')]


MUTANTS = [
    ("    if type(roles) not in (list, tuple):", "    if not isinstance(roles, (list, tuple)):"),
    ("    if len(roles) > MAX_ROWS:", "    if len(roles) >= MAX_ROWS:"),
    ("MAX_ROWS = 50", "MAX_ROWS = 51"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(role) is not str or not 1 <= len(role) <= MAX_NAME:",
     "        if not isinstance(role, str) or not 1 <= len(role) <= MAX_NAME:"),
    ("not 1 <= len(role) <= MAX_NAME", "not 1 <= len(role) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(actor) is not str or not 1 <= len(actor) <= MAX_NAME:",
     "        if not isinstance(actor, str) or not 1 <= len(actor) <= MAX_NAME:"),
    ("        if role in seen_roles:", "        if role not in seen_roles:"),
    ("        if actor in seen_actors:", "        if actor not in seen_actors:"),
    ("        seen_roles.add(role)", "        seen_roles.add(actor)"),
    ("        seen_actors.add(actor)", "        seen_actors.add(role)"),
    ("    return {'cast': rows, 'size': len(rows)}", "    return {'cast': rows, 'size': len(rows) + 1}"),
    ("    return {'cast': rows, 'size': len(rows)}", "    return {'cast': sorted(rows), 'size': len(rows)}"),
    ("    return {'cast': rows, 'size': len(rows)}", "    return {'cast': list(reversed(rows)), 'size': len(rows)}"),
    ("    for role, actor in rows:\n        if role in seen_roles:",
     "    for role, actor in rows[:1]:\n        if role in seen_roles:"),
    ("    rows = []\n    for row in roles:", "    rows = [('zz', 'zz')]\n    for row in roles:"),
    ("'roles must be a list or tuple'", "'roles must be a sequence'"),
    ("'roles must contain at most 50 rows'", "'roles must contain at most 49 rows'"),
    ("'each role must be a (role, actor) row'", "'each role must be a (role, actor) tuple'"),
    ("'role must be a string of 1 to 8 characters'", "'role must be a string of 1 to 7 characters'"),
    ("'actor must be a string of 1 to 8 characters'", "'actor must be a string of 1 to 7 characters'"),
    ("'each role may appear only once'", "'each role may appear twice'"),
    ("'each actor may play only one role'", "'each actor may play one role'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
