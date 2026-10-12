"""Candidates inside the declared PBS/RTT ranges are kept; the primary nick follows primary_position."""
import pytest

from sugarcode.modules.prime_design.core import (
    architecture_variants, compile_prime_edit, design_pegrna)

SPACER = "GACGCATAAAGATGAGACGC"
EDIT12 = "ACGTACGTACGT"


def test_pbs16_rtt12_is_kept_by_architecture_variants():
    peg = design_pegrna(SPACER, EDIT12, 16, 12)  # accepted directly
    pairs = {(v["pbs_length"], v["rtt_length"]) for v in architecture_variants(SPACER, EDIT12)}
    assert (16, 12) in pairs
    assert peg["pbs_length"] == 16 and peg["rtt_length"] == 12


def test_rtt_longer_than_edit_is_still_skipped_and_outside_ranges_rejected():
    pairs = {(v["pbs_length"], v["rtt_length"]) for v in architecture_variants(SPACER, EDIT12)}
    assert all(r <= len(EDIT12) for _, r in pairs)
    assert (10, 13) not in pairs
    with pytest.raises(ValueError):
        design_pegrna(SPACER, EDIT12, 17, 12)
    with pytest.raises(ValueError):
        design_pegrna(SPACER, EDIT12, 16, 9)


def test_primary_nick_comes_from_primary_position():
    cands = [{"position": 170, "strand": "-"}, {"position": 40, "strand": "-"}]
    default = compile_prime_edit(SPACER, EDIT12, nicking_candidates=cands)
    moved = compile_prime_edit(SPACER, EDIT12, nicking_candidates=cands, primary_position=100)
    assert {n["position"]: n["distance"] for n in default["nicking_strategies"]} == {170: 170, 40: 40}
    assert {n["position"]: n["distance"] for n in moved["nicking_strategies"]} == {170: 70, 40: 60}


def test_primary_position_is_keyword_only_and_default_equals_zero():
    import pytest
    cands = [{"position": 170, "strand": "-"}, {"position": 40, "strand": "+"}]
    assert compile_prime_edit(SPACER, EDIT12, nicking_candidates=cands) == compile_prime_edit(
        SPACER, EDIT12, nicking_candidates=cands, primary_position=0)
    with pytest.raises(TypeError):
        compile_prime_edit(SPACER, EDIT12, None, cands, 100)
