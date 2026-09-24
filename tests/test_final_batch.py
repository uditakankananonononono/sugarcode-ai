import numpy as np
import pytest

from sugarcode.modules.chemgpt_engine import generate, score_molecule, pareto_front
from sugarcode.modules.bioprint_pro import calibrate
from sugarcode.modules.bioplayground import run_sandbox
from sugarcode.modules.biosimvr import LabScene, run_session
from sugarcode.modules.synlife_evo import evolve
from sugarcode.modules.neuro_pipeline import train, lesion_study, activation_trace, rsa
from sugarcode.modules.biogpt_lit import KnowledgeGraph
from sugarcode.modules.bio_copilot import mutation_to_phenotype, answer, to_fasta, to_pdb
from sugarcode.modules.synbio_wizard import run_wizard
from sugarcode.modules.enterprise_bio import TIERS, Entitlements
from sugarcode.modules.nexus_support import triage, SUBNETWORK_OWNERS


def test_chemgpt_scores_admet():
    m = score_molecule(["benzene", "carboxyl", "methyl"])
    assert m["mw"] > 0 and m["lipinski_violations"] == 0
    assert -5 < m["logP"] < 8


def test_chemgpt_pareto_not_empty():
    r = generate(n=15, target_logp=2.5, seed=3)
    assert r["pareto_size"] >= 1
    for c in r["pareto_front"]:
        assert "retrosynthesis" in c
        assert len(c["objectives"]) == 5


def test_chemgpt_unknown_fragment():
    with pytest.raises(KeyError):
        score_molecule(["unobtanium"])


def test_bioprint_window_and_crosslink():
    r = calibrate("gelma_10pct")
    assert any(w["printable"] for w in r["printability_window"])
    assert r["recommended"] is not None
    assert r["crosslinking"]["t95_s"] > 0
    assert r["structural_integrity"]["modulus_kPa_at_10s"] > 12.0  # grows past E0


def test_bioprint_unknown_ink():
    with pytest.raises(KeyError):
        calibrate("molten_steel")


def test_bioplayground_construct_retained_with_advantage():
    r = run_sandbox(pop_size=300, generations=200, fitness=[1.02, 0.98, 0.98], seed=5)
    assert r["final_construct_freq"] > 0.5
    assert r["construct_retained"]


def test_bioplayground_costly_construct_lost():
    r = run_sandbox(pop_size=100, generations=400, fitness=[0.85, 1.0, 1.0],
                    mutation_rate=5e-2, seed=5)
    assert not r["construct_retained"]
    assert r["final_construct_freq"] < 0.5  # collapsed to mutation-selection balance
    assert r["interpretation"]


def test_biosimvr_crispr_session():
    r = run_session("crispr_transfection")
    assert len(r["observations"]) >= 3
    assert r["action_log"]
    assert "confirm indels" in r["conclusion"]


def test_biosimvr_labscene_mechanics():
    lab = LabScene()
    lab.add("a", "bench", (0, 0, 0))
    lab.add("b", "plate", (3, 4, 0))
    assert lab.move_to("a", "b") == pytest.approx(5.0)
    with pytest.raises(ValueError):
        lab.interact("a", "pipette", volume_uL=5000)


def test_synlife_evo_burden_silences_pathway():
    r = evolve(generations=1500, burden_cost=0.25, selection_on_yield=0.1,
               mutation_rate=5e-3, seed=2)
    assert r["pathway_silenced"]
    assert r["silencing_onset_gen"] is not None
    assert r["design_recommendations"]


def test_synlife_evo_balanced_survives():
    r = evolve(generations=1000, burden_cost=0.02, selection_on_yield=0.6,
               mutation_rate=1e-4, seed=2)
    assert not r["pathway_silenced"]


def test_neuro_pipeline_trains():
    r = train(epochs=400, seed=1)
    assert r["train_accuracy"] > 0.85
    assert r["final_loss"] < r["loss_curve"][0]


def test_neuro_pipeline_lesion_and_rsa():
    model = train(epochs=300, seed=1)["model"]
    ls = lesion_study(model)
    assert len(ls["lesions"]) == 12
    assert all("accuracy_drop" in l for l in ls["lesions"])
    x = np.random.default_rng(0).normal(0, 1, (1, 6))
    tr = activation_trace(model, x)
    assert tr["output"]
    rr = rsa(model)
    assert -1.0 <= rr["rsa_correlation"] <= 1.0


def test_biogpt_kg_evidence_and_contradiction():
    kg = KnowledgeGraph()
    kg.ingest({"id": "p1", "year": 2015, "citations": 500, "replicated": True,
               "claims": [{"subject": "drugX", "relation": "inhibits", "object": "kinaseY"}]})
    kg.ingest({"id": "p2", "year": 2021, "citations": 5,
               "claims": [{"subject": "drugX", "relation": "activates", "object": "kinaseY"}]})
    q = kg.query("drugX", "kinaseY")
    assert q["consensus"] == "inhibits"  # stronger evidence wins
    contra = kg.contradictions()
    assert len(contra) == 1
    assert contra[0]["subject"] == "drugx"


def test_biogpt_kg_multihop_and_hypotheses():
    kg = KnowledgeGraph()
    kg.ingest({"id": "a", "year": 2018, "citations": 10,
               "claims": [{"subject": "IL6", "relation": "activates", "object": "JAK"},
                          {"subject": "JAK", "relation": "activates", "object": "STAT3"}]})
    r = kg.multi_hop("IL6", "STAT3")
    assert r["connected"]
    assert r["paths"][0]["path"] == ["il6", "jak", "stat3"]
    h = kg.hypothesize("IL6")
    assert "hypotheses" in h


def test_copilot_mutation_to_phenotype_hotspot():
    r = mutation_to_phenotype("TP53", "R", 273, "H")
    assert r["phenotype"] in ("likely pathogenic", "uncertain significance")
    assert r["risk_score"] > 0.5
    assert len(r["computation_graph"]) == 4
    assert any(n["node"] == "structural_perturbation" for n in r["computation_graph"])


def test_copilot_benign_variant():
    r = mutation_to_phenotype("KRAS", "A", 150, "V")
    assert r["risk_score"] < 0.7


def test_copilot_unknown_gene():
    with pytest.raises(KeyError):
        mutation_to_phenotype("FAKEGENE", "A", 1, "V")


def test_copilot_structured_outputs():
    fasta = to_fasta("tp53_fragment", "MEEPQSDPSVEPPLSQETFSDLWKLLPEN")
    assert fasta.startswith(">tp53_fragment")
    pdb = to_pdb("MEEPQSDPSV")
    lines = pdb.splitlines()
    assert lines[0].startswith("ATOM") and lines[-1] == "END"
    assert len(lines) == 11  # 10 residues + END


def test_copilot_answer_routing(monkeypatch):
    # keep unit tests hermetic: force the named local fallback path
    import sugarcode.modules.bio_copilot.core as cc
    monkeypatch.setattr(cc, "live_gene_context",
                        lambda gene, offline=False: {"gene": gene,
                                                     "source": "local knowledge slice",
                                                     "warning": "test stub",
                                                     "local": cc.GENES.get(gene)})
    r = answer("What is the function of TP53 hotspots?")
    assert r["route"] == "gene_knowledge"
    assert r["grounding"] == "local knowledge slice"
    r2 = answer("how do I check a variant effect?")
    assert r2["route"] in ("variant_pipeline", "literature_synthesis")


def test_synbio_wizard_full_pipeline():
    r = run_wizard("vanillin", seed=9)
    assert r["steps"]["4_selected_chassis"]["chassis"] in CHASSIS_KEYS
    assert r["steps"]["5_assembly"]["method"] in ("Golden Gate", "Gibson")
    lo, hi = r["steps"]["6_yield_simulation"]["90pct_CI"]
    assert lo <= r["steps"]["6_yield_simulation"]["mean_titer_fraction"] <= hi
    assert 0.0 <= r["feasibility_score"] <= 1.0


CHASSIS_KEYS = {"E_coli", "S_cerevisiae", "CHO", "B_subtilis"}


def test_synbio_wizard_unknown_goal():
    with pytest.raises(KeyError):
        run_wizard("unobtanium_synthesis")


def test_enterprise_tier_gating():
    acad = Entitlements("academic")
    assert not acad.check_module_access("car_t_designer", 60)["allowed"]
    assert acad.check_module_access("gene_explorer", 5)["allowed"]
    assert not acad.use_vault()["allowed"]
    assert not acad.dispatch_robot(" colony picking ")["allowed"]
    ent = Entitlements("enterprise")
    assert ent.dispatch_robot("colony picking")["allowed"]


def test_enterprise_compute_quota():
    e = Entitlements("startup")
    assert e.consume_compute(600)["allowed"]
    r = e.consume_compute(500)
    assert not r["allowed"]
    assert "quota" in r["reason"]
    assert r["remaining_hours"] == 400


def test_nexus_triage_bug_routing():
    r = triage("CRISPR Opt crashes with a traceback on my guide input", module="crispr_opt")
    assert r["classification"] == "bug"
    assert r["routed_to"]["sub_network"] == "genome-editing"
    assert r["priority"] == "high"


def test_nexus_triage_custom_build_enterprise_sla():
    r = triage("we need a custom white-label build", tier="enterprise")
    assert r["classification"] == "custom_build"
    assert r["sla_hours"] == 120  # 240 * 0.5 enterprise


def test_nexus_module_map_covers_88():
    all_mods = [m for mods in SUBNETWORK_OWNERS.values() for m in mods]
    assert len(set(all_mods)) == 89
