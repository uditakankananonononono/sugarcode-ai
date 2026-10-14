"""Row630 hardening: exact-type subclass pins, full-message pins, union
self-time oracle, non-adjacent-order and mixed-validity witnesses, boundary
accepts, mutation sweep. Tests-only delta.

Spans are accepted in BOTH exact list and exact tuple shape by design
(type(s) in (list, tuple)); subclasses of either are refused. Value-type
errors here are ValueError, not TypeError (landed message contract).
Bounding the depth walk (while j!=-1 and depth<100) is an equivalent mutant:
valid parents keep depth <= 31 and any cycle trips the seen check first, so
the extra condition can never change an observable outcome.
"""
import enum
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import distributed_tracing as mod

SRC = pathlib.Path(mod.__file__).read_text()


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


class LyingGe(int):
    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True

    def __gt__(self, other):
        return True

    def __lt__(self, other):
        return True


class WeirdNe(int):
    def __ne__(self, other):
        return False

    def __eq__(self, other):
        return False


class Color(enum.IntEnum):
    RED = 1


class L(list):
    pass


class T(tuple):
    pass


def _oracle(spans):
    n = len(spans)
    root = None
    for i, s in enumerate(spans):
        if s[0] == -1:
            root = i
    depths = []
    for i, (p, a, b) in enumerate(spans):
        d, j = 0, p
        while j != -1:
            d += 1
            j = spans[j][0]
        depths.append(d)
    self_times = []
    for i, (p, a, b) in enumerate(spans):
        kids = sorted((x, y) for q, x, y in spans if q == i)
        covered = 0
        cur_s = cur_e = None
        for x, y in kids:
            if cur_e is None or x > cur_e:
                if cur_e is not None:
                    covered += cur_e - cur_s
                cur_s, cur_e = x, y
            else:
                cur_e = y if y > cur_e else cur_e
        if cur_e is not None:
            covered += cur_e - cur_s
        self_times.append(b - a - covered)
    return {'root': root, 'depths': depths, 'self_times': self_times, 'request_observed': False}


def _core(m):
    run = m.analyze_trace
    # union of child intervals, not sum; nested and contained siblings
    assert run([[-1, 0, 10], [0, 1, 6], [0, 4, 8], [1, 2, 3]]) == {
        'root': 0, 'depths': [0, 1, 1, 2], 'self_times': [3, 4, 4, 1], 'request_observed': False}
    assert run([[-1, 0, 10], [0, 1, 8], [0, 2, 3]])['self_times'] == [3, 7, 1]
    assert run([[-1, 5, 10], [0, 5, 7], [0, 7, 7]])['self_times'] == [3, 2, 0]
    # children declared before parent in the list (order-independent analysis)
    assert run([[1, 4, 4], [-1, 0, 65536]])['self_times'] == [0, 65536]
    # tuple-shaped outer and spans accepted alongside list shape
    assert run(((-1, 0, 10), (0, 1, 6), (0, 4, 8), (1, 2, 3)))['self_times'] == [3, 4, 4, 1]
    assert run([(-1, 0, 4), [0, 1, 2]])['depths'] == [0, 1]
    # 32-deep chain and 32 spans cap
    chain = [[-1, 0, 31]] + [[i - 1, 0, 31] for i in range(1, 32)]
    assert run(chain)['depths'] == list(range(32))
    # boundary accepts
    assert run([[-1, 0, 65536]])['self_times'] == [65536]
    assert run([[-1, 65536, 65536]])['self_times'] == [0]
    assert run([[-1, 0, 0]])['self_times'] == [0]
    # seeded random valid-tree oracle
    rng = random.Random(630)
    for _ in range(200):
        n = rng.randint(1, 32)
        spans = [[-1, 0, rng.randint(0, 65536)]]
        for i in range(1, n):
            q = rng.randrange(i)
            _, pa, pb = spans[q]
            a = rng.randint(pa, pb)
            b = rng.randint(a, pb)
            spans.append([q, a, b])
        order = list(range(n))
        rng.shuffle(order)
        shuffled = [spans[j] for j in order]
        # remap parent indices to the shuffled positions
        pos = {old: new for new, old in enumerate(order)}
        remapped = [[-1 if s[0] == -1 else pos[s[0]], s[1], s[2]] for s in shuffled]
        assert run(remapped) == _oracle(remapped)
    # full exact error messages
    for bad in (None, 1, 'x', {}, {1}, 1.0):
        _raises(TypeError, 'spans must be a list or tuple', run, bad)
    _raises(ValueError, 'span count must be between 1 and 32', run, [])
    _raises(ValueError, 'span count must be between 1 and 32', run, [None] * 33)
    for bad in ([None], [['x']], [[-1, 0]], [[-1, 0, 1, 2]], ['abc']):
        _raises(ValueError, 'spans must contain parent start end', run, bad)
    for slot in range(3):
        for bad in (True, None, 1.0, '1', [], {}):
            s = [-1, 0, 1]
            s[slot] = bad
            _raises(ValueError, 'span values must be nonbool integers', run, [s])
    for s in ([0, 0, 1], [1, 0, 1], [-2, 0, 1], [-1, -1, 1], [-1, 2, 1], [-1, 0, 65537], [-1, 1, 0]):
        _raises(ValueError, 'span indices and times must be valid', run, [s])
    _raises(ValueError, 'span indices and times must be valid', run, [[2, 0, 1], [-1, 0, 1]])  # parent == n
    _raises(ValueError, 'trace must have exactly one root', run, [[-1, 0, 1], [-1, 0, 0]])
    _raises(ValueError, 'trace must have exactly one root', run, [[1, 0, 1], [0, 0, 1]])  # root check before cycle
    _raises(ValueError, 'span parents must be acyclic', run, [[1, 0, 0], [0, 0, 0], [-1, 0, 0]])
    _raises(ValueError, 'child interval must fit parent', run, [[-1, 0, 5], [0, 0, 6]])
    _raises(ValueError, 'child interval must fit parent', run, [[-1, 1, 5], [0, 0, 1]])
    _raises(ValueError, 'child interval must fit parent', run, [[-1, 1, 5], [0, 1, 6]])


def _mix(m):
    run = m.analyze_trace
    # non-adjacent invalid span among valid ones
    _raises(ValueError, 'span values must be nonbool integers',
            run, [[-1, 0, 10], [0, 1, 2], [0, 'x', 4], [0, 2, 3]])
    _raises(ValueError, 'span indices and times must be valid',
            run, [[-1, 0, 10], [0, 1, 2], [0, 2, 70000], [0, 2, 3]])
    _raises(ValueError, 'child interval must fit parent',
            run, [[-1, 0, 10], [0, 1, 2], [1, 2, 3], [0, 2, 30]])
    # mixed-validity: subclass and bad values in later spans after valid earlier spans
    _raises(ValueError, 'spans must contain parent start end', run, [[-1, 0, 10], [0, 1, 2], L([0, 2, 3])])
    _raises(ValueError, 'spans must contain parent start end', run, [[-1, 0, 10], T((0, 1, 2))])
    _raises(ValueError, 'span values must be nonbool integers', run, [[-1, 0, 10], [0, 1, 2], [0, I(2), 3]])
    _raises(ValueError, 'span values must be nonbool integers', run, [[-1, 0, 10], [0, 1, 2], [0, 2, WeirdNe(3)]])
    # non-adjacent-order witness: two roots at positions 1 and 4
    _raises(ValueError, 'trace must have exactly one root',
            run, [[-1, 0, 10], [0, 1, 2], [0, 2, 3], [-1, 4, 5]])


def _late(m):
    run = m.analyze_trace
    # exact-type refusals: subclass at every typed slot (outer, span, value)
    _raises(TypeError, 'spans must be a list or tuple', run, L([[-1, 0, 1]]))
    _raises(TypeError, 'spans must be a list or tuple', run, T(([-1, 0, 1],)))
    _raises(ValueError, 'spans must contain parent start end', run, [L([-1, 0, 1])])
    _raises(ValueError, 'spans must contain parent start end', run, [T((-1, 0, 1))])
    for slot in range(3):
        for bad in (I(1), LyingGe(1), WeirdNe(1), Color.RED):
            s = [-1, 0, 1]
            s[slot] = bad
            _raises(ValueError, 'span values must be nonbool integers', run, [s])
    # subclass refused before any cap or bound check
    _raises(TypeError, 'spans must be a list or tuple', run, L([[-1, 0, 1]] * 33))
    _raises(ValueError, 'spans must contain parent start end', run, [[-1, 0, 10]] * 31 + [L([0, 1, 2])])
    _raises(ValueError, 'span values must be nonbool integers', run, [[-1, 0, LyingGe(10 ** 30)]])
    _raises(ValueError, 'span values must be nonbool integers', run, [[WeirdNe(-1), 0, 1]])
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert run(list([list([-1, 0, 1])]))['root'] == 0
    assert run(tuple([tuple((-1, 0, 1))]))['root'] == 0
    assert run([[-1, 0, 1], [0, 0, int(1)]])['depths'] == [0, 1]


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(spans) not in (list,tuple)', 'not isinstance(spans, (list,tuple))'),
    ('type(s) not in (list,tuple)', 'not isinstance(s, (list,tuple))'),
    ('type(v) is not int', 'not isinstance(v, int)'),
    ('if not 1<=n<=32', 'if not 1<=n<=33'),
    ('if not 1<=n<=32', 'if not 0<=n<=32'),
    ('len(s)!=3', 'len(s)!=4'),
    ('-1<=p<n', '-1<=p<=n'),
    (' or p==i', ''),
    ('0<=a<=b<=65536', '0<=a<=b<=65537'),
    ('0<=a<=b<=65536', 'a<=b<=65536'),
    ('0<=a<=b<=65536', '0<=a<b<=65536'),
    ('if len(roots)!=1', 'if len(roots)>1'),
    ('if j in seen:raise', 'if False:raise'),
    ('not spans[p][1]<=a<=b<=spans[p][2]', 'not spans[p][1]<a<b<spans[p][2]'),
    ('if p!=-1 and not spans[p][1]<=a<=b<=spans[p][2]', 'if False'),
    ('intervals=sorted((x,y) for parent,x,y in spans if parent==i)',
     'intervals=[(x,y) for parent,x,y in spans if parent==i]'),
    ('covered+=max(0,y-max(right,x))', 'covered+=y-max(right,x)'),
    ('right=max(right,y)', 'right=y'),
    ('self_times.append(b-a-covered)', 'self_times.append(b-a)'),
    ('depths.append(depth)', 'depths.append(depth+1)'),
    ("'request_observed':False", "'request_observed':True"),
    ('if p==-1', 'if p==0'),
    ('spans must be a list or tuple', 'spans must be a list'),
    ('span count must be between 1 and 32', 'span count must be between 1 and 33'),
    ('spans must contain parent start end', 'spans must contain parent start and end'),
    ('span values must be nonbool integers', 'span values must be integers'),
    ('span indices and times must be valid', 'span indices and times must be in range'),
    ('trace must have exactly one root', 'trace must have one root'),
    ('span parents must be acyclic', 'span parents must not cycle'),
    ('child interval must fit parent', 'child interval must fit inside parent'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
