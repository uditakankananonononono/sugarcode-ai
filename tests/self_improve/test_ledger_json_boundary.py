import json
from decimal import Decimal

import pytest

from sugarcode.self_improve.engine import SelfImprovementEngine


def engine(tmp_path):
    return SelfImprovementEngine(module_id=1, module_slug="m", state_dir=tmp_path)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), Decimal(1), {1:"x"}, object()])
@pytest.mark.parametrize("existing", [False, True])
def test_bad_values_never_append_or_create(tmp_path, bad, existing):
    from sugarcode.self_improve.engine import InvalidLedgerValue
    e = engine(tmp_path)
    if existing:
        e._log("good")
    before = e._ledger_path.read_bytes() if existing else None
    with pytest.raises(InvalidLedgerValue, match="no append"):
        e._log("bad", value=bad)
    if existing:
        assert e._ledger_path.read_bytes() == before
    else:
        assert not e._ledger_path.exists()


@pytest.mark.parametrize("row", [
    '{"module":"m","module":"wrong"}',
    r'{"module":"m","value":{"a":1,"\u0061":2}}',
    '{"module":"m","value":NaN}', '{"module":"m","value":1e999}',
    '{"module":"wrong"}', '[]', '{bad',
])
def test_bad_history_indexed_and_unchanged(tmp_path, row):
    from sugarcode.self_improve.engine import InvalidLedgerValue
    e = engine(tmp_path)
    e._log("good")
    with e._ledger_path.open("a") as stream:
        stream.write("\n" + row + "\n")
    before = e._ledger_path.read_bytes()
    with pytest.raises(InvalidLedgerValue, match="row 3"):
        e.ledger()
    assert e._ledger_path.read_bytes() == before


def test_cycles_and_hostile_methods_never_coerced(tmp_path):
    from sugarcode.self_improve.engine import InvalidLedgerValue
    e = engine(tmp_path)
    cycle=[]; cycle.append(cycle)
    class Hostile:
        def __str__(self):
            pytest.fail("str called")
        def __repr__(self):
            pytest.fail("repr called")
    for value in (cycle,Hostile()):
        with pytest.raises(InvalidLedgerValue):
            e._log("bad", value=value)
    assert not e._ledger_path.exists()


def test_roundtrip_tuple_aliases_and_string_nan(tmp_path):
    e=engine(tmp_path)
    shared=[1,"NaN"]
    value={"a":shared,"b":shared,"tuple":(2,)}
    e._log("valid", value=value)
    shared.append("late")
    assert e.ledger()[0]["value"] == {"a":[1,"NaN"],"b":[1,"NaN"],"tuple":[2]}


def test_value_depth_budget_per_record(tmp_path):
    from sugarcode.self_improve.engine import InvalidLedgerValue
    e=engine(tmp_path)
    e._log("good")
    before=e._ledger_path.read_bytes()
    deep=[]
    for _ in range(66): deep=[deep]
    for value in (deep,[0]*10000):
        with pytest.raises(InvalidLedgerValue): e._log("bad",value=value)
        assert e._ledger_path.read_bytes()==before


@pytest.mark.parametrize("failure", [ValueError,TypeError,RecursionError])
def test_encoder_failure_precedes_file_open(tmp_path, monkeypatch, failure):
    from sugarcode.self_improve.engine import InvalidLedgerValue
    e=engine(tmp_path)
    def broken(*args,**kwargs): raise failure("encoder failed")
    monkeypatch.setattr(json,"dumps",broken)
    with pytest.raises(InvalidLedgerValue) as caught: e._log("bad")
    assert type(caught.value.__cause__) is failure
    assert not e._ledger_path.exists()


def test_foreign_module_override_cannot_poison_fresh_history(tmp_path):
    from sugarcode.self_improve.engine import InvalidLedgerValue
    e=engine(tmp_path)
    with pytest.raises(InvalidLedgerValue): e._log("bad", module="other")
    assert not e._ledger_path.exists()
    e._log("good", module="m")
    assert e.ledger()[0]["module"]=="m"


def test_existing_legacy_string_fields_are_not_reinterpreted(tmp_path):
    e=engine(tmp_path)
    e._ledger_path.write_text('{"module":"m","event":"legacy","value":"NaN"}\n')
    assert e.ledger()==[{"module":"m","event":"legacy","value":"NaN"}]
