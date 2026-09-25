import math
import pytest
from sugarcode.modules.epi_edit.core import (design_epigenome_edit, effector_response,
    expression_trajectory, multiplex_design)

SEQ = "ACGT" * 200

def test_bug68_steady_state_includes_feedback():
    r = expression_trajectory("KRAB", .7)
    assert r["steady_state"] == pytest.approx(r["relative_expression"][-1], rel=1e-3)
    r0 = expression_trajectory("KRAB", .7, feedback=0)
    target = effector_response("KRAB", .7)["relative_expression"]
    assert r0["steady_state"] == pytest.approx(target / (math.log(2) / 6), rel=1e-9)

def test_bug69_crispra_never_pulls_downstream_guides():
    d = design_epigenome_edit(SEQ, (30, 80), mode="CRISPRa")
    assert d["guides"] == [] and d["guide_window"] == [0, 0]
    assert d["predicted_effect"]["fold_change"] == 1.0

def test_effector_hill_at_half_occupancy():
    assert effector_response("KRAB", .5)["recruited_fraction"] == pytest.approx(.5)

def test_expression_states_clipped():
    r = effector_response("p300", 1.0, {"accessibility": .9, "acetylation": .9, "methylation": .1})
    assert all(0 <= v <= 1 for v in r["state"].values())

def test_windows_match_documented_rules(tmp_path):
    seq = ("GATTACA" * 120)
    mid = len(seq) // 2
    di = design_epigenome_edit(seq, (mid, mid + 50), mode="CRISPRi")
    da = design_epigenome_edit(seq, (mid, mid + 50), mode="CRISPRa")
    assert di["guide_window"] == [mid - 50, min(len(seq), mid + 300)]
    assert da["guide_window"] == [mid - 400, mid - 50]

def test_multiplex_spacing_and_occupancy():
    guides = [{"composite": .8, "start": 0}, {"composite": .7, "start": 10}, {"composite": .6, "start": 100}]
    m = multiplex_design(guides, min_spacing=50)
    assert m["count"] == 2 and m["combined_occupancy"] == pytest.approx(1 - .2 * .4)
