import numpy as np
from sugarcode.modules.phageforge import design_phage
from sugarcode.modules.cell_twin import create_twin, run_drug_trial
from sugarcode.modules.fate_predictor import predict_reprogramming
from sugarcode.modules.cellfatenet import lineage_network, transition_recipe
from sugarcode.modules.organoid_ai import design_organoid, simulate_growth, drug_response
from sugarcode.modules.bioimage_ai import analyze_image, count_cells
from sugarcode.modules.cellpainter import profile_perturbation, compare_profiles
from sugarcode.modules.cellpainter_4d import simulate_morphology
from sugarcode.modules.syndroid import simulate_minimal_cell
from sugarcode.modules.tissue_eng import design_tissue


def test_phageforge_design():
    gene = "ATG" + "GCTGCAATC" * 100 + "TAA" + "AGG" + "TTGCA" * 30
    r = design_phage(gene, "NDM-1")
    assert r["payload"]["fits"]
    assert r["payload"]["guides"]
    assert r["specificity"]["microbiome_sparing"] > 0


def test_cell_twin_trial():
    twin = create_twin({"mutations": [{"gene": "TP53", "driver_score": 0.9}],
                        "expression": {"MKI67": 80, "MYC": 50}})
    r = run_drug_trial(twin, ["cisplatin", "olaparib", "trametinib"])
    assert len(r["per_drug"]) == 3
    assert r["combinations"]
    assert twin["apoptosis_threshold"] > 0.5  # TP53 loss raises threshold


def test_fate_prediction_curated():
    r = predict_reprogramming("fibroblast", "neuron")
    assert r["curated"] and "ASCL1" in r["transcription_factors"]
    assert 0 < r["estimated_success_rate"] < 1
    assert r["protocol"]


def test_cellfatenet_recipe():
    net = lineage_network()
    assert net["edges"] and net["key_regulatory_nodes"]
    rec = transition_recipe("fibroblast", "neuron")
    assert rec["recipe"][0]["action"] == "overexpress"


def test_organoid_full():
    d = design_organoid("intestinal", ["APC"])
    assert "Wnt3a" in d["media_recipe"]["factors"]
    g = simulate_growth("intestinal", days=10)
    assert g["final_cells"] > 5000
    resp = drug_response("tumor", ["cisplatin", "olaparib"], ["BRCA1_rev"])
    assert resp["responses"]["olaparib"]["resistance_modifier"] > 0


def _synthetic_cells_image(n=5):
    img = np.zeros((100, 100))
    rng = np.random.default_rng(0)
    for _ in range(n):
        y, x = rng.integers(10, 90, 2)
        yy, xx = np.ogrid[:100, :100]
        img[((yy - y) ** 2 + (xx - x) ** 2) < 25] = 1.0
    return img


def test_bioimage_count_and_health():
    img = _synthetic_cells_image(6)
    c = count_cells(img.tolist())
    assert c["cell_count"] == 6
    a = analyze_image(img.tolist())
    assert a["cell_count"] == 6
    assert a["culture_health"]["confluence_pct"] > 0


def test_cellpainter_profiles():
    p1 = profile_perturbation("dna_damage", 10.0)
    p2 = profile_perturbation("dna_damage", 1.0)
    p3 = profile_perturbation("mitochondrial_toxin", 10.0)
    assert p1["fingerprint_strength"] > p2["fingerprint_strength"] * 0.5
    cmp = compare_profiles([p1, p2, p3])
    assert cmp["most_similar_pair"]["pair"][0] == "dna_damage"


def test_cellpainter_4d():
    r = simulate_morphology("differentiation", duration_h=48)
    assert len(r["traces"]["area"]) == 25
    assert r["morphological_drift"] > 0
    assert r["event_timeline"]


def test_syndroid_viable_and_nonviable():
    full = simulate_minimal_cell(list({"replication", "transcription", "translation",
                                       "metabolism", "membrane", "division"}), hours=8)
    assert full["viable"]
    dead = simulate_minimal_cell(["transcription", "translation"], hours=8)
    assert not dead["viable"]
    assert any("ATP" in b for b in dead["emergent_behaviors"])


def test_tissue_eng_cardiac():
    r = design_tissue("cardiac_patch", (10, 10, 3))
    assert r["vascularization"]["required"]
    assert r["mechanical_simulation"]["stress_strain"]["stress_kpa"]
    assert r["print_parameters"]["n_layers"] >= 1
