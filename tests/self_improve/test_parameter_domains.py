"""SC-P01 authored tests, NOT RUN. Generated-template checks are ordinary cases.

These tests do not imply the existing templates are wired to the helper.
"""
import math

import pytest

from sugarcode.self_improve.parameter_domains import (
    ParameterDomainError, validate_parameters, validate_runtime_items,
)
from sugarcode.self_improve.codegen import synthesize_code
from sugarcode.self_improve.plans import FeaturePlan

KINDS = (
    "keyword_filter", "scoring_rule", "text_transform", "aggregator",
    "threshold_alert", "field_extractor",
)


@pytest.mark.parametrize("kind", KINDS)
def test_defaults_all_six(kind):
    assert type(validate_parameters(kind, {})) is dict


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("bad", [[], (), False, "", 0])
def test_exact_parameter_container(kind, bad):
    with pytest.raises(ParameterDomainError):
        validate_parameters(kind, bad)


@pytest.mark.parametrize("kind", KINDS)
def test_unknown_fields_all_six(kind):
    for params, overrides in [({"extra": 1}, None), ({}, {"extra": 1})]:
        with pytest.raises(ParameterDomainError):
            validate_parameters(kind, params, overrides)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("bad", [False, [], (), "", 0])
def test_falsey_override_is_not_absent(kind, bad):
    with pytest.raises(ParameterDomainError):
        validate_parameters(kind, {}, bad)


@pytest.mark.parametrize("kind,field,bad", [
    ("keyword_filter", "keywords", "a"),
    ("keyword_filter", "keywords", ("a",)),
    ("keyword_filter", "keywords", [""]),
    ("keyword_filter", "keywords", [1]),
    ("keyword_filter", "keywords", ["A", "a"]),
    ("keyword_filter", "mode", "KEEP"),
    ("scoring_rule", "weights", []),
    ("scoring_rule", "weights", {1: 2}),
    ("scoring_rule", "weights", {"": 2}),
    ("scoring_rule", "weights", {"A": 1, "a": 2}),
    ("text_transform", "pattern", "["),
    ("text_transform", "pattern", 4),
    ("text_transform", "replacement", 4),
    ("text_transform", "replacement", r"\2"),
    ("aggregator", "group_by", ""),
    ("aggregator", "value_field", 1),
    ("aggregator", "op", "median"),
    ("threshold_alert", "field", ""),
    ("threshold_alert", "direction", "equal"),
    ("field_extractor", "fields", []),
    ("field_extractor", "fields", {"": "x"}),
    ("field_extractor", "fields", {"x": "["}),
    ("field_extractor", "fields", {1: "x"}),
    ("field_extractor", "fields", {"x": 1}),
])
def test_invalid_domains_at_plan_and_override(kind, field, bad):
    for params, override in [({field: bad}, None), ({}, {field: bad})]:
        with pytest.raises(ParameterDomainError):
            validate_parameters(kind, params, override)


@pytest.mark.parametrize("bad", [True, None, "1", float("nan"), float("inf"),
                                 -float("inf"), 10 ** 400])
@pytest.mark.parametrize("kind,field", [("scoring_rule", "threshold"),
                                       ("threshold_alert", "threshold"),
                                       ("scoring_rule", "weights")])
def test_nonfinite_and_coerced_numbers_refused(kind, field, bad):
    value = {"x": bad} if field == "weights" else bad
    for params, overrides in [({field: value}, None), ({}, {field: value})]:
        with pytest.raises(ParameterDomainError):
            validate_parameters(kind, params, overrides)


def test_weight_subset_overflow_and_negative_weights():
    with pytest.raises(ParameterDomainError):
        validate_parameters("scoring_rule", {"weights": {"a": 1e308, "b": -1e308}})
    assert validate_parameters("scoring_rule", {"weights": {"a": -2}})["weights"] == {"a": -2.0}


def test_overrides_replace_not_merge_and_copy_nested_values():
    base = {"weights": {"a": 1, "b": 2}}
    result = validate_parameters("scoring_rule", base, {"weights": {"c": 3}})
    assert result["weights"] == {"c": 3.0}
    result["weights"]["c"] = 99
    assert base == {"weights": {"a": 1, "b": 2}}
    assert validate_parameters("scoring_rule", base, {"weights": {}})["weights"] == {}
    assert validate_parameters("keyword_filter", {}, {"keywords": []})["keywords"] == []


def test_invalid_base_cannot_be_hidden_by_valid_override():
    with pytest.raises(ParameterDomainError):
        validate_parameters("threshold_alert", {"threshold": math.inf}, {"threshold": 0})


def test_no_custom_conversion_or_mapping_hooks():
    class Trap:
        def __float__(self):
            raise AssertionError("conversion called")
        def __str__(self):
            raise AssertionError("string called")
        def __repr__(self):
            raise AssertionError("repr called")
    class MappingTrap(dict):
        def __iter__(self):
            raise AssertionError("iteration called")
    class StringTrap(str):
        def lower(self):
            raise AssertionError("lower called")
    for value in [Trap(), MappingTrap(), StringTrap("x")]:
        with pytest.raises(ParameterDomainError):
            validate_parameters("threshold_alert", {"threshold": value})
    with pytest.raises(ParameterDomainError):
        validate_parameters("aggregator", MappingTrap())
    with pytest.raises(ParameterDomainError):
        validate_parameters("keyword_filter", {"keywords": [StringTrap("x")]})


@pytest.mark.parametrize("items", [
    [{"category": 1}, {"category": "1"}],
    [{}, {"category": "<missing>"}],
    [{"category": True}, {"category": "True"}],
    [{"category": None}, {"category": "None"}],
    [{"category": []}], [{"category": math.nan}],
    [{1: "x"}],
])
def test_aggregation_group_ambiguity_refused(items):
    with pytest.raises(ParameterDomainError):
        validate_runtime_items("aggregator", items, {})


@pytest.mark.parametrize("op", ["sum", "mean"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True, 10 ** 400])
def test_aggregation_numeric_domain(op, bad):
    with pytest.raises(ParameterDomainError):
        validate_runtime_items("aggregator", [{"value": bad}], {"op": op})


@pytest.mark.parametrize("op", ["sum", "mean"])
def test_aggregation_overflow_is_rejected_before_output(op):
    with pytest.raises(ParameterDomainError):
        validate_runtime_items("aggregator", [{"value": 1e308}, {"value": 1e308}], {"op": op})
    validate_runtime_items("aggregator", [{"value": 1e308}, {"value": -1e308}], {"op": op})


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, "NaN", "1e999", True, 10 ** 400])
def test_threshold_runtime_nonfinite_or_bool_refused(value):
    with pytest.raises(ParameterDomainError):
        validate_runtime_items("threshold_alert", [{"value": value}], {})


def test_runtime_preserves_nonnumeric_skip_and_count_domains():
    validate_runtime_items("threshold_alert", [{}, {"value": None}, {"value": "nope"}, "skip"], {})
    validate_runtime_items("aggregator", [{"value": "nope"}, {}, "skip"], {"op": "mean"})
    validate_runtime_items("aggregator", [{"value": math.inf}], {"op": "count"})


def test_runtime_subclasses_refused_without_hooks():
    class DictTrap(dict):
        def get(self, *args):
            raise AssertionError("get called")
    class FloatTrap(float):
        def __float__(self):
            raise AssertionError("float called")
    for kind in ("aggregator", "threshold_alert"):
        with pytest.raises(ParameterDomainError):
            validate_runtime_items(kind, [DictTrap()], {})
        with pytest.raises(ParameterDomainError):
            validate_runtime_items(kind, [{"value": FloatTrap(1)}], {"op": "sum"} if kind == "aggregator" else {})


@pytest.mark.parametrize("kind,params,items,overrides,expected", [
    ("keyword_filter", {"keywords": ["bio"]}, ["bio grant", "other"], {"mode": "drop"},
     {"items": ["other"], "removed": ["bio grant"], "count": 1}),
    ("scoring_rule", {"weights": {"bio": 2}, "threshold": 1}, ["bio", "other"], {"threshold": 2},
     {"scored": [{"item": "bio", "score": 2.0, "selected": True}, {"item": "other", "score": 0, "selected": False}], "selected": ["bio"], "threshold": 2.0}),
    ("text_transform", {}, ["a  b", 7], None, {"items": ["a b", 7], "changed": 1}),
    ("aggregator", {"op": "sum"}, [{"category": "a", "value": 2}, {"category": "a", "value": 4}], {"op": "mean"},
     {"groups": {"a": 3.0}, "group_by": "category", "op": "mean", "ungrouped": 0}),
    ("threshold_alert", {"threshold": 2}, [{"value": "2"}, {"value": 3}, {}], {"direction": "below"},
     {"flagged": [{"item": {"value": "2"}, "value": 2.0}], "clear": [{"item": {"value": 3}, "value": 3.0}], "skipped": 1, "field": "value", "threshold": 2.0, "direction": "below"}),
    ("field_extractor", {"fields": {"num": r"(\d+)"}}, ["invoice 42", "none", 7], None,
     {"records": [{"text": "invoice 42", "extracted": {"num": "42"}}, {"text": "none", "extracted": {}}], "matched_count": 1}),
])
def test_six_real_template_outputs_ordinary_behavior(kind, params, items, overrides, expected):
    base = validate_parameters(kind, params)
    effective = validate_parameters(kind, base, overrides)
    validate_runtime_items(kind, items, effective)
    plan = FeaturePlan(module_slug="m1", name="domain_case", kind=kind,
                       description="ordinary behavior", gap_signature="domain case", params=base)
    namespace = {}
    exec(compile(synthesize_code(plan), "<authored-template-test>", "exec"), namespace)
    assert namespace["run"](items, effective) == expected


@pytest.mark.parametrize("kind,params", [
    ("keyword_filter", {"keywords": [], "mode": "keep"}),
    ("keyword_filter", {"keywords": ["BIO"], "mode": "drop"}),
    ("scoring_rule", {"weights": {}, "threshold": -2}),
    ("scoring_rule", {"weights": {"a": 0, "b": -1.5}}),
    ("text_transform", {"pattern": "", "replacement": ""}),
    ("text_transform", {"pattern": "(a)", "replacement": r"\1"}),
    ("aggregator", {"op": "count"}),
    ("aggregator", {"op": "sum"}),
    ("aggregator", {"op": "mean"}),
    ("threshold_alert", {"direction": "above", "threshold": 0}),
    ("threshold_alert", {"direction": "below", "threshold": -1}),
    ("field_extractor", {"fields": {"empty": "", "capture": "(a)"}}),
])
def test_supported_domains(kind, params):
    normalized = validate_parameters(kind, params)
    assert validate_parameters(kind, normalized, {}) == normalized


@pytest.mark.parametrize("kind", ["", "unlisted", None, True, []])
def test_unknown_or_nonstring_kind(kind):
    with pytest.raises(ParameterDomainError):
        validate_parameters(kind, {})


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("items", [(), {}, None, "", False])
def test_exact_runtime_list(kind, items):
    with pytest.raises(ParameterDomainError):
        validate_runtime_items(kind, items, {})


def test_ordinary_aggregation_group_labels_and_missing():
    validate_runtime_items("aggregator", [
        {"category": "a", "value": 1}, {"category": "a", "value": 2},
        {"category": 2, "value": -2}, {"value": 3},
        {"category": None, "value": 4}, {"category": False, "value": 0},
    ], {"op": "sum"})


def test_casefold_rule_is_lower_not_unicode_casefold():
    # Mirrors the current matching template exactly, no invented new matching.
    validate_parameters("keyword_filter", {"keywords": ["ss", "ß"]})


def test_runtime_revalidates_effective_parameters():
    with pytest.raises(ParameterDomainError):
        validate_runtime_items("aggregator", [], {"op": "median"})


def test_snapshot_keywords_and_fields_are_detached():
    keywords = ["a"]
    fields = {"a": "x"}
    copied_keywords = validate_parameters("keyword_filter", {"keywords": keywords})
    copied_fields = validate_parameters("field_extractor", {"fields": fields})
    keywords.append("b")
    fields["b"] = "y"
    assert copied_keywords["keywords"] == ["a"]
    assert copied_fields["fields"] == {"a": "x"}
