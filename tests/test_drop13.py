"""Drop 13: A* neuro pathfinding, TASEP dwell times, cfDNA fragment entropy."""
import pytest


class TestAStarNeuro:
    def test_path_reaches_target_and_starts_at_entry(self):
        from sugarcode.modules.neuroplan_ai.core import plan_path_astar
        r = plan_path_astar({"center": [32, 32, 20], "radius_mm": 15}, entry=[32, 32, 63])
        assert r["path"][0] == [32, 32, 63]
        assert r["path"][-1] == [32, 32, 20]
        # contiguity: every consecutive pair is one grid step
        for a, b in zip(r["path"], r["path"][1:]):
            assert max(abs(a[k] - b[k]) for k in range(3)) == 1

    def test_detour_beats_straight_line_when_obstructed(self):
        from sugarcode.modules.neuroplan_ai.core import plan_path_astar
        r = plan_path_astar({"center": [32, 32, 20], "radius_mm": 15}, entry=[5, 5, 63])
        assert r["path_risk_integral"] < r["straight_line_risk_integral"]
        assert r["risk_reduction_vs_straight"] > 0

    def test_clear_line_tracked(self):
        from sugarcode.modules.neuroplan_ai.core import plan_path_astar
        r = plan_path_astar({"center": [32, 32, 20], "radius_mm": 15}, entry=[32, 32, 63])
        assert abs(r["risk_reduction_vs_straight"]) < 0.1 and r["note"]

    def test_deterministic(self):
        from sugarcode.modules.neuroplan_ai.core import plan_path_astar
        a = plan_path_astar({"center": [32, 32, 20]}, entry=[5, 5, 63])
        b = plan_path_astar({"center": [32, 32, 20]}, entry=[5, 5, 63])
        assert a["path"] == b["path"]


class TestTasepDwell:
    def test_dwell_times_exposed_and_ordered(self):
        from sugarcode.modules.codon_opt import core
        from sugarcode.bio import codon
        r = core.tasep_simulate("ATG" + "CTG" * 5 + "TTA" * 5 + "CTG" * 5, steps=400)
        assert len(r["dwell_times_s"]) == r["codons"]
        # TTA is rare in E. coli: its dwell must exceed common CTG's
        assert r["dwell_times_s"][6] > r["dwell_times_s"][2]
        assert "Missing" in r["dwell_provenance"]  # Ribo-seq calibration honestly absent

    def test_dwell_inverse_of_usage(self):
        from sugarcode.modules.codon_opt import core
        from sugarcode.bio import codon
        w = codon.relative_adaptiveness(codon.ECOLI_PUBLISHED)
        r = core.tasep_simulate("ATG" + "CTG" * 4, steps=200)
        # dwell = 1/(10 * max(w, 0.05))
        assert r["dwell_times_s"][1] == pytest.approx(1.0 / (10 * max(w["CTG"], 0.05)), abs=1e-3)


class TestFragmentEntropy:
    def test_healthy_anchor_peak(self):
        from sugarcode.modules.liquid_biopsy import fragment_length_model
        r = fragment_length_model(0.0, n_fragments=8000)
        assert 160 <= r["modal_length_bp"] <= 175  # published healthy peak ~166 bp

    def test_monotone_with_tumor_fraction(self):
        from sugarcode.modules.liquid_biopsy import fragment_length_model
        r0 = fragment_length_model(0.0, n_fragments=8000)
        r2 = fragment_length_model(0.2, n_fragments=8000)
        assert r2["shannon_entropy_bits"] > r0["shannon_entropy_bits"]
        assert r2["short_fraction_100_150bp"] > r0["short_fraction_100_150bp"]
        assert r2["kl_divergence_to_healthy_ref"] > r0["kl_divergence_to_healthy_ref"]

    def test_anchors_labeled(self):
        from sugarcode.modules.liquid_biopsy import fragment_length_model
        r = fragment_length_model(0.1, n_fragments=2000)
        assert "not fitted patient data" in r["anchors"]["status"]

    def test_bounds_checked(self):
        from sugarcode.modules.liquid_biopsy import fragment_length_model
        with pytest.raises(ValueError):
            fragment_length_model(1.5)
