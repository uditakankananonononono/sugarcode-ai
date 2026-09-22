"""Drop 56: branch-point assessment surfaced in live_splice_assessment for
acceptor-side deep variants in the -45..-18 zone (cryptic verdict unchanged)."""
import json
from pathlib import Path

from sugarcode.modules.deepsplice import live_splice_assessment, BP_WEIGHT

Z = json.loads(Path("tests/fixtures/branchzone_clinvar_golden.json").read_text())


def test_live_path_matches_golden():
    r = live_splice_assessment("RB1", "c.2490-28T>G")
    assert r["status"] == "cryptic_scan"
    bp = r["branchpoint"]
    assert bp["bp_applicable"] is True
    assert bp["bp_drop_bits"] == 3.1747          # fixture value, exact
    assert bp["delta"] == round(-BP_WEIGHT * 3.1747, 4)
    assert "disruption" in bp["consequence"]


def test_benign_bp_zone_variant_gets_block_too():
    r = live_splice_assessment("TSC2", "c.5062-19C>T") \
        if any(c["notation"] == "c.5062-19C>T" for c in Z["genes"]["TSC2"]["cases"]) else None
    if r is None:  # pick any benign BP-zone case from the fixture
        gene, c = next((g, c) for g, gg in Z["genes"].items() for c in gg["cases"]
                       if c["in_bp_zone"] and c["sig"] == "benign")
        r = live_splice_assessment(gene, c["notation"])
        assert r["branchpoint"]["bp_drop_bits"] == c["bp_pwm_drop"]
    else:
        assert r["branchpoint"]["bp_applicable"] is True


def test_outside_zone_no_bp_block():
    # -50 is outside -45..-18: cryptic scan only, no branchpoint block
    gene, c = next((g, c) for g, gg in Z["genes"].items() for c in gg["cases"]
                   if c["dist"] == 50)
    r = live_splice_assessment(gene, c["notation"])
    assert r["status"] == "cryptic_scan"
    assert "branchpoint" not in r
