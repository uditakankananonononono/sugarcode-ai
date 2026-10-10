"""AUTHORED, NOT RUN. H02: malformed model tool calls get a typed error (ToolCallShapeError, a ProviderError) in BOTH
agent._run and shared.shared_ask, through ONE helper (llm/tool_call_shape.py). Two failure classes are kept apart:
- CONTAINER failure: a truthy non-list tool_calls value raises ToolCallShapeError, nothing runs.
- PER-CALL failure: one malformed entry. In agent._run the whole attempt fails (raises, nothing in the batch runs, ask() falls back);
  in shared_ask that call gets a typed error result and valid siblings still execute."""
from types import SimpleNamespace

import pytest

from sugarcode.llm import agent as A
from sugarcode.llm import shared as S
from sugarcode.llm.providers import ProviderError
from sugarcode.llm.tool_call_shape import (
    ToolCallShapeError, tool_call_batch, tool_call_container, tool_call_fields)


def oa(name="m__f", arguments="{}", id="c1"):
    return {"id": id, "type": "function", "function": {"name": name, "arguments": arguments}}


# ---------------- helper: container ----------------
def test_shape_error_is_a_provider_error_subclass():
    assert issubclass(ToolCallShapeError, ProviderError) and ToolCallShapeError is not ProviderError


@pytest.mark.parametrize("raw", [None, [], "", 0, {}, False, 0.0])
def test_container_missing_or_falsey_means_no_calls(raw):
    assert tool_call_container(raw) == []


@pytest.mark.parametrize("raw", [{"a": 1}, "abc", 5, True, 1.5, ("x",)])
def test_container_truthy_non_list_raises(raw):
    with pytest.raises(ToolCallShapeError) as e:
        tool_call_container(raw)
    assert "tool_calls" in str(e.value)


def test_container_list_returned_as_is():
    raw = [oa()]
    assert tool_call_container(raw) is raw


# ---------------- helper: OpenAI-style entry ----------------
def test_fields_valid_entry():
    f = tool_call_fields(oa("m__f", '{"a": 1}', "c9"))
    assert (f.name, f.arguments, f.id) == ("m__f", '{"a": 1}', "c9")


def test_fields_id_missing_is_empty_string_and_empty_name_is_a_str():
    c = oa("")
    del c["id"]
    f = tool_call_fields(c)
    assert f.id == "" and f.name == ""


@pytest.mark.parametrize("arguments", [None, "", {}, [1], 5, '{"a": 1}'])
def test_fields_arguments_pass_through_unjudged(arguments):
    assert tool_call_fields(oa(arguments=arguments)).arguments == arguments


@pytest.mark.parametrize("entry", [None, 1, "x", [], ["a"], 1.5, True])
def test_fields_non_dict_entry_raises(entry):
    with pytest.raises(ToolCallShapeError):
        tool_call_fields(entry)


@pytest.mark.parametrize("function", [None, "f", [], 3, True])
def test_fields_present_non_dict_function_raises(function):
    with pytest.raises(ToolCallShapeError):
        tool_call_fields({"id": "c", "function": function})


def test_fields_missing_function_raises():
    with pytest.raises(ToolCallShapeError):
        tool_call_fields({"id": "c"})


@pytest.mark.parametrize("name", [None, 5, ["a"], {"a": 1}, True])
def test_fields_non_str_name_raises(name):
    with pytest.raises(ToolCallShapeError):
        tool_call_fields({"id": "c", "function": {"name": name, "arguments": "{}"}})


def test_fields_missing_name_raises():
    with pytest.raises(ToolCallShapeError):
        tool_call_fields({"id": "c", "function": {"arguments": "{}"}})


@pytest.mark.parametrize("id_", [None, 5, ["a"], True])
def test_fields_present_non_str_id_raises(id_):
    c = oa()
    c["id"] = id_
    with pytest.raises(ToolCallShapeError):
        tool_call_fields(c)


def test_fields_error_can_name_the_index():
    with pytest.raises(ToolCallShapeError) as e:
        tool_call_fields(None, index=3)
    assert "3" in str(e.value)


# ---------------- helper: flat entry (instinct_models ChatResult.tool_calls) ----------------
def test_flat_valid_entry_and_function_key_is_not_required():
    f = tool_call_fields({"name": "m__f", "arguments": {"a": 1}}, flat=True)
    assert (f.name, f.arguments, f.id) == ("m__f", {"a": 1}, "")


@pytest.mark.parametrize("entry", [None, 1, "x", [], ["a"]])
def test_flat_non_dict_entry_raises(entry):
    with pytest.raises(ToolCallShapeError):
        tool_call_fields(entry, flat=True)


@pytest.mark.parametrize("name", [None, 5, ["a"], {"a": 1}])
def test_flat_non_str_name_raises(name):
    with pytest.raises(ToolCallShapeError):
        tool_call_fields({"name": name, "arguments": {}}, flat=True)


def test_flat_missing_name_raises_and_empty_name_is_ok():
    with pytest.raises(ToolCallShapeError):
        tool_call_fields({"arguments": {}}, flat=True)
    assert tool_call_fields({"name": ""}, flat=True).name == ""


# ---------------- helper: batch ----------------
def test_batch_validates_every_entry_before_returning():
    assert [f.name for f in tool_call_batch([oa("a"), oa("b")])] == ["a", "b"]
    with pytest.raises(ToolCallShapeError):
        tool_call_batch([oa("a"), None, oa("b")])
    with pytest.raises(ToolCallShapeError):
        tool_call_batch({"a": 1})
    assert tool_call_batch(None) == [] and tool_call_batch([]) == []


# ---------------- agent._run ----------------
class _Client:
    profile = "stub"
    supports_tools = True

    def __init__(self, *messages):
        self._messages = list(messages)
        self.sent = []

    def chat(self, messages, tools=None, **kw):
        self.sent.append([dict(m) for m in messages])
        return self._messages.pop(0)


@pytest.fixture
def ran(monkeypatch):
    log = []
    monkeypatch.setattr(A, "call_tool", lambda name, arguments: log.append((name, arguments)) or {"result": name})
    return log


def test_run_valid_batch_executes_in_order_with_unchanged_trace(ran):
    c = _Client({"content": "", "tool_calls": [oa("a", None, "c1"), oa("b", '{"x": 1}', "c2")]}, {"content": " done "})
    answer, trace = A._run(c, "q", [], 4)
    assert answer == "done"
    assert ran == [("a", "{}"), ("b", '{"x": 1}')]
    assert trace == [{"tool": "a", "arguments": None, "ok": True}, {"tool": "b", "arguments": '{"x": 1}', "ok": True}]
    tool_msgs = [m for m in c.sent[1] if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_msgs] == ["c1", "c2"]


def test_run_per_call_failure_fails_the_attempt_and_runs_nothing(ran):
    c = _Client({"content": "", "tool_calls": [oa("a"), None, oa("b")]})
    with pytest.raises(ToolCallShapeError) as e:
        A._run(c, "q", [], 4)
    assert str(e.value).startswith("stub")
    assert ran == []  # the valid first call was NOT executed


@pytest.mark.parametrize("container", [{"a": 1}, "abc", 5, True])
def test_run_container_failure_raises_and_runs_nothing(ran, container):
    c = _Client({"content": "", "tool_calls": container})
    with pytest.raises(ToolCallShapeError):
        A._run(c, "q", [], 4)
    assert ran == []


@pytest.mark.parametrize("container", [None, [], "", 0])
def test_run_missing_or_falsey_container_is_a_plain_answer(ran, container):
    c = _Client({"content": " hi ", "tool_calls": container})
    assert A._run(c, "q", [], 4) == ("hi", [])
    assert ran == []


def test_run_unknown_tool_name_is_still_a_call_error_not_a_shape_error():
    c = _Client({"content": "", "tool_calls": [oa("no_such__tool")]}, {"content": "ok"})
    answer, trace = A._run(c, "q", [], 4)
    assert answer == "ok" and trace[0]["ok"] is False


# ---------------- ask(): fallback and recording ----------------
def _ask_with(monkeypatch, *clients):
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: (list(clients), []))
    return A.ask("codon optimize a protein for E. coli expression", route="x", env={})


@pytest.mark.parametrize("bad", [[None], {"a": 1}, [{"id": "c", "function": "f"}], [oa(name=5)]])
def test_ask_falls_back_and_records_shape_error(monkeypatch, bad):
    bad_c = _Client({"content": "", "tool_calls": bad})
    bad_c.profile = "bad"
    good = _Client({"content": "answer"})
    good.profile = "good"
    res = _ask_with(monkeypatch, bad_c, good)
    assert res.profile == "good" and res.answer == "answer"
    assert any(s.startswith("bad") for s in res.skipped)


def test_ask_with_only_malformed_profile_reports_error_not_exception(monkeypatch):
    bad_c = _Client({"content": "", "tool_calls": [None]})
    bad_c.profile = "bad"
    res = _ask_with(monkeypatch, bad_c)
    assert res.answer is None and res.error and any(s.startswith("bad") for s in res.skipped)


# ---------------- shared_ask ----------------
def _router(tool_calls):
    result = SimpleNamespace(provider="p", model="m", text="t", tool_calls=tool_calls)
    res = SimpleNamespace(ok=True, attempts=[], result=result)
    return SimpleNamespace(run=lambda task: res)


@pytest.fixture
def offered_name():
    tools, _ = S.shared_tools("design a CRISPR guide for TP53")
    return tools[0]["name"]


def test_shared_per_call_failure_recovers_and_valid_siblings_execute(monkeypatch, offered_name):
    log = []
    monkeypatch.setattr(S, "call_tool", lambda name, arguments: log.append((name, arguments)) or {"result": 1})
    calls = [{"name": offered_name, "arguments": {"a": 1}}, None, {"name": 5, "arguments": {}},
             {"name": offered_name}, {"name": "os__system", "arguments": {}}, {"arguments": {}}]
    out = S.shared_ask("design a CRISPR guide for TP53", router=_router(calls))
    results = out["tool_results"]
    assert len(results) == len(calls)  # one result per call, order kept
    assert results[0] == {"result": 1} and results[3] == {"result": 1}
    assert "malformed tool call" in results[1]["error"]
    assert "malformed tool call" in results[2]["error"]
    assert "not offered" in results[4]["error"]
    assert "malformed tool call" in results[5]["error"]
    assert log == [(offered_name, {"a": 1}), (offered_name, {})]
    assert out["tool_calls"] is calls


@pytest.mark.parametrize("container", [{"name": "x"}, "abc", 5, True])
def test_shared_container_failure_raises_and_runs_nothing(monkeypatch, container):
    log = []
    monkeypatch.setattr(S, "call_tool", lambda name, arguments: log.append(name) or {"result": 1})
    with pytest.raises(ToolCallShapeError):
        S.shared_ask("design a CRISPR guide for TP53", router=_router(container))
    assert log == []


@pytest.mark.parametrize("container", [[], None, "", 0])
def test_shared_falsey_container_has_no_tool_results(monkeypatch, container):
    out = S.shared_ask("design a CRISPR guide for TP53", router=_router(container))
    assert "tool_results" not in out


def test_shared_execute_false_does_not_validate_or_run(monkeypatch):
    log = []
    monkeypatch.setattr(S, "call_tool", lambda name, arguments: log.append(name) or {"result": 1})
    out = S.shared_ask("design a CRISPR guide for TP53", router=_router({"a": 1}), execute=False)
    assert "tool_results" not in out and log == []
