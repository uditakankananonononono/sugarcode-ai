import re
import subprocess
import sys

import numpy as np
import pytest

from sugarcode.modules.syndroid import core, seed_checked as sc
from sugarcode.seed_check import MAX_SEED, check_seed

CAP = 2**63 - 1
PROG = {"circuit": {"burden": 0.1}}


def msg(s):
    return re.escape(s) + "$"


def run(mod, fn, args):
    body = ("import sys; sys.setrecursionlimit(10**7); s = []\nfor _ in range(100000): s = [s]\n"
            f"from sugarcode.modules.syndroid import {mod} as m\nm.{fn}({args}, seed=s)\n")
    return subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, timeout=120)


CASES = [("stochastic_gene_expression", "['a'], minutes=1"), ("evolutionary_stability", "{'circuit': {'burden': 0.1}}")]


@pytest.mark.parametrize("fn,args", CASES)
def test_unchecked_core_crashes_on_nested_list_seed(fn, args):
    # environment-robust: older numpy segfaults (rc -11/139), newer numpy may raise TypeError; either way no valid result
    assert run("core", fn, args).returncode != 0


@pytest.mark.parametrize("fn,args", CASES)
def test_checked_entry_raises_named_error(fn, args):
    r = run("seed_checked", fn, args)
    assert r.returncode == 1
    assert r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"


def test_check_seed_pins():
    assert MAX_SEED == CAP
    for ok in (0, 1, CAP, np.int64(5), np.uint64(CAP), np.int32(0)):
        assert check_seed(ok) == int(ok) and type(check_seed(ok)) is int
    for bad in (True, False, np.bool_(True), 1.0, np.float64(1), "1", b"1", None, [1], [[]], 1 + 0j):
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            check_seed(bad)
    for bad in (-1, CAP + 1, 2**64, -(2**64), 10**400, np.int64(-1), np.uint64(2**63)):
        with pytest.raises(ValueError, match=msg(f"seed must be between 0 and {CAP}")):
            check_seed(bad)
    assert check_seed(None, allow_none=True) is None
    with pytest.raises(TypeError, match=msg("seed must be an integer")):
        check_seed(None, allow_none=False)


def test_both_functions_reject_through_wrapper():
    for fn, a, kw in ((sc.stochastic_gene_expression, (["a"],), {"minutes": 1}), (sc.evolutionary_stability, (PROG,), {})):
        for bad, exc, m in ((True, TypeError, "seed must be an integer"), (None, TypeError, "seed must be an integer"),
                            (-1, ValueError, f"seed must be between 0 and {CAP}"), (CAP + 1, ValueError, f"seed must be between 0 and {CAP}")):
            with pytest.raises(exc, match=msg(m)):
                fn(*a, seed=bad, **kw)
        with pytest.raises(TypeError, match=msg("seed must be an integer")):
            fn(*a, seed=[[]], **kw)


def test_valid_results_equal_core_called_directly():
    for s in (0, 7, CAP, np.int64(7)):
        assert sc.stochastic_gene_expression(["a", "b"], minutes=3, seed=s) == core.stochastic_gene_expression(["a", "b"], minutes=3, seed=int(s))
        assert sc.evolutionary_stability(PROG, generations=20, population=50, seed=s) == core.evolutionary_stability(PROG, generations=20, population=50, seed=int(s))
    assert sc.stochastic_gene_expression(["a"], minutes=2) == core.stochastic_gene_expression(["a"], minutes=2)


def test_numpy_integer_seed_reaches_core_as_plain_int():
    r = sc.stochastic_gene_expression(["a"], minutes=2, seed=np.int64(7))
    assert type(r["seed"]) is int and r["seed"] == 7
