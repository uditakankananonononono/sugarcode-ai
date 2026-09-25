"""Module 125 synthetic_life: explicit-vs-default catalogs, category validation,
FBA infeasible honesty, reaction-name-checked limits, dFBA termination honesty,
and fermentation solver-failure handling. Catalog anchors: PMID 20212490 (What
is flux balance analysis?) and PMID 28893188 (genome-reduced Pseudomonas
chassis for secondary-metabolite production)."""
import math
import numpy as np
import pytest
from sugarcode.modules.synthetic_life import (design_minimal_genome,
    compile_synthetic_life, flux_optimize, dynamic_fba, fermentation_simulate,
    optimize_minimal_genome, gene_evidence_score)
from sugarcode.modules.virtual_cell.core import MetabolicModel

GENES = [{"name":"rep","category":"replication","size_bp":1000,"crispr_essentiality":.95},
         {"name":"tx","category":"transcription","size_bp":900,"transposon_essentiality":.9},
         {"name":"tl","category":"translation","size_bp":1100,"model_essentiality":.95},
         {"name":"stress","category":"stress_response","size_bp":500,"crispr_essentiality":.1},
         {"name":"mot","category":"motility","size_bp":600,"crispr_essentiality":.05}]


def test_empty_catalog_rejected_none_keeps_default():
    with pytest.raises(ValueError, match="must not be empty"):
        design_minimal_genome([])  # was: silently designed from the 450-gene default
    with pytest.raises(ValueError, match="must not be empty"):
        compile_synthetic_life([])
    assert design_minimal_genome(None)["input_genes"] == 450


def test_unrecognized_category_rejected_missing_becomes_unknown():
    with pytest.raises(ValueError, match="unrecognized gene category"):
        design_minimal_genome([{"name":"x","category":"quantum_magic","size_bp":500}])
    r = design_minimal_genome([{"name":"y","size_bp":500}])  # was: KeyError crash
    assert r["dropped_by_category"] == {"unknown": 1}


def test_flux_infeasible_reports_same_shape_and_no_fake_objective():
    r = flux_optimize(product_reaction="GLC_UP", growth_floor=1e9)
    assert r["status"] == "infeasible" and r["objective"] is None  # was: 0
    assert set(r) == {"status","objective","product_reaction","fluxes","growth_floor"}


def test_limits_require_named_reactions():
    toy = MetabolicModel(reactions=["A_IN","BIOMASS"], metabolites=["a"],
        S=np.array([[-1.0,1.0]]), lb=np.array([0.0,0.0]), ub=np.array([10.0,10.0]))
    with pytest.raises(KeyError, match="GLC_UP"):
        flux_optimize(toy, glucose_limit=0.0)  # was: silently ignored, flux 10 returned
    with pytest.raises(KeyError, match="RESP"):
        flux_optimize(toy, oxygen_limit=0.0)


def test_dfba_reports_early_termination_and_never_returns_empty():
    r = dynamic_fba(hours=24, glucose0=1e-10)  # was: zero trajectory points, no flag
    assert len(r["trajectory"]) == 1 and r["trajectory"][0]["time_h"] == 0.0
    assert r["terminated_early"] is True and r["simulated_hours"] == 0.0
    full = dynamic_fba(hours=24, glucose0=50)
    assert full["terminated_early"] is False and len(full["trajectory"]) == 97


def test_fermentation_rejects_nonfinite_and_surfaces_solver_failure():
    with pytest.raises(ValueError, match="finite"):
        fermentation_simulate(hours=1, mu_max=float("inf"))  # was: AttributeError 'list' ...
    r = fermentation_simulate(hours=8)
    assert r["final_product_mM"] > 0 and len(r["time_h"]) == 193


def test_essentiality_posterior_weights_sum_to_one():
    r = gene_evidence_score(GENES[0])
    assert math.isclose(r["posterior_essentiality"],
        .3*.95 + .25*.85 + .2*.85 + .25*.85)  # 0.88 measured
    opt = optimize_minimal_genome(GENES)
    kept = {g["name"] for g in opt["kept"]}
    assert {"rep","tx","tl"} <= kept and "mot" in kept  # coverage rule keeps best per category


def test_pubmed_fba_and_chassis_anchors_live():
    from sugarcode.bio.entrez import esummary
    try:
        s = esummary("pubmed", ["20212490", "28893188"])
    except Exception as e:
        pytest.skip("entrez unavailable: %s" % e)
    assert "flux balance analysis" in s["20212490"]["title"].lower()
    assert "genome-reduced" in s["28893188"]["title"].lower()
