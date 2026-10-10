"""AUTHORED, NOT RUN. H10: sugarcode shared ask boundary, vendored instinct_models untouched.
Base 12a9bc7a55843b990d1b0337cf08f063616c50be. Written BEFORE the code change.
1. RouteAttempt.detail: only the five exact source-proven (outcome, detail) pairs pass through; everything else, every
   ("error", *) included, becomes the fixed text ATTEMPT_DETAIL_WITHHELD. No class is available on RouteAttempt, so none is added.
2. Config failures at shared_config / Router.from_config (config ValueError, lexical OSError/JSONDecodeError, fit
   KeyError/TypeError/AttributeError) return {"ok": False, "config_error_class": <actual class>} and nothing else.
   No catch around router.run or chat, and no catch-all. The CLI prints {"error": class, "message": "<class>: provider setup error (details withheld)"}, exit 1."""
import json
from types import SimpleNamespace

import pytest

from instinct_models import Router
from instinct_models.providers import InklingLocal, ProviderError, ProviderUnavailable
from instinct_models.router import RouteAttempt
from sugarcode.cli import main
from sugarcode.llm import shared

Q = "design a CRISPR guide for TP53"
WITHHELD = "details withheld"
SECRET = "SECRET-VALUE-9f3a"
HOST = "10.9.8.7"

# the five exact source-proven pairs (instinct_models/router.py lines 81, 67, 70, 73 + default at 33, 83)
KEEP = [("escalated", "no tool call"), ("skipped", "not a tool-calling task"),
        ("skipped", "private task never goes to a hosted route"), ("unavailable", ""), ("ok", "")]


def stub_router(attempts, ok=False):
    result = SimpleNamespace(provider="p", model="m", text="t", tool_calls=[]) if ok else None
    res = SimpleNamespace(ok=ok, attempts=attempts, result=result)
    return SimpleNamespace(run=lambda task: res)


def test_constant_declares_the_five_pairs_and_the_fixed_text():
    assert shared.ATTEMPT_DETAIL_WITHHELD == WITHHELD
    assert set(shared.ATTEMPT_CONSTANT_PAIRS) == set(KEEP)


@pytest.mark.parametrize("outcome,detail", KEEP)
def test_exact_constant_pairs_pass_through(outcome, detail):
    out = shared.shared_ask(Q, router=stub_router([RouteAttempt("needle-local", outcome, detail)]))
    assert out["attempts"] == [{"provider": "needle-local", "outcome": outcome, "detail": detail}]


@pytest.mark.parametrize("outcome,detail", [
    ("error", f"HTTP 500 from http://{HOST}:9000/v1/chat/completions: b'{SECRET}'"),
    ("error", f"cannot reach http://{HOST}: refused"),
    ("error", ""), ("error", "x" * 300), ("error", "no tool call"),                 # error never uses the allowlist
    ("escalated", "other"), ("escalated", ""), ("skipped", "other"), ("skipped", ""),
    ("unavailable", "x"), ("ok", "x"), ("ok", "no tool call"), ("weird", "not a tool-calling task"),
    ("weird", ""), ("", "")])
def test_every_other_pair_gets_the_fixed_text_alone(outcome, detail):
    out = shared.shared_ask(Q, router=stub_router([RouteAttempt("inkling-local", outcome, detail)]))
    assert out["attempts"] == [{"provider": "inkling-local", "outcome": outcome, "detail": WITHHELD}]
    assert SECRET not in json.dumps(out) and HOST not in json.dumps(out)


def test_attempts_order_count_and_non_detail_fields_preserved():
    atts = [RouteAttempt("a", "skipped", "not a tool-calling task"), RouteAttempt("b", "error", f"{SECRET}"),
            RouteAttempt("c", "unavailable"), RouteAttempt("d", "ok")]
    out = shared.shared_ask(Q, router=stub_router(atts, ok=True))
    assert [(a["provider"], a["outcome"]) for a in out["attempts"]] == [("a", "skipped"), ("b", "error"),
                                                                       ("c", "unavailable"), ("d", "ok")]
    assert [a["detail"] for a in out["attempts"]] == ["not a tool-calling task", WITHHELD, "", ""]
    assert all(set(a) == {"provider", "outcome", "detail"} for a in out["attempts"])


def test_non_str_detail_does_not_crash_and_is_withheld():
    out = shared.shared_ask(Q, router=stub_router([SimpleNamespace(provider="p", outcome="error", detail=["x"])]))
    assert out["attempts"][0]["detail"] == WITHHELD


# ---- real vendored Router.run with failing transports: detail is never the exception text ----
@pytest.mark.parametrize("exc", [ProviderError(f"HTTP 500 from http://{HOST}: b'{SECRET}'"),
                                 ProviderUnavailable(f"cannot reach http://{HOST}: refused")])
def test_real_router_error_attempt_is_withheld(exc):
    def transport(url, body, headers, timeout):
        raise exc
    r = Router([InklingLocal(f"http://{HOST}:9/v1", "m", transport=transport)])
    out = shared.shared_ask(Q, router=r)
    assert out["ok"] is False
    assert out["attempts"] == [{"provider": r.providers[0].name, "outcome": "error", "detail": WITHHELD}]
    assert SECRET not in json.dumps(out) and HOST not in json.dumps(out)


def test_private_task_hosted_skip_keeps_its_constant_through_the_real_router():
    from instinct_models.providers import InklingHFRouter
    r = Router([InklingHFRouter("m", token="hf_x", transport=lambda *a: {})])
    out = shared.shared_ask(Q, router=r, private=True)
    assert out["attempts"] == [{"provider": r.providers[0].name, "outcome": "skipped",
                                "detail": "private task never goes to a hosted route"}]


# ---- success and no-answer payloads unchanged ----
def test_no_answer_payload_keys_and_error_sentence_unchanged():
    out = shared.shared_ask(Q, router=stub_router([RouteAttempt("a", "unavailable")]))
    assert list(out) == ["modules", "tools_offered", "attempts", "ok", "error"]
    assert out["ok"] is False
    assert out["error"] == "no configured model answered (see attempts); set INSTINCT_* env or HF_TOKEN"


def test_success_payload_keys_unchanged():
    out = shared.shared_ask(Q, router=stub_router([RouteAttempt("a", "ok")], ok=True))
    assert list(out) == ["modules", "tools_offered", "attempts", "ok", "provider", "model", "text", "tool_calls"]


# ---- config failures: P1 config ValueError, P2 OSError/JSONDecodeError, P3 fit shape errors ----
def cfg_error(env):
    out = shared.shared_ask(Q, env=env)
    assert set(out) == {"ok", "config_error_class"} and out["ok"] is False
    return out["config_error_class"]


def test_p1_product_value_error_returns_class_only():
    assert cfg_error({"INSTINCT_PRODUCT": "atlas"}) == "ValueError"
    out = shared.shared_ask(Q, env={"INSTINCT_PRODUCT": SECRET})
    assert out == {"ok": False, "config_error_class": "ValueError"}
    assert SECRET not in json.dumps(out)


def _jsonl(tmp_path, text):
    p = tmp_path / "train.jsonl"
    p.write_text(text)
    return {"INSTINCT_LEXICAL_TRAIN_JSONL": str(p)}


def test_p2_missing_file_is_oserror_class_without_the_path(tmp_path):
    env = {"INSTINCT_LEXICAL_TRAIN_JSONL": str(tmp_path / f"{SECRET}.jsonl")}
    out = shared.shared_ask(Q, env=env)
    assert out == {"ok": False, "config_error_class": "FileNotFoundError"}
    assert SECRET not in json.dumps(out) and str(tmp_path) not in json.dumps(out)


def test_p2_directory_is_oserror_subclass(tmp_path):
    out = shared.shared_ask(Q, env={"INSTINCT_LEXICAL_TRAIN_JSONL": str(tmp_path)})
    assert set(out) == {"ok", "config_error_class"}
    assert out["config_error_class"] in ("IsADirectoryError", "PermissionError")


def test_p2_bad_json_is_json_decode_error_class(tmp_path):
    assert cfg_error(_jsonl(tmp_path, '{"query": ' + SECRET + "\n")) == "JSONDecodeError"


@pytest.mark.parametrize("row,cls", [
    ('{"x": 1}', "KeyError"),                                              # r["query"]
    ('{"query": "q", "answers": [{"x": 1}]}', "KeyError"),                 # ["name"]
    ('[1]', "TypeError"),                                                  # r["query"] on a list
    ('{"query": "q", "answers": [1]}', "TypeError"),                       # 1["name"]
    ('{"query": "q", "answers": [{"name": "n", "arguments": 5}]}', "AttributeError")])   # 5.items()
def test_p3_fit_shape_errors_return_the_actual_class(tmp_path, row, cls):
    assert cfg_error(_jsonl(tmp_path, row + "\n")) == cls


# ---- NO broad catch: other exceptions and anything outside from_config/shared_config propagate ----
def test_runtime_error_from_from_config_propagates(monkeypatch):
    def boom(cls, cfg):
        raise RuntimeError("bug")
    monkeypatch.setattr(shared.Router, "from_config", classmethod(boom))
    with pytest.raises(RuntimeError, match="bug"):
        shared.shared_ask(Q)


def test_provider_error_from_from_config_is_not_swallowed(monkeypatch):
    def boom(cls, cfg):
        raise ProviderError("x")
    monkeypatch.setattr(shared.Router, "from_config", classmethod(boom))
    with pytest.raises(ProviderError):
        shared.shared_ask(Q)


@pytest.mark.parametrize("exc", [ValueError("v"), OSError("o"), KeyError("k"), TypeError("t"), AttributeError("a")])
def test_same_classes_from_router_run_are_not_caught(exc):
    def run(task):
        raise exc
    with pytest.raises(type(exc)):
        shared.shared_ask(Q, router=SimpleNamespace(run=run))


def test_passed_router_skips_config_entirely(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("config must not be read when a router is passed")
    monkeypatch.setattr(shared, "shared_config", boom)
    out = shared.shared_ask(Q, router=stub_router([RouteAttempt("a", "unavailable")]))
    assert out["ok"] is False and "config_error_class" not in out


# ---- CLI ----
def run(argv, capsys):
    rc = main(argv)
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def test_cli_prints_class_and_setup_message_exit_1(monkeypatch, capsys):
    monkeypatch.setattr("sugarcode.llm.shared.shared_ask",
                        lambda *a, **k: {"ok": False, "config_error_class": "FileNotFoundError"})
    rc, out, err = run(["shared", "ask", "q"], capsys)
    assert rc == 1 and err == ""
    assert json.loads(out) == {"error": "FileNotFoundError",
                               "message": "FileNotFoundError: provider setup error (details withheld)"}


def test_cli_end_to_end_product_env_is_not_echoed(monkeypatch, capsys):
    monkeypatch.setenv("INSTINCT_PRODUCT", SECRET)
    rc, out, err = run(["shared", "ask", "q"], capsys)
    assert rc == 1 and err == ""
    assert json.loads(out) == {"error": "ValueError", "message": "ValueError: provider setup error (details withheld)"}
    assert SECRET not in out


def test_cli_no_answer_payload_still_prints_as_before(monkeypatch, capsys):
    payload = {"modules": [], "tools_offered": [], "attempts": [], "ok": False, "error": "no configured model answered"}
    monkeypatch.setattr("sugarcode.llm.shared.shared_ask", lambda *a, **k: payload)
    rc, out, err = run(["shared", "ask", "q"], capsys)
    assert rc == 1 and json.loads(out) == payload
