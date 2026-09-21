"""Hermetic golden regression: learned splice PWM vs ClinVar BRCA1 set.

Fixture: tests/fixtures/brca1_splice_golden.json - 186 pathogenic and 20
benign NM_007294 splice SNVs pulled live from ClinVar on 2026-09-21, mapped
onto RefSeqGene NG_005905.2 junction windows. Thresholds in deepsplice were
calibrated on this set; these tests lock the calibration in place.
"""
import json
import re
from pathlib import Path

from sugarcode.modules.deepsplice import (score_donor, score_acceptor,
                                          variant_effect, variant_at, PWM_SOURCE)

FIX = json.loads(Path("tests/fixtures/brca1_splice_golden.json").read_text())
PATH, BEN = FIX["pathogenic"], FIX["benign"]


def _k(case):
    return int(re.search(r"[+-](\d+)", case["notation"]).group(1))


def test_pwm_source_is_real_data():
    assert "RefSeqGene" in PWM_SOURCE


def test_real_consensus_scores_high():
    # learned consensus from 1,215 real GT-AG junctions
    assert score_donor("AAGGTAAGT") > 0.9
    assert score_acceptor("TTTTTTTTTTTCAGG") > 0.9


def test_fixture_covers_gene():
    assert len(PATH) == 186 and len(BEN) == 20


def test_all_canonical_site_variants_called_loss():
    """Every ClinVar pathogenic +/-1 / +/-2 variant must hit the loss band."""
    canonical = [c for c in PATH if _k(c) <= 2]
    assert len(canonical) == 150
    misses = [c["notation"] for c in canonical if c["delta"] > -0.15]
    assert misses == [], f"canonical-site misses: {misses}"


def test_overall_sensitivity_and_specificity():
    tp = sum(1 for c in PATH if c["delta"] <= -0.15)
    tn = sum(1 for c in BEN if c["delta"] > -0.15)
    assert tp / len(PATH) >= 0.80, f"sensitivity dropped: {tp}/{len(PATH)}"
    assert tn / len(BEN) >= 0.85, f"specificity dropped: {tn}/{len(BEN)}"


def test_named_golden_cases():
    by_notation = {c["notation"]: c for c in PATH + BEN}
    # expert-panel-reviewed pathogenic canonical sites
    assert by_notation["c.212+1G>A"]["consequence"].startswith("likely loss")
    assert by_notation["c.135-1G>T"]["consequence"].startswith("likely loss")
    # expert-panel-reviewed benign deep-window variant: minimal effect
    assert by_notation["c.5074+6C>G"]["consequence"] == "minimal predicted effect on splicing"
    assert by_notation["c.4097-10G>A"]["delta"] > -0.05


def test_known_false_positive_documented():
    """c.594-2A>C is ClinVar-benign (ENIGMA expert panel) but our PWM calls
    it a strong loss (-0.180): the position is highly conserved, yet the
    variant is tolerated. Kept visible so the limit is never silently
    'fixed' by tuning it away."""
    c = next(c for c in BEN if c["notation"] == "c.594-2A>C")
    assert c["delta"] <= -0.15
    assert c["sig"] == "benign"


def test_variant_at_index_semantics():
    # donor window index 3 is +1, acceptor index 13 is -1
    r = variant_at("AAGGTAAGT", 3, "A", "donor")
    assert r["delta"] <= -0.15 and r["ref_base"] == "G"
    r = variant_at("TTTTTTTTTTTCAGG", 13, "A", "acceptor")
    assert r["delta"] <= -0.15 and r["ref_base"] == "G"


def test_fixture_cases_reproduce_live_scoring():
    """Recompute every fixture case from its stored window and check the
    recorded scores match the current model exactly."""
    for c in PATH + BEN:
        r = variant_at(c["window"], c["index"],
                       _alt_of(c["window"][c["index"]], c), c["site_type"])
        assert r["delta"] == c["delta"], c["notation"]


def _alt_of(ref_base, case):
    import re as _re
    m = _re.search(r"([ACGT])>([ACGT])$", case["notation"])
    assert m.group(1) == ref_base
    return m.group(2)
