"""Exact-endpoint pins for experiment_log_checked limits (PARTIAL): integer magnitude 1e15, nesting depth 64
for lists AND dicts, node count 100000. Limits are this module's own choices (_PRE, MAX_DEPTH, MAX_NODES), not spec values."""
import pytest

from sugarcode.modules.biofactory_1_a import core
from sugarcode.modules.biofactory_1_a import boundary_ops as b

PROTO = core.generate_protocol("gibson", 2)
PRE = 10**15


def nest_list(depth, leaf=0):
    x = leaf
    for _ in range(depth):
        x = [x]
    return x


def nest_dict(depth, leaf=0):
    x = leaf
    for _ in range(depth):
        x = {"k": x}
    return x


def test_integer_magnitude_endpoint_accepted_and_one_past_refused():
    for v in (PRE, -PRE, PRE - 1):
        r = b.experiment_log_checked(PROTO, {"x": v})
        assert r["results"]["x"] == v and str(v) in r["machine_readable"]
    for v in (PRE + 1, -PRE - 1):
        with pytest.raises(ValueError, match="results integer magnitude too large"):
            b.experiment_log_checked(PROTO, {"x": v})


@pytest.mark.parametrize("make", [nest_list, nest_dict])
def test_depth_64_accepted_depth_65_refused_for_lists_and_dicts(make):
    # root is depth 0, so the leaf of make(d) sits at depth d
    assert b.experiment_log_checked(PROTO, make(64))["results"] == make(64)
    with pytest.raises(ValueError, match="results nested deeper than 64"):
        b.experiment_log_checked(PROTO, make(65))


def test_depth_counts_mixed_list_and_dict_levels_the_same():
    mixed = {"k": [{"k": [0] * 1}] * 1}                       # depth: dict0 -> list1 -> dict2 -> list3 -> leaf 4
    x = 0
    for i in range(64):
        x = [x] if i % 2 else {"k": x}
    assert b.experiment_log_checked(PROTO, x)["results"] == x
    assert b.experiment_log_checked(PROTO, mixed)["results"] == mixed
    y = {"k": x}
    with pytest.raises(ValueError, match="results nested deeper than 64"):
        b.experiment_log_checked(PROTO, y)


def test_node_count_100000_accepted_100001_refused():
    assert len(b.experiment_log_checked(PROTO, [0] * 99_999)["results"]) == 99_999   # root + 99999 = 100000 nodes
    with pytest.raises(ValueError, match="results has more than 100000 values"):
        b.experiment_log_checked(PROTO, [0] * 100_000)


# ---------- v3: container types that must pass through ----------
def test_tuple_inside_results_at_depth_1_passes_through_unchanged():
    t = (1, 2.5, "x", None, True)
    r = b.experiment_log_checked(PROTO, {"k": t})
    assert r["results"]["k"] is t                                   # same object, not converted
    assert r["machine_readable"] == '{"results": {"k": [1, 2.5, "x", null, true]}, "workflow": "%s"}' % PROTO["workflow"]
    r = b.experiment_log_checked(PROTO, (1, (2, 3)))                # tuple at the root and nested
    assert r["results"] == (1, (2, 3)) and '"results": [1, [2, 3]]' in r["machine_readable"]


def test_tuple_children_count_toward_depth_and_nodes_and_are_checked():
    x = 0
    for _ in range(64):
        x = (x,)
    assert b.experiment_log_checked(PROTO, x)["results"] == x       # depth 64 through tuples
    with pytest.raises(ValueError, match="results nested deeper than 64"):
        b.experiment_log_checked(PROTO, (x,))
    with pytest.raises(ValueError, match="results must be finite"):
        b.experiment_log_checked(PROTO, {"k": (1, float("nan"))})
    with pytest.raises(TypeError, match="results keys must be text"):
        b.experiment_log_checked(PROTO, ({1: 2},))


def test_non_dict_mapping_protocol_passes_through():
    from types import MappingProxyType
    p = MappingProxyType({"workflow": "x"})
    r = b.experiment_log_checked(p, {"a": 1})
    assert r["protocol"] is p
    assert r["machine_readable"] == '{"results": {"a": 1}, "workflow": "x"}'
    assert r["provenance"] == {"generator": "BioFactory 1-A", "version": "explicit-model-v1"}
    for bad in ({"workflow": 3}, {}, [("workflow", "x")], "workflow", None):
        with pytest.raises(TypeError, match="protocol must be a mapping with a text workflow"):
            b.experiment_log_checked(bad, {})
