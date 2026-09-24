"""Regression tests for the genomegpt audit defects (deletions, TF-binding deltas, splice risk, TADs)."""
import random

import pytest

from sugarcode.modules.genomegpt.core import (
    cryptic_splice_risk, local_tf_binding, motif_energy, propose_regulatory_edits, reconstruct_contact_map,
    simulate_edit, splice_sites, tad_boundaries, variant_mechanistic_deltas,
)

random.seed(7)
BG = "".join(random.choice("ACGT") for _ in range(3000))
CTCF = "CCGCGAGGCGGCAG"


def rc(s):
    return s[::-1].translate(str.maketrans("ACGT", "TGCA"))


def test_simulate_edit_handles_deletion_insertion_substitution():
    seq = BG[:200]
    deleted = simulate_edit(seq, 50, 57, "")
    assert deleted["edit_type"] == "deletion" and deleted["length_delta"] == -7
    assert deleted["edited_sequence"] == seq[:50] + seq[57:]
    assert simulate_edit(seq, 50, 50, "GG")["edit_type"] == "insertion"
    assert simulate_edit(seq, 50, 52, "A")["edit_type"] == "substitution"
    with pytest.raises(ValueError):
        simulate_edit(seq, 0, len(seq), "")
    with pytest.raises(ValueError):
        simulate_edit(seq, 5, 8, "XYZ")


def test_breaking_an_ap1_site_changes_tf_binding_delta():
    ctx = BG[:500] + "TGACTCA" + BG[500:1000]
    broken = variant_mechanistic_deltas(ctx, 500, "G")  # TGACTCA -> GGACTCA
    assert broken["delta_tf_binding_by_factor"].get("AP-1", 0) > 0  # binding energy weakens (less negative)
    assert broken["delta_tf_binding_kcal_mol"] > 0
    kept = variant_mechanistic_deltas(ctx, 503, "G")  # TGAGTCA: still an AP-1 site on the reverse strand
    assert "AP-1" not in kept["delta_tf_binding_by_factor"]
    created = variant_mechanistic_deltas(BG[:500] + "TGACTCC" + BG[500:1000], 506, "A")
    assert created["delta_tf_binding_by_factor"].get("AP-1", 0) < 0
    assert local_tf_binding(ctx, 503)["AP-1"]["best_match_fraction"] == 1.0


def test_motif_energy_respects_iupac_codes():
    assert motif_energy("TATAAAA", "TATAWAW")["best_match_fraction"] == 1.0
    assert motif_energy("TATAGAG", "TATAWAW")["best_match_fraction"] < 1.0  # W is A/T, not G


def test_cryptic_splice_risk_separates_consensus_from_random_dna():
    rng = random.Random(3)
    risks = [cryptic_splice_risk("".join(rng.choice("ACGT") for _ in range(200))) for _ in range(30)]
    assert sum(risks) / len(risks) < 0.2
    assert cryptic_splice_risk(BG[:100] + "CAGGTAAGT" + BG[100:200]) > 0.9
    assert cryptic_splice_risk(BG[:100] + "TTTCTCTTCCTTCAGG" + BG[100:200]) > 0.9
    assert splice_sites(BG[:100] + "CAGGTAAGT" + BG[100:200])["donors"][0]["position"] == 103


def test_edit_design_safety_term_now_varies():
    edits = propose_regulatory_edits(BG[:120], 0.1, max_edits=50)["edits"]
    assert len({round(e["cryptic_splice_risk"], 6) for e in edits}) > 1
    assert min(e["cryptic_splice_risk"] for e in edits) < 0.5


def test_tad_boundaries_only_with_convergent_ctcf_structure():
    assert tad_boundaries(BG * 3) == []
    loop = BG[:3500] + CTCF + BG[:2000] + rc(CTCF) + BG[:3000]
    cmap = reconstruct_contact_map(loop)
    assert cmap["ctcf_forward_bins"] == [3] and cmap["ctcf_reverse_bins"] == [5]
    assert tad_boundaries(loop)
    assert tad_boundaries(BG[:3500] + rc(CTCF) + BG[:2000] + CTCF + BG[:3000]) == []  # divergent: no loop
