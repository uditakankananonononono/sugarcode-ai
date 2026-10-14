import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import log_merge as mod

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


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: time-ordered merge of supplied log streams, no real logs or storage'
    assert len(mod.NOT_CLAIMED) >= 4 and 'parsing real logs' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(streams, limit):
    """Independent: repeated k-way pick of the smallest head, ties to the earlier stream."""
    heads = [0] * len(streams)
    out = []
    while True:
        best = None
        for si, (src, ents) in enumerate(streams):
            if heads[si] < len(ents) and (best is None or ents[heads[si]][0] < streams[best][1][heads[best]][0]):
                best = si
        if best is None:
            break
        t, msg = streams[best][1][heads[best]]
        out.append((t, streams[best][0], msg))
        heads[best] += 1
    return {'merged': out[:limit], 'counts': {s: len(e) for s, e in streams}, 'total': len(out), 'truncated': len(out) > limit}


def _core(m):
    a = ('web', [(1, 'start'), (5, 'req'), (5, 'resp'), (9, 'stop')])
    b = ('db', [(2, 'open'), (5, 'query'), (7, 'close')])
    r = m.merge_logs([a, b])
    assert r['merged'] == [(1, 'web', 'start'), (2, 'db', 'open'), (5, 'web', 'req'), (5, 'web', 'resp'), (5, 'db', 'query'), (7, 'db', 'close'), (9, 'web', 'stop')]
    assert r['counts'] == {'web': 4, 'db': 3} and r['total'] == 7 and r['truncated'] is False
    assert m.merge_logs([b, a])['merged'][2:5] == [(5, 'db', 'query'), (5, 'web', 'req'), (5, 'web', 'resp')]    # tie goes to the earlier source
    assert m.merge_logs((a, b), 7)['truncated'] is False and m.merge_logs([a, b], 6)['truncated'] is True
    assert m.merge_logs([a, b], 3)['merged'] == [(1, 'web', 'start'), (2, 'db', 'open'), (5, 'web', 'req')]
    assert m.merge_logs([a, b], 1)['merged'] == [(1, 'web', 'start')] and m.merge_logs([a, b], 1)['total'] == 7
    assert m.merge_logs([('x', [])]) == {'merged': [], 'counts': {'x': 0}, 'total': 0, 'truncated': False}
    assert m.merge_logs([['x', ((0, 'm'),)], ('y', [[0, 'n']])])['merged'] == [(0, 'x', 'm'), (0, 'y', 'n')]
    assert m.merge_logs([('x' * 16, [(1000000, 'y' * 40)])])['merged'] == [(1000000, 'x' * 16, 'y' * 40)]
    full = [('s%d' % i, [(j, 'm') for j in range(20)]) for i in range(8)]
    assert m.merge_logs(full, 160)['total'] == 160 and m.merge_logs(full, 160)['truncated'] is False
    assert len(m.merge_logs(full, 160)['merged']) == 160 and m.merge_logs(full, 159)['truncated'] is True
    # default limit 50: 60 entries, the 50th and 51st entries on either side of the cut
    two = [('p', [(i, 'a%d' % i) for i in range(20)]), ('q', [(i, 'b%d' % i) for i in range(20)]), ('r', [(i, 'c%d' % i) for i in range(20)])]
    d = m.merge_logs(two)
    assert len(d['merged']) == 50 and d['total'] == 60 and d['truncated'] is True and d['merged'][-1] == (16, 'q', 'b16')
    assert m.merge_logs(two, 50) == d
    assert m.merge_logs(two[:1])['truncated'] is False
    rng = random.Random(632)
    for _ in range(400):
        streams = []
        for k in range(rng.randint(1, 5)):
            t, ents = 0, []
            for _ in range(rng.randint(0, 8)):
                t += rng.choice((0, 0, 1, 2, 5))
                ents.append((t, 'm%d' % rng.randint(0, 9)))
            streams.append(('s%d' % k, ents))
        lim = rng.choice((1, 3, 10, 50, rng.randint(1, 160)))
        assert m.merge_logs(streams, lim) == _oracle(streams, lim), (streams, lim)


def _late(m):
    ST = 'streams must be a list or tuple'
    SZ = 'streams must contain between 1 and 8 entries'
    LM = 'limit must be a nonbool integer between 1 and 160'
    EP = 'each stream must be a (source, entries) pair'
    SN = 'source names must be strings of 1 to 16 characters'
    EN = 'entries must be a list or tuple'
    EC = 'entries must contain at most 20 items'
    PE = 'each entry must be a (time, message) pair'
    TM = 'time must be a nonbool integer between 0 and 1000000'
    MG = 'messages must be strings of 1 to 40 characters'
    good = ('a', [(1, 'x')])
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, ST, m.merge_logs, bad)
    _raises(TypeError, ST, m.merge_logs, L([good] * 9))
    _raises(ValueError, SZ, m.merge_logs, [])
    _raises(ValueError, SZ, m.merge_logs, [('s%d' % i, []) for i in range(9)])
    for bad in (0, 161, True, False, 1.0, '1', None, I(50), LyingI(50), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, LM, m.merge_logs, [good], bad)
    for K in (L, T):
        for bad in (K(good), K(('a',))):
            _raises(ValueError, EP, m.merge_logs, [bad])
            _raises(ValueError, EP, m.merge_logs, [good, bad])
    for bad in ('ab', None, 5, ('a',), ('a', [], 1), ()):
        _raises(ValueError, EP, m.merge_logs, [bad])
        _raises(ValueError, EP, m.merge_logs, [good, bad])
    for bad in ('', 'x' * 17, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, SN, m.merge_logs, [(bad, [])])
        _raises(ValueError, SN, m.merge_logs, [good, (bad, [])])
    _raises(ValueError, 'duplicate source name', m.merge_logs, [good, good])
    _raises(ValueError, 'duplicate source name', m.merge_logs, [good, ('b', []), ('a', [])])
    for bad in ('ab', None, 5, {}, L([(1, 'x')]), T([(1, 'x')]), L(), T()):
        _raises(ValueError, EN, m.merge_logs, [('b', bad)])
        _raises(ValueError, EN, m.merge_logs, [good, ('b', bad)])
    _raises(ValueError, EN, m.merge_logs, [('b', L([(1, 'x')] * 21))])          # subclass refused before the 20 cap
    _raises(ValueError, EC, m.merge_logs, [('b', [(1, 'x')] * 21)])
    assert m.merge_logs([('b', [(1, 'x')] * 20)])['total'] == 20
    for K in (L, T):
        for bad in (K((1, 'x')), K((1,))):
            _raises(ValueError, PE, m.merge_logs, [('b', [bad])])
            _raises(ValueError, PE, m.merge_logs, [('b', [(1, 'x'), bad])])
    for bad in ('ab', None, 5, (1,), (1, 'x', 2), ()):
        _raises(ValueError, PE, m.merge_logs, [('b', [bad])])
        _raises(ValueError, PE, m.merge_logs, [('b', [(1, 'x'), bad])])
    for bad in (-1, 1000001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TM, m.merge_logs, [('b', [(bad, 'x')])])
        _raises(ValueError, TM, m.merge_logs, [('b', [(1, 'x'), (bad, 'x')])])
    for bad in ('', 'x' * 41, None, 5, S('x'), LyingS('x'), b'x'):
        _raises(ValueError, MG, m.merge_logs, [('b', [(1, bad)])])
        _raises(ValueError, MG, m.merge_logs, [('b', [(1, 'x'), (2, bad)])])
    _raises(ValueError, 'times must not decrease within a stream', m.merge_logs, [('b', [(5, 'x'), (4, 'x')])])
    assert m.merge_logs([('b', [(5, 'x'), (5, 'x')]), ('c', [(1, 'x')])])['total'] == 3         # decreasing across streams is fine
    # order: streams, size, limit, then per stream: shape, source, duplicate, entries type, count, then per entry shape, time, message, order
    _raises(TypeError, ST, m.merge_logs, L([1]), I(1))
    _raises(ValueError, SZ, m.merge_logs, [], I(1))
    _raises(ValueError, LM, m.merge_logs, [1], I(1))
    _raises(ValueError, EP, m.merge_logs, [1], 5)
    _raises(ValueError, SN, m.merge_logs, [(S('a'), L())])
    _raises(ValueError, EN, m.merge_logs, [('a', L([1]))])
    _raises(ValueError, PE, m.merge_logs, [('a', [1])])
    _raises(ValueError, TM, m.merge_logs, [('a', [(I(1), S('x'))])])
    _raises(ValueError, MG, m.merge_logs, [('a', [(5, S('x')), (4, 'x')])])                       # message before the order check


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
    def __hash__(self): return hash('a')


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


def test_result_is_fresh_and_streams_unchanged():
    streams = [('a', [(1, 'x')])]
    r = mod.merge_logs(streams)
    r['merged'].append('zzz')
    r['counts']['zzz'] = 1
    assert streams == [('a', [(1, 'x')])]
    assert mod.merge_logs(streams)['merged'] == [(1, 'a', 'x')]


MUTANTS = [
    ("type(streams) not in (list, tuple)", "not isinstance(streams, (list, tuple))"),
    ("not 1 <= len(streams) <= MAX_STREAMS", "not 0 <= len(streams) <= MAX_STREAMS"),
    ("not 1 <= len(streams) <= MAX_STREAMS", "not 1 <= len(streams) < MAX_STREAMS"),
    ("MAX_STREAMS = 8", "MAX_STREAMS = 9"),
    ("MAX_ENTRIES = 20", "MAX_ENTRIES = 21"),
    ("MAX_ENTRIES = 20", "MAX_ENTRIES = 19"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(limit, 1, 160", "_int(limit, 0, 160"),
    ("_int(limit, 1, 160", "_int(limit, 1, 161"),
    ("limit=50", "limit=51"),
    ("limit=50", "limit=49"),
    ("type(s) not in (list, tuple) or len(s) != 2", "not isinstance(s, (list, tuple)) or len(s) != 2"),
    ("or len(s) != 2", "or len(s) > 2"),
    ("or len(s) != 2", "or len(s) < 2"),
    ("type(source) is not str", "not isinstance(source, str)"),
    ("not 1 <= len(source) <= 16", "not 0 <= len(source) <= 16"),
    ("not 1 <= len(source) <= 16", "not 1 <= len(source) <= 17"),
    ("not 1 <= len(source) <= 16", "not 1 <= len(source) < 16"),
    ("if source in names:", "if False:"),
    ("if type(entries) not in (list, tuple):", "if not isinstance(entries, (list, tuple)):"),
    ("len(entries) > MAX_ENTRIES", "len(entries) >= MAX_ENTRIES"),
    ("type(e) not in (list, tuple) or len(e) != 2", "not isinstance(e, (list, tuple)) or len(e) != 2"),
    ("or len(e) != 2", "or len(e) > 2"),
    ("or len(e) != 2", "or len(e) < 2"),
    ("_int(t, 0, 1000000", "_int(t, 1, 1000000"),
    ("_int(t, 0, 1000000", "_int(t, 0, 1000001"),
    ("type(msg) is not str", "not isinstance(msg, str)"),
    ("not 1 <= len(msg) <= 40", "not 0 <= len(msg) <= 40"),
    ("not 1 <= len(msg) <= 40", "not 1 <= len(msg) <= 41"),
    ("not 1 <= len(msg) <= 40", "not 1 <= len(msg) < 40"),
    ("if t < last:", "if t <= last:"),
    ("if t < last:", "if False:"),
    ("last = t", "last = 0"),
    ("key=lambda x: (x[0], x[1], x[2])", "key=lambda x: (x[0], x[2], x[1])"),
    ("key=lambda x: (x[0], x[1], x[2])", "key=lambda x: (x[0], -x[1], x[2])"),
    ("key=lambda x: (x[0], x[1], x[2])", "key=lambda x: (x[0], x[1], -x[2])"),
    ("tagged[:limit]", "tagged[:limit - 1]"),
    ("tagged[:limit]", "tagged[:limit + 1]"),
    ("'total': len(tagged)", "'total': len(tagged[:limit])"),
    ("len(tagged) > limit", "len(tagged) >= limit"),
    ("len(entries) for source, entries in streams}", "len(entries) + 1 for source, entries in streams}"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
