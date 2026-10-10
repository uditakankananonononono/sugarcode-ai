"""Duplicate-key ambiguity and typed serialization failures, without migration."""
import json
import sys

import pytest

from sugarcode.self_improve.events import GapEvent, GapEventStore
from sugarcode.self_improve.json_values import InvalidTelemetryValue


@pytest.mark.parametrize("row", [
    '{"module_slug":"m","module_slug":"m","signature":"x"}',
    '{"module_slug":"wrong","module_slug":"m","signature":"x"}',
    '{"module_slug":"m","signature":"x","exemplar":{"a":1,"a":2}}',
    '{"module_slug":"m","signature":"x","exemplar":[{"a":1,"a":1}]}',
    r'{"module_slug":"m","signature":"x","exemplar":{"a":1,"\u0061":2}}',
    '{"module_slug":"m","signature":"x","at":0,"at":1}',
])
def test_duplicate_keys_fail_closed_at_exact_row(tmp_path, row):
    store = GapEventStore(tmp_path)
    store.append(GapEvent("m", "good", at=0))
    path = tmp_path / "m.gap-events.jsonl"
    with path.open("a") as stream:
        stream.write(row + "\n")
    before = path.read_bytes()
    with pytest.raises(InvalidTelemetryValue, match="row 2") as caught:
        store.all("m")
    assert isinstance(caught.value.__cause__, InvalidTelemetryValue)
    assert "duplicate" in str(caught.value.__cause__)
    assert path.read_bytes() == before


def test_equal_keys_in_separate_objects_are_valid(tmp_path):
    store = GapEventStore(tmp_path)
    store.append(GapEvent("m", "ok", at=0, exemplar=[{"a": 1}, {"a": 2}]))
    assert store.all("m")[0].exemplar == [{"a": 1}, {"a": 2}]


@pytest.mark.parametrize("error", [ValueError, TypeError, RecursionError])
@pytest.mark.parametrize("existing", [False, True])
def test_encoder_failures_are_typed_and_never_open_append(tmp_path, monkeypatch, error, existing):
    store = GapEventStore(tmp_path)
    path = tmp_path / "m.gap-events.jsonl"
    if existing:
        store.append(GapEvent("m", "good", at=0))
    before = path.read_bytes() if existing else None
    def broken(*args, **kwargs):
        raise error("encoder failure")
    monkeypatch.setattr(json, "dumps", broken)
    with pytest.raises(InvalidTelemetryValue, match="serialization") as caught:
        store.append(GapEvent("m", "bad", at=0, exemplar=1))
    assert type(caught.value.__cause__) is error
    if existing:
        assert path.read_bytes() == before
    else:
        assert not path.exists()


def test_real_integer_conversion_limit_is_typed(tmp_path):
    if not hasattr(sys, "set_int_max_str_digits"):
        pytest.skip("interpreter has no configurable integer string limit")
    old = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        store = GapEventStore(tmp_path)
        store.append(GapEvent("m", "good", at=0))
        path = tmp_path / "m.gap-events.jsonl"
        before = path.read_bytes()
        with pytest.raises(InvalidTelemetryValue, match="serialization"):
            store.append(GapEvent("m", "bad", at=0, exemplar=10**700))
        assert path.read_bytes() == before
        with path.open("a") as stream:
            stream.write('{"module_slug":"m","signature":"big","exemplar":' + "1" * 701 + '}\n')
        historical = path.read_bytes()
        with pytest.raises(InvalidTelemetryValue, match="row 2"):
            store.all("m")
        assert path.read_bytes() == historical
    finally:
        sys.set_int_max_str_digits(old)
