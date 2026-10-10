"""PREP-NORUN. Reference calculations live only in this test file.

Provenance: base 6e1a42145e529d50751ec3b5cedc6d6ff3105f60;
json_values.py:19-51, gate.py:77-142, capped_readers.py:12.
Auditor executes in isolated synthetic temp directories, never live state.
"""
import hashlib
import json
import math
import inspect
import os
from types import SimpleNamespace

import pytest

from sugarcode.self_improve import gate as gate_module
from sugarcode.self_improve.approval_schema import ApprovalSchemaError, validate_record
from sugarcode.self_improve.capped_readers import InputLimitExceeded
from sugarcode.self_improve.gate import InvalidApprovalState, ManualApprovalGate
from sugarcode.self_improve.json_values import InvalidTelemetryValue, snapshot_json

BASE = "6e1a42145e529d50751ec3b5cedc6d6ff3105f60"
LIMIT = 4 * 1024 * 1024
STAMP = 1000.0  # exact synthetic point bound, not a production average
HEX = "000000000001" + "0" * 20  # exact 32-character UUID hex seam


class Refusal(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def measure(value):
    """Independent iterative expansion oracle; keys never consume visits.

    Returns normalized tree, count, deepest root-0 visit. Count every alias
    expansion but reject active-path cycles. No global identity deduplication.
    """
    count = 0
    deepest = 0
    active = set()
    root = [None]
    work = [("visit", value, 0, root, 0)]
    while work:
        kind, item, depth, parent, slot = work.pop()
        if kind == "leave":
            active.remove(item)
            continue
        count += 1
        deepest = max(deepest, depth)
        if count > 10000:
            raise Refusal("expanded_values")
        if depth > 64:
            raise Refusal("depth")
        typ = type(item)
        if item is None or typ in (str, bool, int):
            parent[slot] = item
        elif typ is float:
            if not math.isfinite(item):
                raise Refusal("nonfinite")
            parent[slot] = item
        elif typ in (dict, list, tuple):
            identity = id(item)
            if identity in active:
                raise Refusal("cycle")
            active.add(identity)
            if typ is dict:
                if any(type(key) is not str for key in item):
                    raise Refusal("key_type")
                result = {}
                children = list(item.items())
            else:
                result = [None] * len(item)
                children = list(enumerate(item))
            parent[slot] = result
            work.append(("leave", identity, 0, None, None))
            work.extend(("visit", child, depth + 1, result, key)
                        for key, child in reversed(children))
        else:
            raise Refusal("custom_input")
    return root[0], count, deepest


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode("utf-8")


def strict_source(raw):
    if type(raw) is not bytes:
        raise Refusal("source_type")
    if len(raw) > LIMIT:
        raise Refusal("raw_file_bytes")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Refusal("duplicate_key")
            result[key] = value
        return result

    def constant(_):
        raise Refusal("nonfinite")

    def finite(text):
        value = float(text)
        if not math.isfinite(value):
            raise Refusal("nonfinite")
        return value

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                       parse_constant=constant, parse_float=finite)
    if type(value) is not dict:
        raise Refusal("root_not_object")
    return value


def request_record(*, auto=False, summary="x", payload=None):
    return {"module_id": 1, "module_slug": "synthetic", "action_type": "generic",
            "summary": summary, "payload": {} if payload is None else payload,
            "status": "approved" if auto else "pending", "requested_at": STAMP,
            "decided_at": None}


def prospective(state, operation, *, auto=False):
    # Copy-on-write only the outer map and selected record. Old record replaced,
    # not retained as an extra alias. Other aliases count per tree expansion.
    new = dict(state)
    if operation["kind"] == "request":
        new[operation["id"]] = operation["record"]
        validate_record(new[operation["id"]], allow_unrecorded_decision=auto)
    elif operation["kind"] == "decision":
        if operation["status"] not in ("approved", "rejected"):
            raise Refusal("decision_argument")
        old = state[operation["id"]]
        if type(old) is not dict or type(old.get("status")) is not str or old["status"] not in (
                "pending", "approved", "rejected"):
            raise Refusal("status_record")
        record = dict(old)
        record.update(status=operation["status"], decided_at=operation["timestamp"],
                      decided_by=operation["actor"])
        if "action_type" in record:
            validate_record(record, allow_unrecorded_decision=auto)
        new[operation["id"]] = record
    else:
        raise Refusal("operation")
    return new


def forecast(raw, operation, *, auto=False):
    """Synthetic report schema, not installed API or independent schema validator."""
    result = {"base": BASE, "source_sha256": hashlib.sha256(raw).hexdigest(),
              "live_usage": "UNKNOWN", "archive_eligibility": 0,
              "uncertainty": ["synthetic exact shapes only", "no I/O durability forecast"]}
    result["raw_bytes"] = len(raw)
    result["raw_headroom"] = LIMIT - len(raw)
    try:
        state = strict_source(raw)
    except (Refusal, ValueError, TypeError, RecursionError) as exc:
        reason = getattr(exc, "reason", type(exc).__name__)
        result["baseline"] = {"unavailable_reason": reason}
        result["prospective"] = {"admitted": False, "reason": reason,
                                 "stage": "source", "provenance": "gate.py:77-88"}
        return result
    try:
        normalized, count, depth = measure(state)
        encoded = canonical(normalized)
        result["baseline"] = {"expanded_values": count, "depth": depth,
                              "encoded_bytes": len(encoded), "value_headroom": 10000-count,
                              "depth_headroom": 64-depth,
                              "encoded_headroom": LIMIT-len(encoded)}
    except (Refusal, ValueError, TypeError, RecursionError) as exc:
        result["baseline"] = {"unavailable_reason": getattr(exc, "reason", type(exc).__name__)}
    try:
        next_state = prospective(state, operation, auto=auto)
        normalized, count, depth = measure(next_state)
        encoded = canonical(normalized)
        if len(encoded) > LIMIT:
            raise Refusal("encoded_file_bytes")
        result["prospective"] = {"admitted": True, "expanded_values": count, "depth": depth,
                                 "encoded_bytes": len(encoded), "value_headroom": 10000-count,
                                 "depth_headroom": 64-depth,
                                 "encoded_headroom": LIMIT-len(encoded)}
    except (Refusal, ApprovalSchemaError, ValueError, TypeError, KeyError, RecursionError) as exc:
        result["prospective"] = {"admitted": False,
                                 "reason": getattr(exc, "reason", getattr(exc, "code", type(exc).__name__))}
    return result


def gate_at(tmp_path, raw=b"{}", auto=False):
    path = tmp_path / "synthetic-approvals.json"
    path.write_bytes(raw)
    return ManualApprovalGate(path, auto_approve=auto), path


def seams(monkeypatch):
    monkeypatch.setattr(gate_module, "uuid4", lambda: SimpleNamespace(hex=HEX))
    monkeypatch.setattr(gate_module.time, "time", lambda: STAMP)


@pytest.mark.parametrize("n,accepted", [(9999, True), (10000, False)])
def test_exact_expanded_10000_10001(n, accepted):
    state = {str(i): 0 for i in range(n)}  # root + scalar children, keys excluded
    if accepted:
        assert measure(state)[1:] == (10000, 1)
        assert snapshot_json(state) == state
    else:
        with pytest.raises(Refusal, match="expanded_values"):
            measure(state)
        with pytest.raises(InvalidTelemetryValue):
            snapshot_json(state)


@pytest.mark.parametrize("depth,accepted", [(64, True), (65, False)])
def test_root_zero_depth_boundary(depth, accepted):
    item = 0
    for _ in range(depth):
        item = [item]
    if accepted:
        assert measure(item)[1:] == (65, 64)
        assert snapshot_json(item) == item
    else:
        with pytest.raises(Refusal, match="depth"):
            measure(item)
        with pytest.raises(InvalidTelemetryValue):
            snapshot_json(item)


def test_keys_aliases_tuples_and_copy_on_write():
    shared = (1, 2)
    state = {"a": shared, "b": shared}
    assert measure(state) == ({"a": [1, 2], "b": [1, 2]}, 7, 2)
    assert snapshot_json(state) == measure(state)[0]
    baseline = {"id": {"status": "pending"}}
    updated = prospective(baseline, {"kind": "decision", "id": "id", "status": "approved",
                                    "timestamp": STAMP, "actor": None})
    assert measure(baseline)[1] == 3
    assert measure(updated)[1] == 5  # new timestamp/actor, old record not counted
    assert baseline == {"id": {"status": "pending"}}


@pytest.mark.parametrize("extra,accepted", [(0, True), (1, False)])
def test_exact_raw_4mib_plus_one(tmp_path, extra, accepted):
    raw = b"{}" + b" " * (LIMIT - 2 + extra)
    gate, path = gate_at(tmp_path, raw)
    if accepted:
        assert strict_source(raw) == gate._load() == {}
    else:
        with pytest.raises(Refusal, match="raw_file_bytes"):
            strict_source(raw)
        with pytest.raises(InvalidApprovalState) as error:
            gate._load()
        assert isinstance(error.value.__cause__, InputLimitExceeded)
    assert path.read_bytes() == raw


@pytest.mark.parametrize("extra,accepted", [(0, True), (1, False)])
def test_exact_encoded_4mib_plus_one(tmp_path, extra, accepted):
    overhead = len(canonical({"x": ""}))
    state = {"x": "a" * (LIMIT - overhead + extra)}
    assert len(canonical(state)) == LIMIT + extra
    gate, path = gate_at(tmp_path)
    if accepted:
        gate._save(state)
        assert len(path.read_bytes()) == LIMIT
    else:
        with pytest.raises(InputLimitExceeded):
            gate._save(state)
        assert path.read_bytes() == b"{}"


@pytest.mark.parametrize("text,literal", [("é", b'"\\u00e9"'),
                                          ("🙂", b'"\\ud83d\\ude42"'),
                                          ("\ud800", b'"\\ud800"')])
def test_ascii_escape_multibyte_surrogate_semantics(tmp_path, text, literal):
    assert json.dumps(text, ensure_ascii=True).encode("utf-8") == literal
    gate, path = gate_at(tmp_path)
    state = {"z": text, "a": 0}
    gate._save(state)
    assert path.read_bytes() == canonical(state)
    assert path.read_bytes().startswith(b'{\n  "a": 0,\n  "z": ')
    assert gate._load() == state


@pytest.mark.parametrize("raw", [b'{"x":0,"x":1}', b'{"x":{"a":0,"a":1}}',
                                 b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}'])
def test_duplicate_nonfinite_read_error_provenance(tmp_path, raw):
    gate, path = gate_at(tmp_path, raw)
    with pytest.raises(InvalidApprovalState) as error:
        gate._load()
    assert isinstance(error.value.__cause__, InvalidApprovalState)
    with pytest.raises(Refusal):
        strict_source(raw)
    assert path.read_bytes() == raw


@pytest.mark.parametrize("kind", ["cycle", "custom", "nonfinite", "key"])
def test_write_domain_refusals_preserve_bytes(tmp_path, kind):
    class Custom:
        def __str__(self):
            raise AssertionError("conversion must not run")
    state = {"x": []}
    if kind == "cycle":
        state["x"].append(state)
    elif kind == "custom":
        state["x"] = Custom()
    elif kind == "nonfinite":
        state["x"] = float("nan")
    else:
        state = {1: "x"}
    gate, path = gate_at(tmp_path)
    with pytest.raises(Refusal):
        measure(state)
    with pytest.raises(InvalidApprovalState) as error:
        gate._save(state)
    assert isinstance(error.value.__cause__, InvalidTelemetryValue)
    assert path.read_bytes() == b"{}"


def test_read_succeeds_while_every_decision_write_is_j04_blocked(tmp_path):
    state = {"id": {"status": "pending"}, "filler": [0] * 10000}
    raw = json.dumps(state, separators=(",", ":")).encode()
    gate, path = gate_at(tmp_path, raw)
    assert gate._load() == state
    for status in ("approved", "rejected"):
        op = {"kind": "decision", "id": "id", "status": status, "timestamp": STAMP, "actor": None}
        assert forecast(raw, op)["prospective"] == {"admitted": False, "reason": "expanded_values"}
        with pytest.raises(InvalidApprovalState) as error:
            gate.decide("id", status, decided_by=None)
        assert isinstance(error.value.__cause__, InvalidTelemetryValue)
        assert path.read_bytes() == raw


@pytest.mark.parametrize("auto", [False, True])
def test_request_envelope_matches_real_gate(tmp_path, monkeypatch, auto):
    seams(monkeypatch)
    raw = b"{}"
    record = request_record(auto=auto)
    op = {"kind": "request", "id": "si-" + HEX[:12], "record": record}
    report = forecast(raw, op, auto=auto)
    gate, path = gate_at(tmp_path, raw, auto=auto)
    approval = gate.request(module_id=1, module_slug="synthetic", action_type="generic",
                            summary="x", payload={})
    assert approval == op["id"]
    assert gate._load() == {approval: record}
    assert len(path.read_bytes()) == report["prospective"]["encoded_bytes"]
    assert report["prospective"]["expanded_values"] == 10
    assert report["source_sha256"] == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("initial", ["pending", "approved", "rejected"])
@pytest.mark.parametrize("target", ["approved", "rejected"])
@pytest.mark.parametrize("actor", [None, "human"])
def test_full_and_legacy_decisions_match_real_gate(tmp_path, monkeypatch, initial, target, actor):
    seams(monkeypatch)
    for full in (False, True):
        directory = tmp_path / ("full" if full else "legacy")
        directory.mkdir()
        record = request_record() if full else {"status": initial}
        record["status"] = initial
        if full and initial != "pending":
            record.update(decided_at=STAMP, decided_by="human")
        raw = canonical({"id": record})
        op = {"kind": "decision", "id": "id", "status": target, "timestamp": STAMP, "actor": actor}
        report = forecast(raw, op)
        gate, path = gate_at(directory, raw)
        gate.decide("id", target, decided_by=actor)
        assert report["prospective"]["admitted"] is True
        assert len(path.read_bytes()) == report["prospective"]["encoded_bytes"]
        assert gate.decision("id") == target
        assert gate._load()["id"]["decided_by"] == actor


@pytest.mark.parametrize("actor", ["", 0, [], {}])
def test_full_schema_refusal_vs_legacy_generic_decision(tmp_path, monkeypatch, actor):
    seams(monkeypatch)
    for full in (False, True):
        directory = tmp_path / str(full)
        directory.mkdir()
        raw = canonical({"id": request_record() if full else {"status": "pending"}})
        op = {"kind": "decision", "id": "id", "status": "approved", "timestamp": STAMP, "actor": actor}
        report = forecast(raw, op)
        gate, path = gate_at(directory, raw)
        if full:
            assert report["prospective"] == {"admitted": False, "reason": "decided_by_type"}
            with pytest.raises(InvalidApprovalState) as error:
                gate.decide("id", "approved", decided_by=actor)
            assert isinstance(error.value.__cause__, ApprovalSchemaError)
            assert path.read_bytes() == raw
        else:
            assert report["prospective"]["admitted"] is True
            gate.decide("id", "approved", decided_by=actor)
            assert len(path.read_bytes()) == report["prospective"]["encoded_bytes"]


def test_unknown_action_payload_is_not_request_binding_validation(tmp_path, monkeypatch):
    seams(monkeypatch)
    gate, _ = gate_at(tmp_path)
    approval = gate.request(module_id=-1, module_slug="x", action_type="unrecognized",
                            summary="", payload={"anything": (1, 2)})
    assert gate._load()[approval]["payload"] == {"anything": [1, 2]}
    # gate.request calls validate_record, not validate_payload/check_binding.


def test_repeat_shape_count_is_exact_not_generic_guarantee(tmp_path):
    # Exact empty-payload envelope: 9 visits per record, root consumes 1.
    # IDs have a fixed unique 12-lowercase-hex suffix; timestamps exactly 1000.0.
    # No actor until decision; not a random UUID/timestamp average.
    state = {f"si-{i:012x}": request_record() for i in range(1111)}
    assert measure(state)[1] == 10000
    # Indented entry contributes 223 bytes plus comma/newline overhead;
    # root/newline accounting gives 225*n + 2 for this exact nonempty shape.
    assert len(canonical(state)) == 225 * 1111 + 2
    gate, path = gate_at(tmp_path)
    gate._save(state)
    assert path.read_bytes() == canonical(state)
    original = path.read_bytes()
    state["si-000000000457"] = request_record()  # 1111 decimal, new unique ID
    assert len(canonical(state)) == 225 * 1112 + 2
    with pytest.raises(Refusal, match="expanded_values"):
        measure(state)
    with pytest.raises(InvalidApprovalState) as error:
        gate._save(state)
    assert isinstance(error.value.__cause__, InvalidTelemetryValue)
    assert path.read_bytes() == original


def test_uuid_collision_overwrites_instead_of_adding(tmp_path, monkeypatch):
    seams(monkeypatch)
    approval = "si-" + HEX[:12]
    raw = canonical({approval: {"status": "pending"}})
    gate, path = gate_at(tmp_path, raw)
    record = request_record()
    report = forecast(raw, {"kind": "request", "id": approval, "record": record})
    assert gate.request(module_id=1, module_slug="synthetic", action_type="generic",
                        summary="x", payload={}) == approval
    assert len(gate._load()) == 1
    assert len(path.read_bytes()) == report["prospective"]["encoded_bytes"]


def test_terminal_age_does_not_grant_archive_capacity():
    state = {"id": {"status": "approved", "decided_at": -1e100, "decided_by": None}}
    raw = canonical(state)
    report = forecast(raw, {"kind": "decision", "id": "id", "status": "rejected",
                            "timestamp": STAMP, "actor": None})
    assert report["archive_eligibility"] == 0
    assert report["live_usage"] == "UNKNOWN"
    assert report["baseline"]["expanded_values"] == 5


@pytest.mark.parametrize("mutant", ["count_keys", "deduplicate_alias", "utf8", "drop_indent", "drop_sort"])
def test_wrong_reference_mutants_are_detected(mutant):
    # Auditor chooses one actual function-source mutation via a synthetic test
    # environment selector. Mutant run MUST fail this oracle assertion.
    selected = os.environ.get("GATE_FORECAST_MUTANT")
    namespace = dict(globals())
    count_fn, bytes_fn = measure, canonical
    if selected == mutant:
        if mutant == "count_keys":
            source = inspect.getsource(measure).replace(
                "children = list(item.items())", "count += len(item); children = list(item.items())")
            exec(source, namespace)
            count_fn = namespace["measure"]
        elif mutant == "deduplicate_alias":
            source = inspect.getsource(measure).replace("active.remove(item)", "pass").replace(
                'raise Refusal("cycle")', 'parent[slot] = []; continue')
            exec(source, namespace)
            count_fn = namespace["measure"]
        else:
            source = inspect.getsource(canonical)
            if mutant == "utf8":
                source = source.replace("allow_nan=False", "allow_nan=False, ensure_ascii=False")
            elif mutant == "drop_indent":
                source = source.replace("indent=2, ", "")
            else:
                source = source.replace("sort_keys=True, ", "")
            exec(source, namespace)
            bytes_fn = namespace["canonical"]
    shared = [0]
    state = {"z": shared, "a": shared, "u": "é"}
    assert count_fn(state)[1] == 6
    expected = b'{\n  "a": [\n    0\n  ],\n  "u": "\\u00e9",\n  "z": [\n    0\n  ]\n}'
    assert bytes_fn(state) == expected


@pytest.mark.parametrize("raw,reason", [
    (b"{}" + b" " * (LIMIT - 1), "raw_file_bytes"),
    (b'{"x":0,"x":1}', "duplicate_key"),
    (b'{"x":NaN}', "nonfinite"),
    (b'{"x":1e999}', "nonfinite"),
    (b"[]", "root_not_object"),
    (b"\xff", "UnicodeDecodeError"),
    (b"{", "JSONDecodeError"),
])
def test_forecast_source_refusals_return_contract(tmp_path, raw, reason):
    report = forecast(raw, {"kind": "decision", "id": "missing", "status": "approved",
                            "timestamp": STAMP, "actor": None})
    assert report["baseline"] == {"unavailable_reason": reason}
    assert report["prospective"] == {"admitted": False, "reason": reason,
                                     "stage": "source", "provenance": "gate.py:77-88"}
    assert report["source_sha256"] == hashlib.sha256(raw).hexdigest()
    gate, path = gate_at(tmp_path, raw)
    with pytest.raises(InvalidApprovalState):
        gate._load()
    assert path.read_bytes() == raw


def test_collision_replacement_can_repair_unsavable_baseline(tmp_path, monkeypatch):
    seams(monkeypatch)
    approval = "si-" + HEX[:12]
    state = {approval: {"status": "pending", "oversize": [0] * 10000}}
    raw = json.dumps(state, separators=(",", ":")).encode()
    gate, path = gate_at(tmp_path, raw)
    assert gate._load() == state
    op = {"kind": "request", "id": approval, "record": request_record()}
    report = forecast(raw, op)
    assert report["baseline"]["unavailable_reason"] == "expanded_values"
    assert report["prospective"]["admitted"] is True
    gate.request(module_id=1, module_slug="synthetic", action_type="generic", summary="x", payload={})
    assert path.read_bytes() == canonical({approval: request_record()})
