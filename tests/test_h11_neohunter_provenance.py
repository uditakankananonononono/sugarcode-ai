"""AUTHORED, NOT RUN. H11: provenance/honesty metadata for the neohunter ridge PSSM. Base 1463a9201bff0c90c321ab43ebd64535d1d52ac5.
Written BEFORE the code, JSON and trainer edits. No weight or per-allele numeric change; stored r/AUC are stored source values,
not validated performance. The IEDB 9-mer logistic model (iedb_pssm_9mer.json / hla_binding_iedb) is out of scope."""
import json
from pathlib import Path

from sugarcode.modules.neohunter import core as nh
from sugarcode.modules.neohunter.core import hla_binding, hla_binding_trained

CAVEAT = ("stored held-out r/AUC describe the 80%-fit model, not the shipped all-row model; "
          "stored source values, not validated performance")
SPLIT = "about 20% held out; exact split not reproducible from available artifacts"
JSON_PATH = Path(nh.__file__).with_name("data_pssm_iedb2013.json")
DATA = json.load(open(JSON_PATH))
TRAINER = Path(__file__).resolve().parents[1] / "scripts" / "train_neohunter_pssm.py"

# stored source values as they stand at the base (pinned so a metadata edit cannot move a number)
STORED = {"HLA-A*02:01": (6038, 1220, 0.7859, 0.9243), "HLA-A*03:01": (2844, 564, 0.7571, 0.8978),
          "HLA-A*24:02": (1712, 318, 0.7448, 0.9136), "HLA-B*07:02": (1957, 383, 0.7369, 0.8872),
          "HLA-B*44:03": (531, 119, 0.7493, 0.8404)}


def test_json_top_level_provenance_keys():
    assert DATA["fit_all_rows"] is True
    assert DATA["metrics_describe_model"] == "80pct-fit"
    assert DATA["split_description"] == SPLIT
    assert set(DATA) == {"source", "target", "method", "fit_all_rows", "metrics_describe_model", "split_description",
                         "n_train_total_semantics", "near_neighbour_note", "alleles"}


def test_json_notes_are_attributed_not_invented():
    assert "ALL rows" in DATA["n_train_total_semantics"] and "n_heldout" in DATA["n_train_total_semantics"]
    note = DATA["near_neighbour_note"]
    assert "STATUS.md:750" in note and "about 12%" in note and "A*02:01" in note
    assert "not reproduced" in note


def test_no_per_allele_metadata_duplication_and_numbers_unchanged():
    assert set(DATA["alleles"]) == set(STORED)
    for al, m in DATA["alleles"].items():
        assert set(m) == {"n_train_total", "n_heldout", "heldout_pearson_r", "heldout_auc_ic50_lt_500nM", "bias", "weights"}, al
        assert (m["n_train_total"], m["n_heldout"], m["heldout_pearson_r"], m["heldout_auc_ic50_lt_500nM"]) == STORED[al], al
        assert sorted(m["weights"]) == [str(i) for i in range(9)] and all(len(w) == 20 for w in m["weights"].values())


def test_returned_dict_keeps_existing_keys_and_adds_exact_caveat():
    r = hla_binding_trained("GILGFVFTL", "A*02:01")
    for k in ("peptide", "hla", "score", "predicted_ic50_nM", "class", "method", "heldout_pearson_r",
              "heldout_auc_ic50_lt_500nM"):
        assert k in r, k
    assert r["metrics_caveat"] == CAVEAT
    assert r["heldout_pearson_r"] == STORED["HLA-A*02:01"][2] and r["heldout_auc_ic50_lt_500nM"] == STORED["HLA-A*02:01"][3]


def test_hla_binding_9mer_passes_caveat_through_and_heuristic_has_none():
    assert hla_binding("GILGFVFTL", "A*02:01")["metrics_caveat"] == CAVEAT
    assert "metrics_caveat" not in hla_binding("LLFGYPVY", "A*02:01")


def test_docstring_warns_metrics_describe_80pct_fit():
    d = hla_binding_trained.__doc__
    assert "80%-fit" in d and "NOT the shipped" in d and "not validated performance" in d


def test_trainer_source_emits_future_provenance_fields():
    # text check only: the trainer is NOT imported or run
    t = TRAINER.read_text()
    for needle in ('"metric_fit_size"', '"fit_all_rows"', '"metrics_describe_model"', '"split_description"',
                   '"n_train_total_semantics"'):
        assert needle in t, needle
    assert "int((~test).sum())" in t
