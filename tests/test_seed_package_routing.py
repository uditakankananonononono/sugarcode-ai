"""Across ALL packages: the package-level name of every seeded function that has a seed wrapper is that wrapper.

A wrapper is a function in a submodule named seed_* (functools.wraps of the implementation, or defined there under the
implementation's name). The implementation is the one function of that name, with a `seed` parameter, in a non-seed submodule.
"""
import importlib
import inspect
import pkgutil
import re
import subprocess
import sys

import pytest

import sugarcode.modules as modules_pkg

# package-level names that cannot be the wrapper's own name: the wrapper is exported under a distinct alias instead
ALIASES = {
    ("docking_studio", "dock"): "dock_vina_real",  # package `dock` is core.dock, a different unseeded function
    ("docking_studio", "prepare_ligand_from_smiles"): "prepare_ligand_vina_real",  # not exported before; alias keeps the vina names distinct
}


def scan():
    rows = []
    for _, m, ispkg in pkgutil.iter_modules(modules_pkg.__path__):
        if not ispkg:
            continue
        pkg = importlib.import_module(f"sugarcode.modules.{m}")
        subs = [n for _, n, _ in pkgutil.iter_modules(pkg.__path__)]
        impl = [importlib.import_module(f"sugarcode.modules.{m}.{n}") for n in subs if not n.startswith("seed_")]
        for s in subs:
            if not s.startswith("seed_"):
                continue
            sm = importlib.import_module(f"sugarcode.modules.{m}.{s}")
            for n, o in vars(sm).items():
                if n.startswith("_") or not inspect.isfunction(o):
                    continue
                ts = [vars(im).get(n) for im in impl]
                ts = [t for t in ts if inspect.isfunction(t) and t.__module__ == vars(im := importlib.import_module(t.__module__))["__name__"]
                      and "seed" in inspect.signature(t).parameters]
                if len(ts) != 1 or o is ts[0] or o.__module__ not in (sm.__name__, ts[0].__module__):
                    continue
                rows.append((m, s, n, ts[0]))
    return rows


ROWS = scan()
ROUTED = [r for r in ROWS if (r[0], r[2]) not in ALIASES]


def test_scan_counts():
    assert len(ROWS) == 74 and len(ROUTED) == 72
    assert {(r[0], r[2]) for r in ROWS if (r[0], r[2]) in ALIASES} == set(ALIASES)


def test_each_package_function_has_exactly_one_wrapper():
    keys = [(r[0], r[2]) for r in ROWS]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("m,s,n,impl", ROUTED, ids=[f"{r[0]}.{r[2]}" for r in ROUTED])
def test_package_name_is_the_wrapper(m, s, n, impl):
    pkg = importlib.import_module(f"sugarcode.modules.{m}")
    w = getattr(importlib.import_module(f"sugarcode.modules.{m}.{s}"), n)
    assert getattr(pkg, n, None) is w and getattr(pkg, n) is not impl


@pytest.mark.parametrize("m,s,n,impl", ROUTED, ids=[f"{r[0]}.{r[2]}" for r in ROUTED])
def test_package_name_refuses_bad_seed_before_the_implementation(m, s, n, impl):
    f = getattr(importlib.import_module(f"sugarcode.modules.{m}"), n)
    req = [p for p in inspect.signature(f).parameters.values()
           if p.default is inspect.Parameter.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    args = [None] * len(req)
    with pytest.raises(TypeError, match=r"^seed must be an integer$"):
        f(*args, seed=True)
    with pytest.raises(ValueError, match=r"^seed must be between 0 and 9223372036854775807$"):
        f(*args, seed=2**63)


@pytest.mark.parametrize("m,n", sorted(ALIASES))
def test_alias_is_the_wrapper_and_core_name_is_untouched(m, n):
    pkg = importlib.import_module(f"sugarcode.modules.{m}")
    row = [r for r in ROWS if (r[0], r[2]) == (m, n)][0]
    w = getattr(importlib.import_module(f"sugarcode.modules.{m}.{row[1]}"), n)
    assert getattr(pkg, ALIASES[(m, n)]) is w and w.__wrapped__ is row[3]
    assert ALIASES[(m, n)] in pkg.__all__
    if n == "dock":
        assert pkg.dock is importlib.import_module(f"sugarcode.modules.{m}.core").dock
    else:
        assert not hasattr(pkg, n)
    req = [p for p in inspect.signature(w).parameters.values()
           if p.default is inspect.Parameter.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    args = [None] * len(req)
    with pytest.raises(TypeError, match=r"^seed must be an integer$"):
        w(*args, seed=True)
    with pytest.raises(ValueError, match=r"^seed must be between 0 and 9223372036854775807$"):
        w(*args, seed=2**63)


def test_deep_list_seed_through_a_package_name_is_refused_in_a_subprocess():
    body = ("import sys; sys.setrecursionlimit(10**7); s = []\nfor _ in range(100000): s = [s]\n"
            "from sugarcode.modules.cellpainter_4d import simulate_population_4d as f\n"
            "f('apoptosis', {'area_um2': 200, 'circularity': .85, 'aspect_ratio': 1.2, 'intensity': 100, 'cell_count': 300}, duration_h=6, seed=s)\n")
    r = subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, timeout=120)
    assert r.returncode == 1 and r.stderr.strip().splitlines()[-1] == "TypeError: seed must be an integer"
