import subprocess
import sys

import pytest

SRC = "import sys; sys.setrecursionlimit(10**7); s = []\nfor _ in range(100000): s = [s]\n"
STAB = "{'mode':'plasmid','burden':0.1,'size_kb':5}"
CASES = [
    ("syndroid", "mechanistic_cell_program", "None, hours=1", ""),
    ("syndroid", "design_syndroid", "", ""),
    ("stability_ai", "stochastic_drift", STAB, ""),
    ("stability_ai", "stochastic_drift_v2", STAB, ""),
    ("stability_ai", "analyze_stability", STAB, ""),
    ("stability_ai", "analyze_stability_v2", STAB, ""),
]


def run(mod, kind, fn, args):
    body = SRC + f"from sugarcode.modules.{mod} import {kind} as m\nm.{fn}({args + ', ' if args else ''}seed=s)\n"
    return subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("mod,fn,args,_", CASES)
def test_unwrapped_core_crashes_on_nested_list_seed(mod, fn, args, _):
    # environment-robust: older numpy segfaults (rc -11/139), newer numpy may raise TypeError; either way no valid result
    assert run(mod, "core", fn, args).returncode != 0


@pytest.mark.parametrize("mod,fn,args,_", CASES)
def test_guard_raises_named_error_instead(mod, fn, args, _):
    r = run(mod, "seed_guard", fn, args)
    assert r.returncode == 1
    assert r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"
