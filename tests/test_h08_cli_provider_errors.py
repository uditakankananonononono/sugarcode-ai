"""AUTHORED, NOT RUN. H08: expected ProviderError family becomes a typed CLI message, never a traceback.
Base ab1542455bd3065c5c41dd054c44c25a6736d67c. Only the wrapped escape sites are covered; no general CLI privacy claim.
Exit: provider-runtime 1; JSON {error} on stdout for the JSON commands; no new codes."""
import json

import pytest

from sugarcode.cli import main
from sugarcode.llm.providers import ProviderError
from sugarcode.llm.tool_call_shape import ToolCallShapeError

PROFILES = "SUGARCODE_MODEL_PROFILES"
ROUTE = "SUGARCODE_MODEL_ROUTE"
SECRET_NAME = "secret-lab-box"
SECRET_ROUTE = "zz-secret-route"
GOOD = [{"name": SECRET_NAME, "base_url": "http://10.9.8.7:9000/v1", "model": "m", "kind": "self_hosted"}]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv(PROFILES, raising=False)
    monkeypatch.delenv(ROUTE, raising=False)


@pytest.fixture
def no_router(monkeypatch):
    monkeypatch.setattr("sugarcode.llm.agent.route_modules", lambda q, k=3: [])
    monkeypatch.setattr("sugarcode.llm.agent.tools_for_modules", lambda m, limit=24: [])


def run(argv, capsys):
    rc = main(argv)
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def only_error(out):
    data = json.loads(out)
    assert set(data) == {"error"}
    return data["error"]


def no_leak(*texts):
    for t in texts:
        assert SECRET_NAME not in t and SECRET_ROUTE not in t
        assert "10.9.8.7" not in t and "Traceback" not in t


# ---- loader failures: SAFE H04 message, top-level {error}, exit 1 -------------------------------------------

LOADER_BAD = '[1]'
LOADER_MSG = "SUGARCODE_MODEL_PROFILES item 0 must be a JSON object"


@pytest.mark.parametrize("argv", [["models", "list"], ["models", "check"], ["models", "check", "ollama"],
                                  ["ask", "q"], ["ask", "q", "--profile", "ollama"]])
def test_loader_failure_is_top_level_safe_message(argv, monkeypatch, capsys, no_router):
    monkeypatch.setenv(PROFILES, LOADER_BAD)
    rc, out, err = run(argv, capsys)
    assert rc == 1 and err == ""
    assert only_error(out) == LOADER_MSG


def test_loader_failure_never_echoes_custom_name(monkeypatch, capsys):
    bad = [dict(GOOD[0], nonsense=1)]
    monkeypatch.setenv(PROFILES, json.dumps(bad))
    rc, out, err = run(["models", "list"], capsys)
    assert rc == 1
    msg = only_error(out)
    assert "unknown fields" in msg and "nonsense" in msg
    no_leak(out, err)


# ---- unknown route after a passing preflight: UNSAFE source, generic text, class name only ------------------

def test_models_check_unknown_route_is_generic(monkeypatch, capsys):
    monkeypatch.setenv(PROFILES, json.dumps(GOOD))
    monkeypatch.setenv(ROUTE, f"ollama,{SECRET_ROUTE}")
    rc, out, err = run(["models", "check"], capsys)
    assert rc == 1 and err == ""
    assert only_error(out) == "ProviderError: model provider error (details withheld)"
    no_leak(out, err)


def test_ask_unknown_route_is_generic(monkeypatch, capsys, no_router):
    monkeypatch.setenv(PROFILES, json.dumps(GOOD))
    rc, out, err = run(["ask", "q", "--route", f"{SECRET_ROUTE},ollama"], capsys)
    assert rc == 1 and err == ""
    assert only_error(out) == "ProviderError: model provider error (details withheld)"
    no_leak(out, err)


# ---- error AFTER preflight (config changed in between, or resolve path): generic, zero exception text --------

def test_models_check_error_after_preflight_has_zero_exception_text(monkeypatch, capsys):
    def boom(*a, **k):
        raise ProviderError(f"{SECRET_NAME} needs KEY at http://10.9.8.7")
    monkeypatch.setattr("sugarcode.llm.providers.parse_route", boom)
    rc, out, err = run(["models", "check"], capsys)
    assert rc == 1
    assert only_error(out) == "ProviderError: model provider error (details withheld)"
    no_leak(out, err)


def test_models_list_error_after_preflight_is_generic(monkeypatch, capsys):
    def boom(*a, **k):
        raise ProviderError(SECRET_NAME)
    monkeypatch.setattr("sugarcode.llm.providers.profile_status", boom)
    rc, out, err = run(["models", "list"], capsys)
    assert rc == 1
    assert only_error(out) == "ProviderError: model provider error (details withheld)"
    no_leak(out, err)


def test_ask_error_after_preflight_is_generic(monkeypatch, capsys):
    def boom(*a, **k):
        raise ProviderError(SECRET_NAME)
    monkeypatch.setattr("sugarcode.llm.agent.ask", boom)
    rc, out, err = run(["ask", "q"], capsys)
    assert rc == 1
    assert only_error(out) == "ProviderError: model provider error (details withheld)"
    no_leak(out, err)


def test_subclass_of_provider_error_uses_its_class_name_and_no_text(monkeypatch, capsys):
    class LabBoxError(ProviderError):
        pass

    def boom(*a, **k):
        raise LabBoxError(SECRET_NAME)
    monkeypatch.setattr("sugarcode.llm.agent.ask", boom)
    rc, out, err = run(["ask", "q"], capsys)
    assert rc == 1
    assert only_error(out) == "LabBoxError: model provider error (details withheld)"
    assert SECRET_NAME not in out


# ---- shared ask: container ToolCallShapeError is an expected typed error ---------------------------------------

def test_shared_ask_container_shape_error_message(monkeypatch, capsys):
    def boom(*a, **k):
        raise ToolCallShapeError("tool_calls must be a list, got str")
    monkeypatch.setattr("sugarcode.llm.shared.shared_ask", boom)
    rc, out, err = run(["shared", "ask", "q"], capsys)
    assert rc == 1 and err == ""
    assert only_error(out) == "ToolCallShapeError: tool_calls must be a list, got str"


def test_shared_ask_shape_error_subclass_same_classification(monkeypatch, capsys):
    class Sub(ToolCallShapeError):
        pass

    def boom(*a, **k):
        raise Sub("tool call 2 name must be a string, got int")
    monkeypatch.setattr("sugarcode.llm.shared.shared_ask", boom)
    rc, out, err = run(["shared", "ask", "q"], capsys)
    assert rc == 1
    assert only_error(out) == "Sub: tool call 2 name must be a string, got int"


def test_shared_ask_plain_provider_error_is_generic(monkeypatch, capsys):
    def boom(*a, **k):
        raise ProviderError(SECRET_NAME)
    monkeypatch.setattr("sugarcode.llm.shared.shared_ask", boom)
    rc, out, err = run(["shared", "ask", "q"], capsys)
    assert rc == 1
    assert only_error(out) == "ProviderError: model provider error (details withheld)"
    no_leak(out, err)


# ---- no catch-all: unexpected bugs keep behavior ---------------------------------------------------------------

@pytest.mark.parametrize("argv,target", [(["shared", "ask", "q"], "sugarcode.llm.shared.shared_ask"),
                                         (["ask", "q"], "sugarcode.llm.agent.ask"),
                                         (["models", "list"], "sugarcode.llm.providers.profile_status")])
def test_non_provider_errors_still_propagate(argv, target, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("bug")
    monkeypatch.setattr(target, boom)
    with pytest.raises(RuntimeError, match="bug"):
        main(argv)


# ---- unchanged behavior when config is fine --------------------------------------------------------------------

def test_models_list_valid_config_still_lists(monkeypatch, capsys):
    monkeypatch.setenv(PROFILES, json.dumps(GOOD))
    rc, out, err = run(["models", "list"], capsys)
    assert rc == 0
    names = {r["name"] for r in json.loads(out)}
    assert "ollama" in names and SECRET_NAME in names
