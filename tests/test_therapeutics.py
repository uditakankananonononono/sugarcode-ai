import pytest

from sugarcode.modules.neohunter import find_neoantigens, hla_binding
from sugarcode.modules.car_t_designer import design_car
from sugarcode.modules.living_tx import design_living_therapeutic
from sugarcode.modules.gene_tx_opt import optimize_gene_therapy
from sugarcode.modules.vector_opt import engineer_capsid
from sugarcode.modules.organoid_screen import screen
from sugarcode.modules.neuroplan_ai import plan_surgery
from sugarcode.modules.neodti_engine import repurposing_scan
from sugarcode.modules.liquid_biopsy import detect_ctdna
from sugarcode.modules.rarenet_ai import diagnose
from sugarcode.modules.oncocircuit import design_oncocircuit
from sugarcode.modules.pdx_insight import fidelity_assessment
from sugarcode.modules.infinite_diagnosis import cross_domain_diagnosis

NORMAL = ("MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKAL"
          "PDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMG")


def test_neohunter_finds_mutant_binders():
    mut = NORMAL[:40] + "Y" + NORMAL[41:]
    r = find_neoantigens(mut, NORMAL, mutation_pos=40, hlas=["A*02:01"])
    cands = r.get("candidates") or r.get("neoantigens")
    assert len(cands) >= 1
    for c in cands[:3]:
        pep = c.get("peptide", c.get("mutant_peptide", ""))
        assert "Y" in pep


def test_neohunter_rejects_identical_sequences():
    with pytest.raises((ValueError, KeyError, IndexError)):
        find_neoantigens(NORMAL, NORMAL, mutation_pos=0)


def test_hla_binding_scores_peptide():
    r = hla_binding("YLQLRLFGK", "A*02:01")
    assert 0.0 <= r.get("percentile", 0.5) <= 100.0
    assert any(k in r for k in ("score", "affinity_nM", "ic50_nM"))


def test_hla_binding_unknown_allele_raises():
    with pytest.raises(KeyError):
        hla_binding("YLQLRLFGK", "HLA-Z*99:99")


def test_car_t_designer_cd19():
    r = design_car("CD19", indication="B-ALL")
    assert r["antigen"] == "CD19"
    assert "scfv" in r["construct"]
    assert r["safety_switches"]
    assert 0.0 <= r["toxicity_prediction"]["crs_grade2plus_risk"] <= 1.0


def test_car_t_designer_unknown_antigen_raises():
    with pytest.raises((KeyError, ValueError)):
        design_car("NOT_A_REAL_ANTIGEN_XYZ")


def test_living_tx_design():
    r = design_living_therapeutic("IL-10")
    assert r["payload"] == "IL-10"
    containment = r["genetic_program"]["containment"]
    assert any("kill switch" in c.lower() for c in containment)


def test_gene_tx_opt_tissue_route():
    r = optimize_gene_therapy("liver", transgene_kb=3.5, route="iv")
    assert r["tissue"] == "liver"
    assert r["selected"] is not None
    assert r["selected"]["fits_transgene"]
    assert r["promoter_recommended"] in r["promoter_options"]
    assert 0.0 < r["efficiency_estimate"] <= 1.0


def test_gene_tx_opt_oversized_transgene_selects_nothing():
    r = optimize_gene_therapy("retina", transgene_kb=9.0, route="intravitreal")
    assert r["selected"] is None  # no AAV fits 9 kb - honest refusal
    assert not any(v["fits_transgene"] for v in r["vector_ranking"])


def test_vector_opt_capsid_variants():
    r = engineer_capsid("AAV9", target_receptor="generic", nab_escape=True,
                        n_variants=4, seed=7)
    variants = r.get("variants", r)
    assert len(variants) == 4
    for v in variants:
        assert isinstance(v, dict)


def test_organoid_screen_ranks_compounds():
    r = screen("colon", compounds=["5-FU", "oxaliplatin", "trametinib"],
               mutations=["KRAS_G12D"])
    results = r.get("results", r.get("ranking"))
    assert len(results) == 3


def test_neuroplan_ai_corridor_plan():
    r = plan_surgery({"center": (40, 40, 40), "radius": 8}, image_size=(96, 96, 96))
    assert r["corridor_options"]
    assert "recommended_corridor" in r
    assert r["segmentation"]["tumor_volume_mm3"] > 0
    assert 0.0 <= r["risk_score"] <= 1.0


def test_neodti_engine_repurposing_hits():
    r = repurposing_scan("breast cancer", top_n=5)
    assert 1 <= len(r["candidates"]) <= 5
    assert r["docking_validation"] is not None
    top = r["candidates"][0]
    assert 0.0 < top["therapeutic_resilience_index"] <= 1.0


def test_neodti_engine_excludes_approved_indication():
    r = repurposing_scan("GERD", top_n=5)  # cimetidine already approved -> excluded
    assert all(c["drug"] != "cimetidine" for c in r["candidates"])


def test_neodti_engine_unknown_disease_raises():
    with pytest.raises(KeyError):
        repurposing_scan("totally invented disease xyz")


def test_liquid_biopsy_detects_low_af():
    sig = [0.01, 0.008, 0.012, 0.005, 0.011, 0.009, 0.011, 0.007,
           0.01, 0.006, 0.012, 0.008]
    r = detect_ctdna(sig, tumor_type="lung", depth=30000)
    assert r["ctdna_detected"] is True
    assert r["candidates"]
    assert r["estimated_sensitivity"] > 0.0


def test_liquid_biopsy_clean_sample_negative():
    sig = [0.00001, 0.0, 0.00002] * 4
    r = detect_ctdna(sig, tumor_type="lung", depth=30000)
    assert r["ctdna_detected"] is False
    assert r["estimated_sensitivity"] == 0.0


def test_liquid_biopsy_requires_min_trace():
    with pytest.raises(ValueError):
        detect_ctdna([0.001, 0.0008], tumor_type="lung", depth=30000)


def test_rarenet_ai_diagnose_symptoms():
    r = diagnose(symptoms=["fatigue", "hypotonia", "seizures"],
                 variants=[{"gene": "MT-ND5", "type": "missense"}])
    cands = r.get("candidates", r.get("diagnoses"))
    assert len(cands) >= 1


def test_oncocircuit_two_input_and_gate():
    r = design_oncocircuit("breast", payload="caspase3", two_input=True)
    logic = str(r.get("logic", r))
    assert "AND" in logic or "and" in logic


def test_pdx_insight_fidelity_drift():
    patient = {"mutations": ["TP53_R273H", "KRAS_G12D"], "histology": "adenocarcinoma",
               "copy_number": {"MYC": 6, "PTEN": 1}}
    pdx = {"mutations": ["TP53_R273H"], "histology": "adenocarcinoma",
           "copy_number": {"MYC": 8, "PTEN": 1}}
    r = fidelity_assessment(patient, pdx, passage=5)
    assert 0.0 <= r["model_fidelity_index"] <= 1.0
    assert r["translational_drift"]  # flags lost driver / stroma replacement
    assert "verdict" in r


def test_infinite_diagnosis_cross_domain(monkeypatch):
    from sugarcode.modules.infinite_diagnosis import core as _idx
    monkeypatch.setattr(_idx, "pubmed_ids", lambda q, retmax=10, offline=False: [])
    r = cross_domain_diagnosis("child with developmental delay, lactic acidosis, muscle weakness")
    clusters = r["hidden_clusters"]
    assert len(clusters) >= 1
    joined = str(clusters).lower()
    assert any(k in joined for k in ("genome", "cell", "variant", "diagnos"))
