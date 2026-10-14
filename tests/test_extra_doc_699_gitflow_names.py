import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import gitflow_names as mod

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


import re


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: naming pattern classification of supplied branch names, no repository is read'
    assert len(mod.NOT_CLAIMED) == 5 and 'merge direction' in mod.NOT_CLAIMED and 'release content' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


_RX = re.compile(r'(feature|release|hotfix)/([a-z0-9]|[a-z0-9][a-z0-9-]{0,14}[a-z0-9])')


def _okind(n):
    if n in ('main', 'develop'):
        return n
    mm = _RX.fullmatch(n)
    return mm.group(1) if mm else 'invalid'


def _oracle(ns):
    ks = [(n, _okind(n)) for n in ns]
    order = ['main', 'develop', 'feature', 'release', 'hotfix', 'invalid']
    cs = [(k, [kk for _, kk in ks].count(k)) for k in order]
    return {'kinds': ks, 'counts': cs, 'valid': dict(cs)['invalid'] == 0}


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
    def __hash__(self): return hash('main')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.gitflow_names
    Z = [('main', 0), ('develop', 0), ('feature', 0), ('release', 0), ('hotfix', 0), ('invalid', 0)]
    assert f([]) == {'kinds': [], 'counts': Z, 'valid': True}
    assert f(['main'])['kinds'] == [('main', 'main')] and f(['develop'])['kinds'] == [('develop', 'develop')]
    assert f(['feature/a'])['kinds'] == [('feature/a', 'feature')]
    assert f(['release/1-2'])['kinds'] == [('release/1-2', 'release')]
    assert f(['hotfix/x9'])['kinds'] == [('hotfix/x9', 'hotfix')]
    r = f(['main', 'develop', 'feature/a', 'feature/b', 'release/r', 'hotfix/h', 'bad', 'Main'])
    assert r['counts'] == [('main', 1), ('develop', 1), ('feature', 2), ('release', 1), ('hotfix', 1), ('invalid', 2)]
    assert r['valid'] is False
    for bad in ('', 'Main', 'main ', 'master', 'feature', 'feature/', 'feature/-a', 'feature/a-', 'feature/A', 'feature/a_b', 'feature/a b',
                'feature/' + 'a' * 17, 'feat/a', 'features/a', 'Feature/a', 'feature//a', 'feature/a/b', 'release', 'hotfix/', '/a', 'develop/a', 'main/a', 'feature/é'):
        assert f([bad])['kinds'] == [(bad, 'invalid')], bad
        assert f([bad])['valid'] is False
    for ok in ('feature/' + 'a' * 16, 'feature/a', 'feature/0', 'feature/a-b', 'feature/a--b', 'feature/9-9', 'hotfix/-'[:0] + 'hotfix/z'):
        assert f([ok])['kinds'][0][1] != 'invalid', ok
    assert f(('main',))['valid'] is True
    # default max_names is 8
    n8 = ['feature/%d' % i for i in range(8)]
    f(n8)
    _raises(ValueError, 'names must contain at most max_names entries', f, n8 + ['feature/8'])
    assert f(n8 + ['feature/8'], 9)['counts'][2] == ('feature', 9)
    assert f(['feature/%d' % i for i in range(20)], 20)['counts'][2] == ('feature', 20)
    _raises(ValueError, 'names must contain at most max_names entries', f, n8[:3], 2)
    f(n8[:2], 2)
    rng = random.Random(699)
    alpha = 'ab-9_A/'
    for _ in range(600):
        ns = []
        for _ in range(rng.randint(0, 8)):
            pre = rng.choice(('feature/', 'release/', 'hotfix/', '', 'main', 'develop', 'fix/'))
            ns.append(pre + ''.join(rng.choice(alpha) for _ in range(rng.randint(0, 4))))
        ns = list(dict.fromkeys(ns))
        assert f(ns) == _oracle(ns), ns
    assert f(['feature/' + 'a' * 16, 'feature/' + 'a' * 17, 'feature/-' + 'a'])['counts'][-1] == ('invalid', 2)


def _late(m):
    f = m.gitflow_names
    MN = 'max_names must be a nonbool integer between 1 and 20'
    NT = 'names must be a list or tuple'
    NS = 'names must contain at most max_names entries'
    NE = 'each name must be a string'
    ND = 'names must be distinct'
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MN, f, [], bad)
    f([], 1)
    f([], 20)
    for bad in ('ab', None, 5, {}, L(['main']), T(['main']), L(), T()):
        _raises(TypeError, NT, f, bad)
    _raises(ValueError, NS, f, ['main'] * 9)
    for bad in (None, 5, True, S('main'), LyingS('main'), b'main', ['main']):
        _raises(ValueError, NE, f, [bad])
        _raises(ValueError, NE, f, ['main', bad])
    _raises(ValueError, ND, f, ['main', 'main'])
    _raises(ValueError, ND, f, ['main', 'develop', 'main'])
    # validation order
    _raises(ValueError, MN, f, None, I(1))
    _raises(TypeError, NT, f, None)
    _raises(ValueError, NS, f, [1] * 9)
    _raises(ValueError, NE, f, [1, 1])
    _raises(ValueError, ND, f, ['a', 'a'])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_names=8", "max_names=9"),
    ("max_names=8", "max_names=7"),
    ("type(max_names) is not int or not 1 <= max_names <= 20", "not isinstance(max_names, int) or not 1 <= max_names <= 20"),
    ("type(max_names) is not int or not 1 <= max_names <= 20", "isinstance(max_names, bool) or not isinstance(max_names, int) or not 1 <= max_names <= 20"),
    ("not 1 <= max_names <= 20", "not 0 <= max_names <= 20"),
    ("not 1 <= max_names <= 20", "not 1 <= max_names < 20"),
    ("not 1 <= max_names <= 20", "not 1 <= max_names <= 21"),
    ("type(names) not in (list, tuple)", "not isinstance(names, (list, tuple))"),
    ("len(names) > max_names", "len(names) >= max_names"),
    ("if type(n) is not str:", "if not isinstance(n, str):"),
    ("len(set(names)) != len(names)", "False"),
    ("if name == 'main':", "if name.startswith('main'):"),
    ("if name == 'develop':", "if name.startswith('develop'):"),
    ("for k in ('feature', 'release', 'hotfix'):", "for k in ('feature', 'release'):"),
    ("for k in ('feature', 'release', 'hotfix'):", "for k in ('feature', 'hotfix'):"),
    ("for k in ('feature', 'release', 'hotfix'):", "for k in ('release', 'hotfix'):"),
    ("pre = k + '/'", "pre = k"),
    ("1 <= len(topic) <= 16", "0 <= len(topic) <= 16"),
    ("1 <= len(topic) <= 16", "1 <= len(topic) < 16"),
    ("1 <= len(topic) <= 16", "1 <= len(topic) <= 17"),
    ("topic[0] != '-'", "True"),
    ("topic[-1] != '-'", "True"),
    ("all(c in OK for c in topic)", "True"),
    ("all(c in OK for c in topic)", "all(c in OK[:-1] for c in topic)"),
    ("OK = 'abcdefghijklmnopqrstuvwxyz0123456789-'", "OK = 'abcdefghijklmnopqrstuvwxyz-'"),
    ("OK = 'abcdefghijklmnopqrstuvwxyz0123456789-'", "OK = 'abcdefghijklmnopqrstuvwxyz0123456789-_'"),
    ("OK = 'abcdefghijklmnopqrstuvwxyz0123456789-'", "OK = 'abcdefghijklmnopqrstuvwxyz0123456789-ABC'"),
    ("KINDS = ('main', 'develop', 'feature', 'release', 'hotfix', 'invalid')", "KINDS = ('develop', 'main', 'feature', 'release', 'hotfix', 'invalid')"),
    ("'valid': counts[-1][1] == 0", "'valid': counts[-1][1] <= 1"),
    ("'valid': counts[-1][1] == 0", "'valid': True"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
