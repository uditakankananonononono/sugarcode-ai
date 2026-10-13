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
# functions seed_gate.py wraps (lane 5 coverage list), per module
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
