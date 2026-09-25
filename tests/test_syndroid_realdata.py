"""Module 123 syndroid: MILP genome design contracts, SSA event-count honesty,
and minimal-cell input validation. Catalog anchors: JCVI-syn3.0 minimal cell
(Hutchison 2016, PMID 27013737)."""
import numpy as np
import pytest
from sugarcode.modules.syndroid.core import (simulate_minimal_cell,
    optimize_minimal_genome, stochastic_gene_expression, design_syndroid)


def test_unknown_module_rejected():
    with pytest.raises(ValueError):
        simulate_minimal_cell(["photosynthesis"])  # was: silently ignored, viable cell


def test_environment_medium_now_rescues_glyA():
    rich = optimize_minimal_genome(environment={"medium": "rich"})
    minimal = optimize_minimal_genome(environment={"medium": "minimal"})
    assert "glyA" not in rich["genes"] and "glyA" in minimal["genes"]
    assert minimal["gene_count"] == rich["gene_count"] + 1  # 13 vs 12 measured


def test_ssa_event_counts_are_honest():
    e = stochastic_gene_expression(["g%d" % i for i in range(50)], minutes=240)
    assert e["total_event_count"] > e["stored_event_count"]  # 49761 vs 1000 measured
    assert e["stored_event_count"] == 1000 and e["truncated"] is False


def test_minimal_cell_phenotypes():
    no_met = simulate_minimal_cell(["replication", "translation", "division"])
    assert no_met["viable"] is False and "ATP depletion" in no_met["emergent_behaviors"][0]
    mods = ["replication", "transcription", "translation", "metabolism", "membrane", "division"]
    full = simulate_minimal_cell(mods, hours=10)
    assert full["final_cells"] >= 1 and full["viable"] is True
    starved = simulate_minimal_cell(mods, hours=80)  # glucose exhausted -> ATP crash
    assert any("substrate exhaustion" in b for b in starved["emergent_behaviors"])
    assert starved["viable"] is False  # honest non-viability after starvation
    assert isinstance(full["viable"], bool)  # was numpy.bool_: broke json.dumps


def test_design_pipeline_end_to_end_reproducible():
    a = design_syndroid(hours=12, seed=7)
    b = design_syndroid(hours=12, seed=7)
    assert a["diagnostics"] == b["diagnostics"] and len(a["diagnostics"]) == 51
