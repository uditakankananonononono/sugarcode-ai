"""Unit 18 0006 pins (PARTIAL): every text key/value and field count in mappings that the core copies into its output
is bounded in openclinvar/boundary.py. Limits (MAX_TEXT=256, MAX_FIELDS=32, MAX_TOTAL_CHARS=1_000_000) are this wrapper's
own choices, not spec values. Totals are hand-counted. Illustrative evidence arithmetic only, no clinical statement."""
import pytest
from sugarcode.modules.openclinvar import boundary as b

A = "a" * 256


def ok_bayes(extra): return b.bayesian_acmg_checked([{"strength": "strong", "direction": "pathogenic", **extra}])
def ok_cons(extra): return b.evidence_consensus_checked([{"classification": "pathogenic", **extra}])
def ok_cand(extra): return b.reverse_inference_checked(["a"], [{"phenotypes": ["a"], **extra}])
def ok_upd(extra): return b.federated_evidence_checked([{"supporting": 1, "total": 2, **extra}])


SITES = [ok_bayes, ok_cons, ok_cand, ok_upd]


@pytest.mark.parametrize("fn", SITES)
@pytest.mark.parametrize("field", ["name", "label", "note"])
def test_string_field_256_accepted_257_refused(fn, field):
    fn({field: A})
    with pytest.raises(ValueError, match="longer than 256"):
        fn({field: A + "a"})


@pytest.mark.parametrize("fn", SITES)
def test_key_256_accepted_257_refused_and_nontext_key(fn):
    fn({A: 1})
    with pytest.raises(ValueError, match="key longer than 256"):
        fn({A + "a": 1})
    with pytest.raises(TypeError, match="keys must be text"):
        fn({7: 1})


@pytest.mark.parametrize("fn,base", [(ok_bayes, 2), (ok_cons, 1), (ok_cand, 1), (ok_upd, 2)])
def test_field_count_32_accepted_33_refused(fn, base):
    fn({f"k{i}": 1 for i in range(32 - base)})
    with pytest.raises(ValueError, match="more than 32 fields"):
        fn({f"k{i}": 1 for i in range(33 - base)})


@pytest.mark.parametrize("fn", SITES)
@pytest.mark.parametrize("bad", [[1], (1,), {"x": 1}, {1}, object()])
def test_nested_extras_refused(fn, bad):
    with pytest.raises(TypeError, match="must be text, a number, bool or None"):
        fn({"extra": bad})


@pytest.mark.parametrize("fn", SITES)
def test_scalar_extras_accepted_and_nonfinite_or_huge_refused(fn):
    fn({"a": None, "b": True, "c": 3, "d": 1.5, "e": "x", "f": ""})
    for bad in (float("nan"), float("inf"), 1e16, 10**16):
        with pytest.raises(ValueError):
            fn({"x": bad})


def test_candidate_nested_phenotypes_and_ancestor_map_still_allowed():
    r = b.reverse_inference_checked(["a"], [{"phenotypes": ["a"], "ancestor_map": {"a": ["b"]}}])
    assert r[0]["phenotype_match"]["exact_matches"] == 1


def test_candidate_other_nested_refused():
    with pytest.raises(TypeError):
        b.reverse_inference_checked(["a"], [{"phenotypes": ["a"], "meta": {"x": "y"}}])


def _upd(kl, vl):  # chars counted: 'supporting'(10)+'total'(5)=15 plus key plus value
    return {"supporting": 0, "total": 0, "k" * kl: "v" * vl}


def test_total_chars_exactly_1_000_000_accepted_one_more_refused():
    ups = [_upd(256, 256) for _ in range(1897)]          # 1897 * (15+512) = 999_719
    last = _upd(133, 133)                                  # 15 + 266 = 281 -> total 1_000_000
    b.federated_evidence_checked(ups + [last])
    with pytest.raises(ValueError, match="1000000 characters in total"):
        b.federated_evidence_checked(ups + [_upd(133, 134)])


def test_total_chars_budget_is_per_call_and_per_function():
    ups = [_upd(256, 256) for _ in range(1897)]
    b.federated_evidence_checked(ups); b.federated_evidence_checked(ups)


def test_total_chars_applies_to_records_and_candidates():
    recs = [{"classification": "p", "k" * 256: "v" * 256} for _ in range(1900)]   # 1900*(14+1+512)=1_001_300 > 1e6
    with pytest.raises(ValueError, match="1000000 characters in total"):
        b.evidence_consensus_checked(recs)
    def cand():  # 4 fields of 256+256 chars = 2048
        return {str(j).ljust(256, "k"): "v" * 256 for j in range(4)}
    with pytest.raises(ValueError, match="1000000 characters in total"):
        b.reverse_inference_checked(["a"], [cand() for _ in range(489)])      # 489*2048 = 1_001_472
    b.reverse_inference_checked(["a"], [cand() for _ in range(488)])          # 999_424


def test_total_chars_overflow_caused_by_a_nested_key_name_is_refused():
    def cand():
        return {str(j).ljust(256, "k"): "v" * 256 for j in range(4)}
    last = {"x" * 256: "v" * 256, "q" * 58: "", "phenotypes": ["a"]}   # 256+256+58 = 570 of the 576 left, then the 10-char key 'phenotypes' overflows
    with pytest.raises(ValueError, match="1000000 characters in total"):
        b.reverse_inference_checked(["a"], [cand() for _ in range(488)] + [last])
    ok = {"x" * 256: "v" * 256, "q" * 48: "", "phenotypes": ["a"]}      # 256+256+48+10 = 570 <= 576 left: accepted
    b.reverse_inference_checked(["a"], [cand() for _ in range(488)] + [ok])
