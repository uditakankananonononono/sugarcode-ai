"""AUTHORED, NOT RUN. H09: pre-existing ERROR-PATH echoes of str(e) become fixed generic + class name.
Base 240b620c5fd65a8ccf4c6218dd52eb91f4a0e81c. Written BEFORE the code change.
Scope: AskResult.skipped / .error from ask(), resolve_route skipped text, profile_status reason, `models check` row error,
health() error sources that can carry OS/network text. Successful-output fields (profile names, base_url, model) are NOT
changed and no general name-hiding is claimed. chat() raise text is not changed (only the catch sites classify)."""
import json
import urllib.error

import pytest

from sugarcode.cli import main
from sugarcode.llm import agent as A
from sugarcode.llm import providers as P
from sugarcode.llm.providers import ChatClient, ProviderError
from sugarcode.llm.tool_call_shape import ToolCallShapeError

GEN = "ProviderError: model provider error (details withheld)"
SHAPE = "ToolCallShapeError: model provider error (details withheld)"
SECRET_NAME = "secret-lab-box"
SECRET_ENV = "SECRET_KEY_ENV_LABEL"
SECRET_HOST = "10.9.8.7"
NEEDS_KEY = {"name": SECRET_NAME, "base_url": f"http://{SECRET_HOST}:9000/v1", "model": "m",
             "kind": "self_hosted", "api_key_env": SECRET_ENV, "requires_key": True}
OPEN = {"name": "open-box", "base_url": "http://10.1.1.1:9000/v1", "model": "m", "kind": "self_hosted"}


def env_with(*profiles, **extra):
    e = {"SUGARCODE_MODEL_PROFILES": json.dumps(list(profiles))}
    e.update(extra)
    return e


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.delenv("SUGARCODE_MODEL_PROFILES", raising=False)
    monkeypatch.delenv("SUGARCODE_MODEL_ROUTE", raising=False)
    monkeypatch.setattr(A, "route_modules", lambda q, k=3: [])
    monkeypatch.setattr(A, "tools_for_modules", lambda m, limit=24: [])


def no_leak(text):
    for s in (SECRET_NAME, SECRET_ENV, SECRET_HOST, "Traceback"):
        assert s not in text


# ---- the helper ----
def test_error_text_is_class_plus_fixed_text_for_any_provider_error():
    assert P.error_text(ProviderError(f"{SECRET_NAME} at {SECRET_HOST}")) == GEN
    assert P.error_text(ToolCallShapeError(f"{SECRET_NAME}: tool_calls must be a list, got str")) == SHAPE

    class LabError(ProviderError):
        pass
    assert P.error_text(LabError(SECRET_NAME)) == "LabError: model provider error (details withheld)"


# ---- resolve_route / profile_status ----
def test_resolve_route_skipped_text_is_generic():
    env = env_with(NEEDS_KEY, SUGARCODE_MODEL_ROUTE=SECRET_NAME)
    clients, skipped = P.resolve_route(env=env)
    assert clients == [] and skipped == [GEN]
    no_leak(json.dumps(skipped))


def test_profile_status_reason_is_generic_and_fields_unchanged():
    rows = {r["name"]: r for r in P.profile_status(env=env_with(NEEDS_KEY, OPEN))}
    bad, good = rows[SECRET_NAME], rows["open-box"]
    assert bad["ready"] is False and bad["reason"] == GEN
    assert set(bad) == set(good)            # same keys in error and success rows (name/base_url/model stay as before)
    assert good["ready"] is True and good["reason"] == "configured"
    assert SECRET_ENV not in json.dumps(bad) and "needs" not in bad["reason"]


# ---- ask(): AskResult.skipped / error ----
def test_ask_profile_path_unknown_profile_is_generic():
    res = A.ask("q", profile=SECRET_NAME, env=env_with(OPEN))
    assert res.skipped == [GEN] and res.error == GEN
    no_leak(json.dumps(res.to_dict()))


def test_ask_profile_path_missing_key_is_generic_no_env_label():
    res = A.ask("q", profile=SECRET_NAME, env=env_with(NEEDS_KEY))
    assert res.skipped == [GEN] and res.error == GEN
    no_leak(json.dumps(res.to_dict()))


def test_ask_library_loader_failure_is_generic_too():
    res = A.ask("q", profile="ollama", env={"SUGARCODE_MODEL_PROFILES": "[1]"})
    assert res.skipped == [GEN] and res.error == GEN


class _Boom:
    supports_tools = True

    def __init__(self, profile, exc):
        self.profile, self._exc = profile, exc

    def chat(self, messages, tools=None, **kw):
        raise self._exc


def test_ask_run_failure_text_is_generic(monkeypatch):
    c = _Boom(SECRET_NAME, ProviderError(f"{SECRET_NAME} HTTP 500: body {SECRET_HOST} <html>secret body</html>"))
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: ([c], []))
    res = A.ask("q", route="x", env={})
    assert res.answer is None and res.skipped == [GEN]
    assert res.error == "no model profile answered; the routed modules and tools are listed so you can run them directly"
    no_leak(json.dumps(res.to_dict()))


def test_ask_run_shape_error_with_profile_prefix_is_generic(monkeypatch):
    c = _Boom(SECRET_NAME, ToolCallShapeError(f"{SECRET_NAME}: tool_calls must be a list, got str"))
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: ([c], []))
    res = A.ask("q", route="x", env={})
    assert res.skipped == [SHAPE]
    no_leak(json.dumps(res.to_dict()))


def test_ask_success_schema_and_profile_field_unchanged(monkeypatch):
    class Ok:
        supports_tools = True
        profile = "open-box"

        def chat(self, messages, tools=None, **kw):
            return {"content": " hi "}
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: ([Ok()], []))
    d = A.ask("q", route="x", env={}).to_dict()
    assert d["profile"] == "open-box" and d["answer"] == "hi"
    assert list(d) == ["answer", "profile", "modules", "tools_offered", "tool_calls", "skipped_profiles", "error"]


def test_failed_then_good_profile_keeps_fallback_and_records_generic(monkeypatch):
    bad = _Boom(SECRET_NAME, ProviderError(SECRET_NAME))

    class Good:
        supports_tools = True
        profile = "good"

        def chat(self, messages, tools=None, **kw):
            return {"content": "answer"}
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: ([bad, Good()], ["x"]))
    res = A.ask("q", route="x", env={})
    assert res.profile == "good" and res.answer == "answer"
    assert res.skipped == ["x", GEN]  # a skipped list handed in by resolve_route is passed through as given


# ---- models check row error ----
def run(argv, capsys):
    rc = main(argv)
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def test_models_check_unknown_profile_row_error_is_generic(monkeypatch, capsys):
    monkeypatch.setenv("SUGARCODE_MODEL_PROFILES", json.dumps([OPEN]))
    rc, out, err = run(["models", "check", "nope-name"], capsys)
    rows = json.loads(out)
    assert rc == 1 and err == ""
    assert rows == [{"profile": "nope-name", "ok": False, "error": GEN}]   # profile key: same key success rows emit
    assert "open-box" not in out                                              # the known-profile list is gone


def test_models_check_missing_key_row_has_no_env_label(monkeypatch, capsys):
    monkeypatch.setenv("SUGARCODE_MODEL_PROFILES", json.dumps([NEEDS_KEY]))
    rc, out, err = run(["models", "check", SECRET_NAME], capsys)
    rows = json.loads(out)
    assert rc == 1 and rows[0]["error"] == GEN and set(rows[0]) == {"profile", "ok", "error"}
    assert SECRET_ENV not in out and SECRET_HOST not in out


def test_models_list_reason_via_cli_is_generic(monkeypatch, capsys):
    monkeypatch.setenv("SUGARCODE_MODEL_PROFILES", json.dumps([NEEDS_KEY]))
    rc, out, err = run(["models", "list"], capsys)
    row = next(r for r in json.loads(out) if r["name"] == SECRET_NAME)
    assert rc == 0 and row["ready"] is False and row["reason"] == GEN
    assert SECRET_ENV not in row["reason"]


# ---- health(): sources that can carry OS/network text are class-only; constants stay ----
def _client(url="http://stub.test/v1"):
    return ChatClient(profile="p1", base_url=url, model="m", kind="self_hosted")


@pytest.mark.parametrize("exc,cls", [
    (urllib.error.URLError(f"{SECRET_HOST} refused"), "URLError"),
    (TimeoutError(f"{SECRET_HOST} slow"), "TimeoutError"),
    (OSError(f"{SECRET_HOST} no route"), "OSError"),
    (ConnectionRefusedError(f"{SECRET_HOST}"), "ConnectionRefusedError")])
def test_health_models_probe_error_is_class_only(monkeypatch, exc, cls):
    def fake(req, timeout=None):
        raise exc
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    out = _client().health()
    assert out == {"profile": "p1", "ok": False, "error": f"unreachable: {cls}"}
    no_leak(json.dumps(out))


def test_health_invalid_json_probe_is_class_only(monkeypatch):
    class R:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"not json " + SECRET_HOST.encode()
    monkeypatch.setattr(P.urllib.request, "urlopen", lambda req, timeout=None: R())
    out = _client().health()
    assert out["ok"] is False and out["error"].startswith("unreachable: ") and set(out) == {"profile", "ok", "error"}
    no_leak(json.dumps(out))


def test_health_http_code_constant_stays(monkeypatch):
    def fake(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "x", {}, None)
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    assert _client().health() == {"profile": "p1", "ok": False, "error": "HTTP 503"}


def test_health_whoami_unreachable_is_class_only(monkeypatch):
    class R:
        def __init__(self, raw):
            self.raw = raw

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return self.raw

    def fake(req, timeout=None):
        if req.full_url.endswith("/models"):
            return R(b'{"data": []}')
        raise urllib.error.URLError(f"{SECRET_HOST} refused")
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    out = ChatClient(profile="hf1", base_url="https://router.huggingface.co/v1", model="m", kind="hosted_free").health()
    assert out["token_valid"] == "unreachable: URLError" and out["ok"] is False
    no_leak(json.dumps(out))


# ---- chat() raise text is intentionally NOT changed by H09 (catch sites classify) ----
def test_chat_still_raises_provider_error_with_its_original_type(monkeypatch):
    def fake(req, timeout=None):
        raise urllib.error.URLError("refused")
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    with pytest.raises(ProviderError):
        _client().chat([{"role": "user", "content": "q"}])
