import math
import numpy as np
import pytest
from sugarcode.modules.neuro_pipeline import (one_hot_encode, kmer_encode,
    synthetic_promoter_dataset, train_on_sequences, lesion_study, train)


def test_dataset_shape_balance_and_motif_placement():
    d = synthetic_promoter_dataset(n=200, seq_len=50, motif="TATAAA", seed=1)
    seqs, labels = d["sequences"], d["labels"].ravel()
    assert len(seqs) == 200 and len(labels) == 200
    assert all(len(s) == 50 for s in seqs)
    assert labels.sum() == 100  # balanced classes
    for s, y in zip(seqs, labels):
        assert ("TATAAA" in s) == bool(y)  # motif exactly in positives


def test_one_hot_and_kmer_known_values():
    X = one_hot_encode(["ACGT"])
    assert X.shape == (1, 16)
    # A->index0, C->1, G->2, T->3 within each 4-slot
    assert X[0, 0] == X[0, 5] == X[0, 10] == X[0, 15] == 1.0
    assert X.sum() == 4.0
    X2 = one_hot_encode(["AC", "ACGT"])  # zero-pad shorter
    assert X2.shape == (2, 16) and X2[0, 8:].sum() == 0.0
    K = kmer_encode(["AAAA"], k=2)
    assert K.shape == (1, 16)
    # "AAAA" has three AA 2-mers, all mass on the AA column (index 0)
    assert K[0, 0] == 1.0 and K.sum() == 1.0


def test_train_on_sequences_default_accuracy_seed_pinned():
    r = train_on_sequences(seed=42)
    assert r["train_accuracy"] > 0.9
    r2 = train_on_sequences(seed=42)
    assert r2["train_accuracy"] == r["train_accuracy"]
    assert r2["final_loss"] == r["final_loss"]


def test_user_supplied_sequences_and_bad_base():
    seqs = ["AAATATAAACC", "GGGCGCGCGCG", "TTTATAAATTT", "CGCGCGCGCGC"]
    r = train_on_sequences(seqs, [1, 0, 1, 0], epochs=300, seed=0)
    assert r["n_sequences"] == 4 and r["train_accuracy"] >= 0.75
    assert r["dataset"] == "user-supplied sequences"
    with pytest.raises(ValueError):
        one_hot_encode(["ACGTN"])
    with pytest.raises(ValueError):
        kmer_encode(["ACGTX"], k=2)
    with pytest.raises(ValueError):
        train_on_sequences(["ACGT"])  # labels required


def test_lesion_study_on_sequence_features():
    r = train_on_sequences(seed=42, epochs=200)
    data = synthetic_promoter_dataset(seed=42)
    X = one_hot_encode(data["sequences"])
    out = lesion_study(r["model"], X=X, y=data["labels"])
    assert out["baseline_accuracy"] > 0.8
    assert len(out["lesions"]) == r["model"].W1.shape[1]
    assert all(math.isfinite(e["accuracy_drop"]) for e in out["lesions"])


def test_train_plasticity_note_no_longer_claims_ewc():
    note = train(epochs=50, seed=0)["plasticity_note"]
    assert "STDP" in note
    assert "EWC-style penalty hook" not in note
    assert "continual_update" in note
