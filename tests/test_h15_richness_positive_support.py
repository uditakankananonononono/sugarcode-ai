"""AUTHORED, NOT RUN. H15: analyze_16s richness counts taxa with a POSITIVE count (support), not len(counts). Base 4d5292004feff70fc896be1bae774158e95eb215.
Written BEFORE the source edit. Valid inputs only: no validation is widened, {} and all-zero tables keep raising ValueError (current behaviour),
and no abundance or diversity (shannon/simpson) logic changes. Frozen hand-computed cases: {'A':10,'B':0}->1, {'A':5,'B':3}->2.
Cross-check: cohort_analysis (its own validation boundary: >= 2 samples, non-empty dicts, integers >= 0, positive total per sample) on mixed
positive valid samples gives the same richness per sample."""
import pytest

from sugarcode.modules.microbiome_exp import analyze_16s, cohort_analysis


def test_zero_count_taxon_is_not_counted():
    assert analyze_16s({"A": 10, "B": 0})["alpha_diversity"]["richness"] == 1


def test_all_positive_taxa_are_counted():
    assert analyze_16s({"A": 5, "B": 3})["alpha_diversity"]["richness"] == 2


def test_richness_is_an_int_and_diversity_values_unchanged_by_zero_taxon():
    with_zero = analyze_16s({"A": 5, "B": 3, "C": 0})["alpha_diversity"]
    without = analyze_16s({"A": 5, "B": 3})["alpha_diversity"]
    assert type(with_zero["richness"]) is int and with_zero == without  # a zero taxon adds nothing to shannon/simpson/richness


def test_empty_and_all_zero_still_raise_value_error():
    with pytest.raises(ValueError, match="empty count table"):
        analyze_16s({})
    with pytest.raises(ValueError, match="empty count table"):
        analyze_16s({"A": 0, "B": 0})


def test_cohort_analysis_richness_agrees_on_mixed_positive_samples():
    table = {"s1": {"A": 10, "B": 0}, "s2": {"A": 5, "B": 3}}
    rows = {r["sample"]: r["richness"] for r in cohort_analysis(table)["alpha_diversity"]}
    assert rows == {"s1": 1, "s2": 2}
    for sample, counts in table.items():
        assert analyze_16s(counts)["alpha_diversity"]["richness"] == rows[sample]


def test_cohort_validation_boundary_is_unchanged_all_zero_sample_raises():
    with pytest.raises(ValueError):
        cohort_analysis({"s1": {"A": 0, "B": 0}, "s2": {"A": 5, "B": 3}})
    with pytest.raises(ValueError, match="two samples"):
        cohort_analysis({"s1": {"A": 5, "B": 3}})
