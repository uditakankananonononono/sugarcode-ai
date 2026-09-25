"""Regression: BUG 47 (segment-based tract clearance) and dead duplicate defs."""
import inspect
from sugarcode.modules import neuroplan_ai
from sugarcode.modules.neuroplan_ai import analyze_tractography


def test_clearance_is_segment_based_not_vertex_only():
    # segment passes through (10,9,0); vertices are all >= 10.3 mm from center
    r = analyze_tractography([[[5, 9, 0], [15, 9, 0], [25, 9, 0]]], [10, 0, 0], 3.0)
    assert abs(r["streamlines"][0]["clearance_mm"] - 6.0) < 1e-6


def test_intersection_detected_between_vertices():
    r = analyze_tractography([[[0, 0, 0], [20, 0, 0]]], [10, 0, 0], 3.0)
    assert r["streamlines"][0]["intersects_tumor"]
    assert r["streamlines"][0]["clearance_mm"] == -3.0


def test_no_duplicate_definitions():
    src = inspect.getsource(neuroplan_ai.core)
    for name in ("_place_regions", "_neurotwin", "enhancement_features", "analyze_neurosurgical_case"):
        assert src.count(f"def {name}") == 1, name
