"""Unit 18 0005: text-length cap (MAX_TEXT = 256) and candidate / total-key caps (MAX_CANDIDATES = 1000,
MAX_TOTAL_KEYS = 10000) for openclinvar/boundary.py (PARTIAL). All limits are this wrapper's choices, not spec values.
Scope: wrappers only; the unchanged core is out of scope. Illustrative evidence arithmetic only."""
import re

import pytest

from sugarcode.modules.openclinvar import boundary as b

OK = "a" * 256
BAD = "a" * 257


def refuses(exc, msg, fn, *a, **k):
    with pytest.raises(exc, match="^" + re.escape(msg) + "$"):
        fn(*a, **k)


def test_constants_are_the_documented_choices():
    assert (b.MAX_TEXT, b.MAX_CANDIDATES, b.MAX_TOTAL_KEYS, b.MAX_ITEMS) == (256, 1000, 10000, 10000)


def test_text_cap_256_accepted_257_refused_at_every_text_site():
    g = b.reasoning_graph_checked
    assert g("g", OK, "c")["nodes"][0]["id"] == OK
    refuses(ValueError, "variant longer than 256 characters", g, "g", BAD, "c")
    assert g(OK, "v", "c")["nodes"][1]["id"] == OK
    refuses(ValueError, "gene longer than 256 characters", g, BAD, "v", "c")
    assert g("g", "v", OK)["nodes"][2]["id"] == OK
    refuses(ValueError, "consequence longer than 256 characters", g, "g", "v", BAD)
    assert g("g", "v", "c", structure_effect=OK)["nodes"][-1]["id"] == OK
    refuses(ValueError, "structure_effect longer than 256 characters", g, "g", "v", "c", structure_effect=BAD)
    assert g("g", "v", "c", phenotypes=[OK])["causal_chain"][-1] == OK
    refuses(ValueError, "phenotypes term longer than 256 characters", g, "g", "v", "c", phenotypes=[BAD])
    refuses(ValueError, "pathways term longer than 256 characters", g, "g", "v", "c", pathways=[BAD])
    assert b.phenotype_match_checked([OK], [OK])["exact_matches"] == 1
    refuses(ValueError, "patient_hpo term longer than 256 characters", b.phenotype_match_checked, [BAD], ["a"])
    refuses(ValueError, "disease_hpo term longer than 256 characters", b.phenotype_match_checked, ["a"], [BAD])
    refuses(ValueError, "patient_hpo term longer than 256 characters", b.reverse_inference_checked, [BAD], [])
    refuses(ValueError, "candidate phenotypes term longer than 256 characters", b.reverse_inference_checked, ["a"], [{"phenotypes": [BAD]}])
    assert b.evidence_consensus_checked([{"classification": OK}])["consensus"] == OK
    refuses(ValueError, "classification longer than 256 characters", b.evidence_consensus_checked, [{"classification": BAD}])


def test_text_cap_for_ancestor_keys_and_terms_and_counts_characters_not_bytes():
    assert b.phenotype_match_checked(["a"], ["b"], {OK: [OK]})["exact_matches"] == 0
    refuses(ValueError, "ancestor_map key longer than 256 characters", b.phenotype_match_checked, ["a"], ["b"], {BAD: ["x"]})
    refuses(ValueError, "ancestor_map term longer than 256 characters", b.phenotype_match_checked, ["a"], ["b"], {"k": [BAD]})
    e = "\u00e9" * 256                                         # 256 characters, 512 bytes in UTF-8
    assert len(e.encode()) == 512 and b.phenotype_match_checked([e], [e])["exact_matches"] == 1
    refuses(ValueError, "patient_hpo term longer than 256 characters", b.phenotype_match_checked, ["\u00e9" * 257], ["a"])


def test_text_checks_type_and_emptiness_before_length():
    refuses(TypeError, "variant must be non-empty text", b.reasoning_graph_checked, "g", "", "c")
    refuses(TypeError, "variant must be non-empty text", b.reasoning_graph_checked, "g", 5, "c")


def test_candidate_cap_1000_accepted_1001_refused_before_any_scan():
    cands = [{"phenotypes": []} for _ in range(1000)]
    assert len(b.reverse_inference_checked(["a"], cands)) == 1000
    refuses(ValueError, "candidates exceeds 1000 items", b.reverse_inference_checked, ["a"], cands + [{"phenotypes": []}])
    refuses(ValueError, "candidates exceeds 1000 items", b.reverse_inference_checked, ["a"], [5] * 1001)   # refused before the element type check


def test_total_ancestor_keys_cap_10000_accepted_10001_refused():
    full = lambda: {"phenotypes": [], "ancestor_map": {f"k{i}": [] for i in range(1000)}}       # 1000 keys, 0 terms
    assert len(b.reverse_inference_checked(["a"], [full() for _ in range(10)])) == 10                 # 10 x 1000 = 10000
    refuses(ValueError, "ancestor_map has more than 10000 keys in total", b.reverse_inference_checked, ["a"],
            [full() for _ in range(10)] + [{"phenotypes": [], "ancestor_map": {"x": []}}])             # 10001
    # an absent or empty map costs nothing
    assert len(b.reverse_inference_checked(["a"], [full() for _ in range(10)] + [{"phenotypes": []}, {"phenotypes": [], "ancestor_map": {}}])) == 12


def test_single_map_key_cap_still_1000_before_total_budget():
    refuses(ValueError, "ancestor_map has more than 1000 keys", b.reverse_inference_checked, ["a"],
            [{"phenotypes": [], "ancestor_map": {f"k{i}": [] for i in range(1001)}}])
    refuses(ValueError, "ancestor_map has more than 1000 keys", b.phenotype_match_checked, ["a"], ["b"], {f"k{i}": [] for i in range(1001)})


def test_phenotype_match_keys_do_not_leak_budget_between_calls():
    m = {f"k{i}": [] for i in range(1000)}
    for _ in range(12):                                          # 12 x 1000 keys across calls: a fresh budget each call
        assert b.phenotype_match_checked(["a"], ["b"], m)["exact_matches"] == 0
