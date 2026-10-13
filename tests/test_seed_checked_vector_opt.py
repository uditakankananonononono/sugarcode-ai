import importlib
import inspect
import re
import subprocess
import sys

import numpy as np
import pytest

core = importlib.import_module("sugarcode.modules.vector_opt.core")
sc = importlib.import_module("sugarcode.modules.vector_opt.seed_checked")
CAP = 2**63 - 1


def _split(argstr):
    ns = {'np': np}
    exec('def _f(*a, **k): return a, k', ns)
    return eval('_f(' + argstr + ')', ns)
CASES = [
    ('directed_evolution', 'n_rounds=2, n_variants=2', *_split('n_rounds=2, n_variants=2')),
]


def msg(s):
    return re.escape(s) + "$"


def outcome(fn, args, kw, seed):
    try:
        return ("ok", fn(*args, seed=seed, **kw))
    except Exception as e:  # compare core and wrapper on valid seeds, including core's own refusals
        return ("err", type(e).__name__, str(e))


def run(modname, fn, argstr):
    body = ("import sys; sys.setrecursionlimit(10**7); import numpy as np; s = []\nfor _ in range(100000): s = [s]\n"
            f"from sugarcode.modules.vector_opt import {modname} as m\nm.{fn}({argstr + ', ' if argstr else ''}seed=s)\n")
    return subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_unchecked_core_fails_on_nested_list_seed(fn, argstr, args, kw):
    # import must work first, so a failure below is the seed and not a broken import
    assert subprocess.run([sys.executable, "-c", "from sugarcode.modules.vector_opt import core"], capture_output=True, timeout=120).returncode == 0
    r = run("core", fn, argstr)
    # random.Random(list) raises TypeError (unhashable list on 3.10, unsupported seed type on 3.11+); a segfault or RecursionError would also be a failure
    assert r.returncode == -11 or (r.returncode == 1 and any(l.split(":")[0] in ("TypeError", "RecursionError") for l in r.stderr.splitlines()) and "seed must be an integer" not in r.stderr)


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_checked_entry_refuses_with_helper_message(fn, argstr, args, kw):
    r = run("seed_checked", fn, argstr)
    assert r.returncode == 1
    assert r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_seed_pins(fn, argstr, args, kw):
    w = getattr(sc, fn)
    for bad in (True, False, np.bool_(True), 1.0, "1", None, [1], [[]], b"1"):
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            w(*args, seed=bad, **kw)
    for bad in (-1, CAP + 1, 2**64, 10**400):
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            w(*args, seed=bad, **kw)


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_valid_seed_same_as_core(fn, argstr, args, kw):
    c, w = getattr(core, fn), getattr(sc, fn)
    assert outcome(w, args, kw, 3)[0] == "ok"  # the compared path is a real result, not a shared error
    for s in (0, 3, CAP):
        assert repr(outcome(w, args, kw, s)) == repr(outcome(c, args, kw, s))
    assert repr(outcome(w, args, kw, np.int64(3))) == repr(outcome(c, args, kw, 3))


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_wrapper_wraps_core_and_signature_unchanged(fn, argstr, args, kw):
    import inspect
    assert getattr(sc, fn).__wrapped__ is getattr(core, fn)
    assert inspect.signature(getattr(sc, fn)) == inspect.signature(getattr(core, fn))


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_core_receives_plain_int_and_defaults_untouched(fn, argstr, args, kw, monkeypatch):
    seen = []
    sig = inspect.signature(getattr(core, fn))
    def spy(*a, **k):
        seen.append(sig.bind(*a, **k).arguments.get("seed", "unset"))
        return "ok"
    spy.__signature__ = sig
    g = sc._guard(spy)
    g(*args, seed=np.int32(5), **kw)
    assert type(seen[0]) is int and seen[0] == 5
    g(*args, **kw)  # seed not given: not injected
    assert seen[1] == "unset"
    with pytest.raises(TypeError, match=msg("seed must be an integer")):
        g(*args, seed=None, **kw)
    assert len(seen) == 2
