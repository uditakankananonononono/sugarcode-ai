import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import facilitation as mod

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
    assert mod.SCOPE == 'PARTIAL: speaker turn counting over supplied names, no real facilitation'
    assert len(mod.NOT_CLAIMED) >= 4 and 'sentiment' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_TURNS, mod.MAX_NAME) == (100, 8)


def _oracle(turns):
    """Independent: count with a plain dict, share with a division loop."""
    counts = {}
    for turn in turns:
        counts[turn] = counts.get(turn, 0) + 1
    top = 0
    for count in counts.values():
        if count > top:
            top = count
    total = len(turns)
    share = 0
    if total:
        share = (top * 1000) // total
    return {'turns': sorted(counts.items()), 'total': total, 'max_share_per_mille': share}


def _core(m):
    assert m.review(['a', 'b', 'a', 'a']) == {
        'turns': [('a', 3), ('b', 1)], 'total': 4, 'max_share_per_mille': 750}
    assert m.review([]) == {'turns': [], 'total': 0, 'max_share_per_mille': 0}
    # speakers sort alphabetically, not by count or first appearance
    assert m.review(['zz', 'aa', 'mm'])['turns'] == [('aa', 1), ('mm', 1), ('zz', 1)]
    # a single speaker holds 1000 per mille
    assert m.review(['a', 'a', 'a'])['max_share_per_mille'] == 1000
    # an even split floors: 1 of 3 is 333
    assert m.review(['a', 'b', 'c'])['max_share_per_mille'] == 333
    # the share follows the largest speaker only
    assert m.review(['a', 'a', 'b', 'c'])['max_share_per_mille'] == 500
    # tuples accepted
    assert m.review(('a', 'b'))['total'] == 2
    rng = random.Random(742)
    for _ in range(400):
        turns = [rng.choice(['a', 'b', 'c', 'dd']) for _ in range(rng.randint(0, 15))]
        assert m.review(turns) == _oracle(turns)


def _late(m):
    TRN = 'turns must be a list or tuple'
    CAP = 'turns must contain at most 100 rows'
    STR = 'turns must be speaker names of 1 to 8 characters'
    good = ['a']
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, TRN, m.review, bad)
    _raises(TypeError, TRN, m.review, L(good * 101))             # subclass refused before the cap
    _raises(ValueError, CAP, m.review, good * 101)
    assert m.review(good * 100)['total'] == 100
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1), ('a',)):
        _raises(ValueError, STR, m.review, [bad])
        _raises(ValueError, STR, m.review, ['a', bad])
    assert m.review(['x' * 8])['total'] == 1
    # order: container, cap, strings
    _raises(TypeError, TRN, m.review, L(good))
    _raises(ValueError, CAP, m.review, [5] * 101)
    _raises(ValueError, STR, m.review, [S('a')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    turns = ['a', 'b', 'a']
    r = mod.review(turns)
    r['turns'].append(('bogus', 9))
    assert turns == ['a', 'b', 'a']
    assert mod.review(turns)['turns'] == [('a', 2), ('b', 1)]


MUTANTS = [
    ("    if type(turns) not in (list, tuple):", "    if not isinstance(turns, (list, tuple)):"),
    ("    if len(turns) > MAX_TURNS:", "    if len(turns) >= MAX_TURNS:"),
    ("MAX_TURNS = 100", "MAX_TURNS = 101"),
    ("        if type(turn) is not str or not 1 <= len(turn) <= MAX_NAME:",
     "        if not isinstance(turn, str) or not 1 <= len(turn) <= MAX_NAME:"),
    ("not 1 <= len(turn) <= MAX_NAME", "not 1 <= len(turn) < MAX_NAME"),
    ("not 1 <= len(turn) <= MAX_NAME", "not 0 <= len(turn) <= MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("    counts = {}", "    counts = []"),
    ("        counts[turn] = counts.get(turn, 0) + 1", "        counts[turn] = counts.get(turn, 0) + 2"),
    ("        counts[turn] = counts.get(turn, 0) + 1", "        counts[turn] = counts.get(turn, 1) + 1"),
    ("    total = len(turns)", "    total = len(counts)"),
    ("    top = max(counts.values()) if counts else 0",
     "    top = min(counts.values()) if counts else 0"),
    # the else guard protects only the empty case - pin it via the guard itself
    ("    top = max(counts.values()) if counts else 0",
     "    top = max(counts.values())"),
    ("    return {'turns': sorted(counts.items()), 'total': total,",
     "    return {'turns': sorted(counts.items(), key=lambda kv: kv[1]), 'total': total,"),
    ("    return {'turns': sorted(counts.items()), 'total': total,",
     "    return {'turns': sorted(counts.items(), reverse=True), 'total': total,"),
    ("            'max_share_per_mille': top * 1000 // total if total else 0}",
     "            'max_share_per_mille': top * 100 // total if total else 0}"),
    ("            'max_share_per_mille': top * 1000 // total if total else 0}",
     "            'max_share_per_mille': top * 1000 // total if total else 1}"),
    ("            'max_share_per_mille': top * 1000 // total if total else 0}",
     "            'max_share_per_mille': top * 1000 // (total + 1) if total else 0}"),
    ("    counts = {}\n    for turn in turns:", "    counts = {}\n    for turn in turns[:5]:"),
    ("'turns must be a list or tuple'", "'turns must be a sequence'"),
    ("'turns must contain at most 100 rows'", "'turns must contain at most 99 rows'"),
    ("'turns must be speaker names of 1 to 8 characters'",
     "'turns must be speaker names of 1 to 7 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
