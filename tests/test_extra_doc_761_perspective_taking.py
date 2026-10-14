import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import perspective_taking as mod

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
    assert mod.SCOPE == 'PARTIAL: stance tallying over supplied rows, no real perspective taking'
    assert len(mod.NOT_CLAIMED) >= 4 and 'negotiation' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_VIEWER, mod.STANCES) == (100, 8, ('for', 'neutral', 'against'))


def _oracle(rows):
    """Independent: three counters, majority by strict halving."""
    for_count = 0
    neutral = 0
    against = 0
    for viewer, stance in rows:
        if stance == 'for':
            for_count += 1
        elif stance == 'neutral':
            neutral += 1
        else:
            against += 1
    total = len(rows)
    majority = None
    if for_count > total - for_count:
        majority = 'for'
    elif neutral > total - neutral:
        majority = 'neutral'
    elif against > total - against:
        majority = 'against'
    return {'for': for_count, 'neutral': neutral, 'against': against,
            'majority': majority, 'total': total}


def _core(m):
    assert m.gather([('a', 'for'), ('b', 'against'), ('c', 'for')]) == {
        'for': 2, 'neutral': 0, 'against': 1, 'majority': 'for', 'total': 3}
    # an even split has no majority
    assert m.gather([('a', 'for'), ('b', 'against')])['majority'] is None
    # exactly half is not a majority
    assert m.gather([('a', 'for'), ('b', 'for'), ('c', 'against'), ('d', 'against')])['majority'] is None
    # neutral can hold the majority
    assert m.gather([('a', 'neutral'), ('b', 'neutral'), ('c', 'for')])['majority'] == 'neutral'
    # against can hold the majority
    assert m.gather([('a', 'against'), ('b', 'against')])['majority'] == 'against'
    # empty has no majority
    assert m.gather([]) == {'for': 0, 'neutral': 0, 'against': 0,
                            'majority': None, 'total': 0}
    # a viewer named zz is not pre-seen
    assert m.gather([('zz', 'for')])['majority'] == 'for'
    # one viewer is always a majority
    assert m.gather([('a', 'against')])['majority'] == 'against'
    # tuples accepted at every level
    assert m.gather((('a', 'for'),))['total'] == 1
    rng = random.Random(761)
    for _ in range(400):
        n = rng.randint(0, 9)
        viewers = rng.sample(['v%d' % k for k in range(12)], n)
        rows = [(viewer, rng.choice(['for', 'neutral', 'against'])) for viewer in viewers]
        assert m.gather(rows) == _oracle(rows)


def _late(m):
    VWS = 'views must be a list or tuple'
    CAP = 'views must contain at most 100 rows'
    ROW = 'each view must be a (viewer, stance) row'
    VWR = 'viewer must be a string of 1 to 8 characters'
    STN = 'stance must be for, neutral, or against'
    DUP = 'each viewer may appear only once'
    good = [('a', 'for')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, VWS, m.gather, bad)
    _raises(TypeError, VWS, m.gather, L(good * 101))            # subclass refused before the cap
    _raises(ValueError, CAP, m.gather, [('v%d' % n, 'for') for n in range(101)])
    assert m.gather([('v%d' % n, 'for') for n in range(100)])['total'] == 100
    for bad in ('af', 5, None, ('a',), ('a', 'for', 'x'), ()):
        _raises(ValueError, ROW, m.gather, [bad])
        _raises(ValueError, ROW, m.gather, [('a', 'for'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.gather, [K(('a', 'for'))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, VWR, m.gather, [(bad, 'for')])
        _raises(ValueError, VWR, m.gather, [('a', 'for'), (bad, 'against')])
    for bad in ('', 'FOR', 'for ', 'yes', None, 5, S('for'), LyingS('for'), I(0)):
        _raises(ValueError, STN, m.gather, [('a', bad)])
        _raises(ValueError, STN, m.gather, [('a', 'for'), ('b', bad)])
    assert m.gather([('x' * 8, 'for')])['total'] == 1
    assert m.gather([('x', 'for')])['total'] == 1                # single-character viewer accepted
    _raises(ValueError, DUP, m.gather, [('a', 'for'), ('a', 'against')])
    _raises(ValueError, DUP, m.gather, [('a', 'for'), ('b', 'for'), ('a', 'for')])
    # order: container, cap, rows (shape, viewer, stance), then duplicates
    _raises(TypeError, VWS, m.gather, L(good))
    _raises(ValueError, CAP, m.gather, [('a', 'maybe')] * 101)
    _raises(ValueError, ROW, m.gather, [('a', 'for', 'x')])
    _raises(ValueError, VWR, m.gather, [(S('a'), 'for')])
    _raises(ValueError, STN, m.gather, [('a', S('for'))])
    _raises(ValueError, STN, m.gather, [('a', 'maybe'), ('a', 'maybe')])  # rows before duplicates
    # the first bad row reports first
    _raises(ValueError, VWR, m.gather, [(5, 'maybe'), ('a', 'for', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    views = [('a', 'for'), ('b', 'neutral')]
    assert mod.gather(views)['total'] == 2
    assert views == [('a', 'for'), ('b', 'neutral')]
    assert mod.gather(views)['for'] == 1


MUTANTS = [
    ("    if type(views) not in (list, tuple):", "    if not isinstance(views, (list, tuple)):"),
    ("    if len(views) > MAX_ROWS:", "    if len(views) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(viewer) is not str or not 1 <= len(viewer) <= MAX_VIEWER:",
     "        if not isinstance(viewer, str) or not 1 <= len(viewer) <= MAX_VIEWER:"),
    ("not 1 <= len(viewer) <= MAX_VIEWER", "not 1 <= len(viewer) < MAX_VIEWER"),
    ("MAX_VIEWER = 8", "MAX_VIEWER = 9"),
    ("        if type(stance) is not str or stance not in STANCES:",
     "        if not isinstance(stance, str) or stance not in STANCES:"),
    ("stance not in STANCES", "stance not in STANCES[:2]"),
    ("STANCES = ('for', 'neutral', 'against')", "STANCES = ('for', 'neutral')"),
    ("        if viewer in seen:", "        if viewer not in seen:"),
    ("        seen.add(viewer)", "        seen.add(stance)"),
    ("    counts = {'for': 0, 'neutral': 0, 'against': 0}",
     "    counts = {'for': 1, 'neutral': 0, 'against': 0}"),
    ("        counts[stance] += 1", "        counts[stance] += 2"),
    ("        counts[stance] += 1", "        counts['for'] += 1"),
    ("        if counts[stance] * 2 > total:", "        if counts[stance] * 2 >= total:"),
    ("        if counts[stance] * 2 > total:", "        if counts[stance] > total:"),
    ("            majority = stance", "            majority = 'for'"),
    ("    for viewer, stance in rows:\n        counts[stance] += 1",
     "    for viewer, stance in rows[1:]:\n        counts[stance] += 1"),
    ("            'against': counts['against'], 'majority': majority, 'total': total}",
     "            'against': counts['against'], 'majority': majority, 'total': total + 1}"),
    ("'views must be a list or tuple'", "'views must be a sequence'"),
    ("'views must contain at most 100 rows'", "'views must contain at most 99 rows'"),
    ("'each view must be a (viewer, stance) row'", "'each view must be a (viewer, stance) tuple'"),
    ("'viewer must be a string of 1 to 8 characters'", "'viewer must be a string of 1 to 7 characters'"),
    ("'stance must be for, neutral, or against'", "'stance must be for or neutral'"),
    ("'each viewer may appear only once'", "'each viewer may appear twice'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
