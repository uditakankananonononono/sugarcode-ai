import importlib
import re
import subprocess
import sys

import numpy as np
import pytest

from sugarcode.seed_check import MAX_SEED

core = importlib.import_module("sugarcode.modules.liquid_biopsy.core")
sc = importlib.import_module("sugarcode.modules.liquid_biopsy.seed_checked")
CAP = 2**63 - 1
CASES = [
    ("bootstrap_haplotype_weights", '[[0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]], replicates=10', ([[0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]],), dict(replicates=10)),
]
CASES.append(("fragment_length_model", "0.3, 2000", (0.3, 2000), dict()))


def msg(s):
    return re.escape(s) + "$"


def outcome(fn, args, kw, seed):
    try:
        return ("ok", fn(*args, seed=seed, **kw))
    except Exception as e:  # compare core and wrapper on valid seeds, including core's own refusals
        return ("err", type(e).__name__, str(e))


def run(modname, fn, argstr):
    body = ("import sys; sys.setrecursionlimit(10**7); s = []\nfor _ in range(100000): s = [s]\n"
            f"from sugarcode.modules.liquid_biopsy import {modname} as m\nm.{fn}({argstr + ', ' if argstr else ''}seed=s)\n")
    return subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_unchecked_core_gives_no_valid_result_on_nested_list_seed(fn, argstr, args, kw):
    # import must work first, so a failure below is the seed and not a broken import
    assert subprocess.run([sys.executable, "-c", "from sugarcode.modules.liquid_biopsy import core"], capture_output=True, timeout=120).returncode == 0
    r = run("core", fn, argstr)
    # environment-robust: older numpy segfaults (-11), newer numpy/scipy raises TypeError or RecursionError (seed repr); either is a failure on the seed
    assert r.returncode == -11 or (r.returncode == 1 and r.stderr.strip().splitlines()[-1].split(":")[0] in ("TypeError", "RecursionError"))


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_checked_entry_refuses_with_helper_message(fn, argstr, args, kw):
    r = run("seed_checked", fn, argstr)
    assert r.returncode == 1
    assert r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"


@pytest.mark.parametrize("fn,argstr,args,kw", CASES)
def test_seed_pins(fn, argstr, args, kw):
    w = getattr(sc, fn)
    for bad in (True, False, np.bool_(True), 1.0, "1", None, [1], [[]]):
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
