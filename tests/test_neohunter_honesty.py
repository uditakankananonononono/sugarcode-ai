import json
from pathlib import Path
import pytest
from sugarcode.modules.neohunter import core as nh
from sugarcode.modules.neohunter.core import hla_binding, hla_binding_trained
from omega.registry import REGISTRY

DATA = json.load(open(Path(nh.__file__).with_name("data_pssm_iedb2013.json")))


def test_trained_matrix_has_real_heldout_performance_for_every_allele():
    assert set(DATA["alleles"]) == {"HLA-A*02:01", "HLA-A*03:01", "HLA-A*24:02", "HLA-B*07:02", "HLA-B*44:03"}
    for al, m in DATA["alleles"].items():
        assert m["n_train_total"] > 400 and m["n_heldout"] > 100, al
        assert m["heldout_auc_ic50_lt_500nM"] > 0.83 and m["heldout_pearson_r"] > 0.7, al


def test_known_epitope_vs_non_binder():
    flu = hla_binding_trained("GILGFVFTL", "A*02:01")      # influenza M1 58-66, classic strong A2 binder
    junk = hla_binding_trained("KKKKDDDDE", "A*02:01")
    assert flu["predicted_ic50_nM"] < 500 and flu["class"] in ("strong binder", "weak binder")
    assert junk["class"] == "non-binder" and junk["predicted_ic50_nM"] > flu["predicted_ic50_nM"] * 10
    assert "IEDB" in hla_binding("GILGFVFTL", "A*02:01")["method"]


def test_allele_specificity_is_learned():
    # A*03:01 prefers C-terminal K/R; A*02:01 prefers hydrophobic anchors
    k = "KLFGYPVYK"
    assert hla_binding_trained(k, "A*03:01")["score"] > hla_binding_trained(k, "A*02:01")["score"]


def test_non_9mer_falls_back_to_disclosed_heuristic():
    r = hla_binding("LLFGYPVY", "A*02:01")
    assert "heuristic" in r["method"] and "predicted_ic50_nM" not in r


def test_registry_text():
    s = REGISTRY["neohunter"].summary
    assert "IEDB" in s and "9-mer" in s
