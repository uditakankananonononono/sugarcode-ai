"""Row 271 trope subversion: independent oracle = hand-worked literals plus brute-force edit distance / LCS."""
import itertools
import pytest
from sugarcode.extra_doc import trope_subversion as t

A = t.analyze_trope_subversion


def brute_edit(a, b):
    # exhaustive recursion over the three edit moves, no memo: an independent algorithm from the module's DP
    if not a:
        return len(b)
    if not b:
        return len(a)
    if a[0] == b[0]:
        return brute_edit(a[1:], b[1:])
    return 1 + min(brute_edit(a[1:], b), brute_edit(a, b[1:]), brute_edit(a[1:], b[1:]))


def brute_lcs(a, b):
    best = 0
    for r in range(len(a) + 1):
        for idx in itertools.combinations(range(len(a)), r):
            sub = [a[i] for i in idx]
            it = iter(b)
            if all(x in it for x in sub):
                best = max(best, r)
    return best


def test_hand_worked_chosen_one_trope():
    exp = ["Prophecy", "Mentor dies", "Training", "Final battle", "Hero wins"]
    story = ["prophecy", "Mentor lives", "Training", "negotiation", "Hero wins", "Epilogue"]
    r = A(exp, story, {"mentor dies": "mentor lives", "final battle": "final peace"})
    assert [b["outcome"] for b in r["beats"]] == ["played", "inverted", "played", "substituted", "played", "added"]
    assert r["counts"] == {"played": 3, "inverted": 1, "substituted": 1, "omitted": 0, "added": 1}
    assert r["adherence_rate"] == 0.6 and r["subversion_rate"] == 0.4 and r["subverted_beats"] == 2
    # lowercase + trim normalisation applied; extra beat at the end costs one edit; 2 substitutions: distance 3
    assert r["edit_distance"] == 3 and r["common_subsequence_length"] == 3
    assert r["verdict"] == "mixed" and r["expected_length"] == 5 and r["story_length"] == 6
    assert r["beats"][5] == {"position": 5, "expected": None, "actual": "epilogue", "outcome": "added"}


def test_played_straight_full_reversal_unrelated():
    assert A(["a", "b"], ["A ", " b"])["verdict"] == "played_straight"
    r = A(["a", "b"], ["x", "y"], {"a": "x", "y": "b"})      # inversion map works in either direction
    assert r["verdict"] == "full_reversal" and r["counts"]["inverted"] == 2 and r["subversion_rate"] == 1.0
    r = A(["a", "b"], ["x"])
    assert r["verdict"] == "unrelated_to_trope" and r["counts"] == {"played": 0, "inverted": 0, "substituted": 1, "omitted": 1, "added": 0}
    # extra beat appended to an otherwise straight telling is not played_straight
    assert A(["a"], ["a", "b"])["verdict"] == "mixed"


def test_omitted_when_story_shorter_and_rates():
    r = A(["a", "b", "c", "d"], ["a", "b"])
    assert [b["outcome"] for b in r["beats"]] == ["played", "played", "omitted", "omitted"]
    assert r["adherence_rate"] == 0.5 and r["subversion_rate"] == 0.5 and r["edit_distance"] == 2
    assert r["beats"][2] == {"position": 2, "expected": "c", "actual": None, "outcome": "omitted"}


def test_rounding_six_places():
    r = A(["a", "b", "c"], ["a", "x", "y"])
    assert r["adherence_rate"] == 0.333333 and r["subversion_rate"] == 0.666667


@pytest.mark.parametrize("exp,act", [
    (["a", "b", "c"], ["c", "b", "a"]), (["a", "b", "c", "d"], ["b", "c", "d", "a"]),
    (["x"], ["y", "x", "z"]), (["a", "a", "b"], ["a", "b", "b", "a"]), (["a", "b"], ["b", "a"]),
    (["p", "q", "r", "s", "t"], ["q", "p", "s", "r"]), (["a", "b"], ["x", "a", "b"]), (["a", "b", "c"], ["a", "x", "b", "c"])])
def test_distance_and_lcs_match_brute_force(exp, act):
    r = A(exp, act)
    assert r["edit_distance"] == brute_edit(exp, act)
    assert r["common_subsequence_length"] == brute_lcs(exp, act)


def test_validation_and_caps():
    ok = ["a"] * 200
    assert A(ok, ok)["expected_length"] == 200
    for bad in ([], ["a"] * 201, "abc", None, 5, [1], [""], ["  "], ["x" * 65], [None]):
        with pytest.raises(ValueError, match="expected_beats"):
            A(bad, ["a"])
        with pytest.raises(ValueError, match="story_beats"):
            A(["a"], bad)
    assert A(["x" * 64], ["x" * 64])["verdict"] == "played_straight"
    with pytest.raises(ValueError, match="list of 1..200"):
        A(["a"] * 201, ["a"])
    inv = {str(i): "o" for i in range(200)}
    A(["a"], ["a"], inv)
    with pytest.raises(ValueError, match="at most 200"):
        A(["a"], ["a"], {**inv, "extra": "o"})
    with pytest.raises(ValueError, match="inversions"):
        A(["a"], ["a"], ["a"])
    with pytest.raises(ValueError, match="inversions key"):
        A(["a"], ["a"], {1: "x"})
    with pytest.raises(ValueError, match="inversions value"):
        A(["a"], ["a"], {"x": None})
    with pytest.raises(ValueError, match="conflicting opposites"):
        A(["a"], ["a"], {"X": "p", " x": "q"})
    A(["a"], ["a"], {"X": "p", " x": "P"})        # same opposite after normalisation is fine
    A(["a"], ["a"], None)
    A(("a", "b"), ("a", "b"))                      # tuples accepted


def test_status_note_is_partial():
    assert A(["a"], ["a"])["status_note"].startswith("PARTIAL:")
    assert "no story generation" in A(["a"], ["a"])["status_note"]
