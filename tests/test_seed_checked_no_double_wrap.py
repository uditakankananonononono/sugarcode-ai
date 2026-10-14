"""No function is seed-guarded by both seed_checked.py and seed_gate.py, and every seed_checked wrapper wraps core directly (depth 1).

Independent of the wrappers' own tests: the expected per-module sets below are written out by hand, so a wrapper added to
both files, or a gate stacked on a gate, fails here.
"""
import importlib
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "src" / "sugarcode" / "modules"

# seed_checked.py wrappers that remain after de-duplication against seed_gate.py (numeric_b v2), by module
EXPECTED_CHECKED = {
    "neohunter": {"neoantigen_pipeline"},
    "neuro_pipeline": {"synthetic_promoter_dataset", "sequence_pipeline_demo", "train_on_sequences"},
    "synbio_wizard": {"compile_project", "run_wizard"},
    "synlife_evo": {"optimize_stability"},
    "synthetic_life": {"compile_synthetic_life"},
}
# modules whose numeric_b seed_checked.py was removed because seed_gate.py already wraps every function it covered
REMOVED = ["molecule_eval", "profile_hmm", "qsar_bench", "str_scope", "syn_bio_studio", "syn_stab_ai", "virtual_cell"]
# Functions seed_gate.py wraps, per module
GATE_FUNCS = {
    "virtual_cell": {"simulate_expression", "simulate_cell"},
    "synthetic_life": {"stochastic_control", "ale_trajectory"},
    "synlife_evo": {"evolve", "simulate_evolution_experiment", "simulate_competition"},
    "synbio_wizard": {"gillespie_expression", "uncertainty_distribution"},
    "syn_stab_ai": {"population_simulation"},
    "syn_bio_studio": {"gillespie_expression"},
    "str_scope": {"repeat_instability"},
    "neuro_pipeline": {"train", "lesion_study", "rsa", "predictive_coding_hierarchy", "pipeline_report", "neuro_diagnostics"},
    "molecule_eval": {"evaluate_library", "compare_libraries"},
    "neohunter": {"simulate_immune_escape"},
    "profile_hmm": {"random_profile_hmm"},
    "qsar_bench": {"validate_qsar"},
}


def _wrapped_names(mod):
    return {n for n, v in vars(mod).items() if callable(v) and not n.startswith("_") and hasattr(v, "__wrapped__")}


@pytest.mark.parametrize("m", sorted(EXPECTED_CHECKED))
def test_seed_checked_exports_exactly_the_expected_functions(m):
    mod = importlib.import_module(f"sugarcode.modules.{m}.seed_checked")
    assert _wrapped_names(mod) == EXPECTED_CHECKED[m]


@pytest.mark.parametrize("m", REMOVED)
def test_removed_modules_have_no_seed_checked_file(m):
    assert not (ROOT / m / "seed_checked.py").exists()


@pytest.mark.parametrize("m", sorted(GATE_FUNCS))
def test_seed_gate_defines_the_listed_functions(m):
    gate = importlib.import_module(f"sugarcode.modules.{m}.seed_gate")
    for fn in GATE_FUNCS[m]:
        assert callable(getattr(gate, fn)), (m, fn)


@pytest.mark.parametrize("m", sorted(GATE_FUNCS))
def test_no_function_wrapped_by_both(m):
    both = ROOT / m / "seed_checked.py"
    if not both.exists():
        return
    checked = _wrapped_names(importlib.import_module(f"sugarcode.modules.{m}.seed_checked"))
    assert checked.isdisjoint(GATE_FUNCS[m]), checked & GATE_FUNCS[m]


@pytest.mark.parametrize("m", sorted(EXPECTED_CHECKED))
def test_wrapper_chain_depth_is_one(m):
    mod = importlib.import_module(f"sugarcode.modules.{m}.seed_checked")
    for n in EXPECTED_CHECKED[m]:
        inner = getattr(mod, n).__wrapped__
        assert not hasattr(inner, "__wrapped__"), (m, n)
        assert inner is getattr(importlib.import_module(f"sugarcode.modules.{m}.core"), n)


# ---- scan of every guard file in every module (seed_checked*.py, seed_guard.py, seed_gate.py) ----
EXPECTED_GUARD = {"stability_ai": {"analyze_stability", "analyze_stability_v2"}, "syndroid": {"mechanistic_cell_program", "design_syndroid"}}


def _guard_files(pkg_dir):
    return sorted(p for pat in ("seed_checked*.py", "seed_guard.py", "seed_gate.py") for p in pkg_dir.glob(pat))


def _names_in(path, mod):
    out = set()
    for n, v in vars(mod).items():
        if n.startswith("_") or not callable(v):
            continue
        if getattr(v, "__wrapped__", None) is not None or getattr(v, "__module__", None) == mod.__name__:
            out.add(n)
    return out


def _all_guards():
    result = {}
    for pkg_dir in sorted(ROOT.iterdir()) + [ROOT.parent / "llm"]:
        if not pkg_dir.is_dir():
            continue
        per_file = {}
        for p in _guard_files(pkg_dir):
            mod = importlib.import_module(f"sugarcode.{'llm' if pkg_dir.name == 'llm' else 'modules.' + pkg_dir.name}.{p.stem}")
            per_file[p.name] = _names_in(p, mod)
        if per_file:
            result[pkg_dir.name] = per_file
    return result


GUARDS = _all_guards()


def test_scan_sees_the_known_guard_files():
    assert "seed_gate.py" in GUARDS["neuro_pipeline"] and "seed_checked.py" in GUARDS["neuro_pipeline"]
    assert "seed_guard.py" in GUARDS["stability_ai"] and "seed_gate.py" in GUARDS["stability_ai"]


@pytest.mark.parametrize("pkg", sorted(GUARDS))
def test_no_function_guarded_by_two_files(pkg):
    files = GUARDS[pkg]
    names = sorted(files)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert files[a].isdisjoint(files[b]), (pkg, a, b, files[a] & files[b])


@pytest.mark.parametrize("pkg", sorted(EXPECTED_GUARD))
def test_seed_guard_py_exports_exactly_the_expected_functions(pkg):
    assert GUARDS[pkg]["seed_guard.py"] - {"check_seed", "MAX_SEED"} == EXPECTED_GUARD[pkg]


def test_train_softmax_is_guarded_exactly_once_by_llm_seed_checked_router():
    assert GUARDS["llm"] == {"seed_checked_router.py": {"train_softmax"}}


def test_study_residual_file_is_gone_and_lesion_study_rsa_are_gate_only():
    assert not (ROOT / "neuro_pipeline" / "seed_checked_study.py").exists()
    assert {"lesion_study", "rsa"} <= GUARDS["neuro_pipeline"]["seed_gate.py"]
    assert not {"lesion_study", "rsa"} & GUARDS["neuro_pipeline"]["seed_checked.py"]
