import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import postmortem_check as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


def _load(src):
    m = types.ModuleType('mutant')
    exec(compile(src, 'mutant', 'exec'), m.__dict__)
    return m


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
    def __hash__(self): return hash('web')


REQ = ['summary', 'timeline', 'impact', 'root_cause', 'actions']
ALL = REQ + ['lessons', 'followup', 'appendix']


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: completeness check of supplied post-mortem parts, no tracking or publishing'
    assert len(mod.NOT_CLAIMED) >= 4 and 'publishing' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(secs, items, day, md):
    """Independent: set difference and per-item arithmetic."""
    miss = [r for r in REQ if r not in set(secs)]
    late = [i for i, (o, d) in enumerate(items) if d > day + md]
    return {'missing': miss, 'complete': len(miss) == 0, 'late': late,
            'owners': sorted({o for o, _ in items}),
            'ready': len(miss) == 0 and len(items) >= 1 and late == []}


def _core(m):
    assert m.postmortem_check(REQ, [('ann', 10)]) == {'missing': [], 'complete': True, 'late': [], 'owners': ['ann'], 'ready': True}
    assert m.postmortem_check(ALL, [('ann', 30)])['ready'] is True
    assert m.postmortem_check(ALL, [('ann', 31)]) == {'missing': [], 'complete': True, 'late': [0], 'owners': ['ann'], 'ready': False}
    assert m.postmortem_check(ALL, [('ann', 31)], 0, 31)['late'] == []
    assert m.postmortem_check(ALL, [('ann', 130)], 100)['late'] == [] and m.postmortem_check(ALL, [('ann', 130)], 100)['ready'] is True
    assert m.postmortem_check(ALL, [('ann', 131)], 100)['late'] == [0]
    assert m.postmortem_check(['summary'], []) == {'missing': ['timeline', 'impact', 'root_cause', 'actions'], 'complete': False, 'late': [], 'owners': [], 'ready': False}
    assert m.postmortem_check([], [])['missing'] == REQ
    assert m.postmortem_check(REQ, [])['complete'] is True and m.postmortem_check(REQ, [])['ready'] is False   # needs an action item
    assert m.postmortem_check(['actions', 'impact', 'summary', 'root_cause', 'timeline'], [])['missing'] == []
    assert m.postmortem_check(['lessons', 'followup', 'appendix'], [])['missing'] == REQ
    assert m.postmortem_check(REQ[:-1], [('a', 1)])['ready'] is False
    r = m.postmortem_check(tuple(REQ), [['zed', 5], ('amy', 40), ('zed', 50), ('bob', 6)], 5, 30)
    assert r == {'missing': [], 'complete': True, 'late': [1, 2], 'owners': ['amy', 'bob', 'zed'], 'ready': False}
    # owner names sort in code point order and keep case
    assert m.postmortem_check(REQ, [('b', 1), ('B', 1), ('a', 1)])['owners'] == ['B', 'a', 'b']
    assert m.postmortem_check(REQ, [('o' * 12, 365)], 365)['owners'] == ['o' * 12]
    assert m.postmortem_check(REQ, [('a', 365)], 0, 365)['late'] == []
    assert m.postmortem_check(REQ, [('a', 365)], 0, 364)['late'] == [0]
    assert m.postmortem_check(REQ, [('a', 365)], 0)['late'] == [0]           # default max_days 30
    assert m.postmortem_check(REQ, [('a', 0)], 0)['late'] == []
    assert len(m.postmortem_check(REQ, [('a', 1)] * 10)['owners']) == 1
    rng = random.Random(638)
    for _ in range(600):
        secs = rng.sample(ALL, rng.randint(0, 8))
        day = rng.randint(0, 300)
        items = [(rng.choice(['a', 'bb', 'Cc', 'x' * 12]), rng.randint(day, 365)) for _ in range(rng.randint(0, 10))]
        md = rng.choice([1, 30, 31, rng.randint(1, 365)])
        assert m.postmortem_check(secs, items, day, md) == _oracle(secs, items, day, md), (secs, items, day, md)


def _late(m):
    SE = 'sections must be a list or tuple'
    AI = 'action_items must be a list or tuple'
    S8 = 'sections must contain at most 8 entries'
    A10 = 'action_items must contain at most 10 entries'
    ID = 'incident_day must be a nonbool integer between 0 and 365'
    MD = 'max_days must be a nonbool integer between 1 and 365'
    UN = 'unknown section name'
    DU = 'duplicate section name'
    PR = 'each action item must be an (owner, due_day) pair'
    OW = 'owner must be a string of 1 to 12 characters'
    DD = 'due_day must be a nonbool integer from incident_day to 365'
    item = ('a', 1)
    for bad in ('ab', None, 5, {}, L(REQ), T(REQ), L(), T()):
        _raises(TypeError, SE, m.postmortem_check, bad, [])
    for bad in ('ab', None, 5, {}, L([item]), T([item]), L(), T()):
        _raises(TypeError, AI, m.postmortem_check, REQ, bad)
    _raises(ValueError, S8, m.postmortem_check, ['summary'] * 9, [])
    _raises(ValueError, S8, m.postmortem_check, [1] * 9, [])             # size before names
    assert m.postmortem_check(ALL, [])['complete'] is True
    _raises(ValueError, A10, m.postmortem_check, REQ, [item] * 11)
    _raises(ValueError, A10, m.postmortem_check, REQ, [1] * 11)
    for bad in (-1, 366, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, ID, m.postmortem_check, REQ, [], bad)
    for bad in (0, 366, -1, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MD, m.postmortem_check, REQ, [], 0, bad)
    assert m.postmortem_check(REQ, [], 365, 365) and m.postmortem_check(REQ, [], 0, 1)
    for bad in ('', 'Summary', 'other', None, 5, S('summary'), LyingS('summary'), b'summary', ['summary']):
        _raises(ValueError, UN, m.postmortem_check, [bad], [])
        _raises(ValueError, UN, m.postmortem_check, ['summary', bad], [])
    _raises(ValueError, DU, m.postmortem_check, ['summary', 'summary'], [])
    _raises(ValueError, DU, m.postmortem_check, ['summary', 'impact', 'summary'], [])
    for K in (L, T):
        for bad in (K(item), K(('a',))):
            _raises(ValueError, PR, m.postmortem_check, REQ, [bad])
            _raises(ValueError, PR, m.postmortem_check, REQ, [item, bad])
    for bad in ('ab', None, 5, (1,), ('a', 1, 1), ()):
        _raises(ValueError, PR, m.postmortem_check, REQ, [bad])
        _raises(ValueError, PR, m.postmortem_check, REQ, [item, bad])
    for bad in ('', 'x' * 13, None, 5, S('a'), LyingS('a'), b'a'):
        _raises(ValueError, OW, m.postmortem_check, REQ, [(bad, 1)])
        _raises(ValueError, OW, m.postmortem_check, REQ, [item, (bad, 1)])
    for bad in (0, 366, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, DD, m.postmortem_check, REQ, [('a', bad)], 1)
        _raises(ValueError, DD, m.postmortem_check, REQ, [item, ('a', bad)], 1)
    _raises(ValueError, DD, m.postmortem_check, REQ, [('a', 4)], 5)        # due before incident_day
    assert m.postmortem_check(REQ, [('a', 5)], 5)['late'] == []
    # order: types, sizes, incident_day, max_days, section names, duplicates, then items
    _raises(TypeError, SE, m.postmortem_check, L(), L())
    _raises(TypeError, AI, m.postmortem_check, [], L(), I(1), I(1))
    _raises(ValueError, S8, m.postmortem_check, [1] * 9, [1] * 11)
    _raises(ValueError, A10, m.postmortem_check, [1], [1] * 11, I(1))
    _raises(ValueError, ID, m.postmortem_check, [1], [1], I(1), I(1))
    _raises(ValueError, MD, m.postmortem_check, [1], [1], 0, I(1))
    _raises(ValueError, UN, m.postmortem_check, [1, 1], [1])
    _raises(ValueError, DU, m.postmortem_check, ['summary', 'summary'], [1])
    _raises(ValueError, PR, m.postmortem_check, [], [1, (I(1), 1)])
    _raises(ValueError, OW, m.postmortem_check, [], [(5, I(1))])


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('summary')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(sections) not in (list, tuple)", "not isinstance(sections, (list, tuple))"),
    ("type(action_items) not in (list, tuple)", "not isinstance(action_items, (list, tuple))"),
    ("len(sections) > len(ALLOWED)", "len(sections) >= len(ALLOWED)"),
    ("len(action_items) > MAX_ITEMS", "len(action_items) >= MAX_ITEMS"),
    ("MAX_ITEMS = 10", "MAX_ITEMS = 11"),
    ("ALLOWED = REQUIRED + ('lessons', 'followup', 'appendix')", "ALLOWED = REQUIRED + ('lessons', 'followup')"),
    ("REQUIRED = ('summary', 'timeline', 'impact', 'root_cause', 'actions')", "REQUIRED = ('timeline', 'summary', 'impact', 'root_cause', 'actions')"),
    ("REQUIRED = ('summary', 'timeline', 'impact', 'root_cause', 'actions')", "REQUIRED = ('summary', 'timeline', 'impact', 'root_cause')"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(incident_day, 0, 365", "_int(incident_day, 1, 365"),
    ("_int(incident_day, 0, 365", "_int(incident_day, 0, 366"),
    ("_int(max_days, 1, 365", "_int(max_days, 0, 365"),
    ("_int(max_days, 1, 365", "_int(max_days, 1, 366"),
    ("incident_day=0", "incident_day=1"),
    ("max_days=30", "max_days=31"),
    ("max_days=30", "max_days=29"),
    ("type(s) is not str or s not in ALLOWED", "not isinstance(s, str) or s not in ALLOWED"),
    ("if s in seen:", "if False:"),
    ("type(item) not in (list, tuple) or len(item) != 2", "not isinstance(item, (list, tuple)) or len(item) != 2"),
    ("or len(item) != 2", "or len(item) > 2"),
    ("or len(item) != 2", "or len(item) < 2"),
    ("type(owner) is not str or not 1 <= len(owner) <= 12", "not isinstance(owner, str) or not 1 <= len(owner) <= 12"),
    ("not 1 <= len(owner) <= 12", "not 0 <= len(owner) <= 12"),
    ("not 1 <= len(owner) <= 12", "not 1 <= len(owner) < 12"),
    ("not 1 <= len(owner) <= 12", "not 1 <= len(owner) <= 13"),
    ("_int(due, incident_day, 365", "_int(due, 0, 365"),
    ("_int(due, incident_day, 365", "_int(due, incident_day, 364"),
    ("if due - incident_day > max_days:", "if due - incident_day >= max_days:"),
    ("if due - incident_day > max_days:", "if due > max_days:"),
    ("late.append(i)", "late.append(i + 1)"),
    ("'owners': sorted(owners)", "'owners': sorted(owners, key=str.lower)"),
    ("and len(action_items) > 0 and not late", "and not late"),
    ("and len(action_items) > 0 and not late", "and len(action_items) > 0"),
    ("'ready': not missing", "'ready': True"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
