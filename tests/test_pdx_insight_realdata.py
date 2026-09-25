"""Module 115 pdx_insight: identity checks - a PDX identical to its patient must read as faithful."""
from sugarcode.modules.pdx_insight import multiomic_fidelity, fidelity_assessment, monitor_pdx

P = {"mutations": ["KRAS_G12D", "TP53_R175H", "SMAD4_del"],
     "expression": {"EGFR": 5.1, "MYC": 7.2, "CDKN2A": 1.0, "VIM": 3.3}}


def test_unmeasured_layers_are_not_drift():
    r = multiomic_fidelity(P, P, 0)
    assert r["model_fidelity_index"] == 1.0 and r["translational_drift"] == []  # was 0.65 + 2 false flags
    assert r["layers_not_measured"] == ["copy_number", "methylation"]


def test_measured_layer_drift_still_flagged():
    x = dict(P, expression={"EGFR": 1.0, "MYC": 1.2, "CDKN2A": 7.0, "VIM": 6.3})
    r = multiomic_fidelity(P, x, 0)
    assert "expression drift" in r["translational_drift"] and r["model_fidelity_index"] < 0.8


def test_legacy_components_report_measured_values():
    r = fidelity_assessment(P, P, 10)
    assert r["components"]["mutation_retention"] == 1.0  # was .817 (.98**10 applied to data)
    assert r["components"]["expression_correlation"] == 1.0  # was .599
    assert r["component_basis"]["stroma_human_fraction"] == "passage prior"


def test_no_fabricated_correlation():
    r = fidelity_assessment({"mutations": ["A"]}, {"mutations": ["A"]}, 0)
    assert r["components"]["expression_correlation"] is None  # was a fabricated 0.5


def test_monitor_runs_on_partial_layers():
    r = monitor_pdx(P, [{"passage": 1, "profile": P}, {"passage": 4, "profile": dict(P, mutations=P["mutations"][:2])}])
    assert r["longitudinal"]["fidelity_slope_per_passage"] < 0 and len(r["diagnostics"]) == 50
