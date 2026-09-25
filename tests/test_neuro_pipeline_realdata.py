"""Module 111 neuro_pipeline on real E. coli promoters (UCI ML repository dataset 67,
Harley-Reynolds / Towell: 53 promoters + 53 non-promoters, 57 nt)."""
from pathlib import Path
import numpy as np
import pytest
from sugarcode.modules.neuro_pipeline import (train_on_sequences, predict_sequences, rsa,
                                              lesion_study, synthetic_promoter_dataset,
                                              sequence_pipeline_demo)

DATA = Path(__file__).parent / "data" / "uci_ecoli_promoters.data"


def _load():
    rows = [l.strip().split(",") for l in DATA.read_text().splitlines() if l.strip()]
    return [r[2].strip().upper() for r in rows], [1.0 if r[0] == "+" else 0.0 for r in rows]


def test_real_promoters_report_holdout():
    seqs, y = _load()
    assert len(seqs) == 106 and sum(y) == 53 and {len(s) for s in seqs} == {57}
    r = train_on_sequences(seqs, y, encoding="kmer", k=3)
    assert r["n_holdout"] == 22 and r["n_train"] == 84
    assert r["holdout_accuracy"] is not None and 0.6 < r["holdout_accuracy"] <= 1
    assert abs(r["generalization_gap"] - (r["train_accuracy"] - r["holdout_accuracy"])) < 2e-3


def test_holdout_is_stratified_and_disjoint():
    seqs, y = _load()
    r = train_on_sequences(seqs, y, epochs=10)
    te = r["holdout_index"]
    assert sum(y[i] for i in te) == 11 and len(set(te)) == 22


def test_default_demo_exposes_overfit():
    r = train_on_sequences()
    assert r["train_accuracy"] > 0.9
    assert r["generalization_gap"] > 0.2  # one-hot memorises; the gap is now visible


def test_predict_new_lengths_and_rsa_on_sequence_model():
    r = train_on_sequences(epochs=50)
    p = predict_sequences(r, ["TATAAA" + "A" * 10, "C" * 80])
    assert p.shape == (2,) and np.all((p >= 0) & (p <= 1))
    assert np.isfinite(rsa(r["model"])["rsa_correlation"])
    assert np.isfinite(lesion_study(train_on_sequences(encoding="kmer", epochs=50)["model"])["baseline_accuracy"])


def test_demo_lesions_holdout():
    d = sequence_pipeline_demo()
    assert d["lesion_data"] == "held-out sequences"
    assert d["lesion_on_sequences"]["baseline_accuracy"] == d["training"]["holdout_accuracy"]


def test_bad_args():
    with pytest.raises(ValueError):
        train_on_sequences(encoding="bpe")
    with pytest.raises(ValueError):
        train_on_sequences(holdout=1.0)
