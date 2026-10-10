"""AUTHORED, NOT RUN. H22: CHARACTERIZATION of provider-error text, tests only. NO product change.
Base 352ccdc5d25c72c6d45ea11456fdb3ed98c7081f. Pins the status quo; it does not claim any new privacy property.
(i)   caught/recorded/printed text for the resolver, parse_route, chat and ModelProfile raise sites is ONLY error_text /
      setup_error_text output (no endpoint, env label, body, name).
(ii)  the RAISE-site detail stays (deliberate, H09): the exact messages below are pinned so a change is noticed.
(iii) CLI preflight: config VALUES are excluded, unknown FIELD KEY NAMES are retained (accepted H04/H08).
(iv)  shared / tool-call error text AS IS: model-supplied names are echoed (repr) and stay.
(v)   shared_jev: the uncaught ValueError from shared_config is pinned as is (no CLI caller found by grep).
Excluded: cli.py build_shared_needle_dataset ValueError (unread). No typed ProviderError API is claimed or tested."""
import io
import json
import urllib.error
from types import SimpleNamespace

import pytest

from sugarcode.cli import main
from sugarcode.llm import agent as A
from sugarcode.llm import providers as P
from sugarcode.llm import shared, tools
from sugarcode.llm.providers import ChatClient, ModelProfile, ProviderError, error_text, setup_error_text

PROFILES = "SUGARCODE_MODEL_PROFILES"
GEN = "ProviderError: model provider error (details withheld)"
NAME = "secret-lab-box"
HOST = "10.9.8.7"
URL = f"http://{HOST}:9000/v1"
BODY = "SECRET-BODY-4f2a"
ENVLABEL = "SECRET_ENV_LABEL"
BASE = {"name": NAME, "base_url": URL, "model": "m", "kind": "self_hosted"}


def env_with(*items, **extra):
    e = {PROFILES: json.dumps(list(items))}
    e.update(extra)
    return e


def no_leak(text):
    for s in (NAME, HOST, BODY, ENVLABEL, "Traceback"):
        assert s not in text


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.delenv(PROFILES, raising=False)
    monkeypatch.delenv("SUGARCODE_MODEL_ROUTE", raising=False)
    monkeypatch.delenv("SUGARCODE_ALLOW_PAID", raising=False)


# ---------------------------------------------------------------- the base type and helpers
def test_provider_error_is_a_plain_runtime_error_with_only_args():
    e = ProviderError("x")
    assert isinstance(e, RuntimeError) and ProviderError.__mro__[1] is RuntimeError
    assert e.args == ("x",) and e.__dict__ == {}


def test_error_text_and_setup_error_text_are_class_plus_fixed_text():
    assert error_text(ProviderError(f"{NAME} {HOST} {BODY}")) == GEN
    assert setup_error_text("ValueError") == "ValueError: provider setup error (details withheld)"


# ---------------------------------------------------------------- resolver / parse_route / ModelProfile raise sites
def _profile(**kw):
    return dict(BASE, **kw)


# (profile item, resolve() name, exact raised text)
RESOLVE_TABLE = [
    (_profile(name="lab", base_url="", base_url_env="LAB_URL_ENV"), "lab",
     "lab: set LAB_URL_ENV to your server's /v1 URL"),
    (_profile(name="lab", model="", model_env="LAB_MODEL_ENV"), "lab",
     "lab: set LAB_MODEL_ENV or pass --model"),
    (_profile(name="lab", api_key_env=ENVLABEL, requires_key=True), "lab",
     f"lab needs {ENVLABEL}."),
    (_profile(name="lab", kind="hosted_paid"), "lab",
     "lab is a paid API. Set SUGARCODE_ALLOW_PAID=1 or pass --allow-paid; the free defaults are 'ollama' and 'inkling'."),
]


@pytest.mark.parametrize("item,name,text", RESOLVE_TABLE)
def test_resolve_raise_site_text_stays_and_caught_text_is_generic(item, name, text):
    env = env_with(item)
    with pytest.raises(ProviderError) as e:
        P.resolve(name, env=env)
    assert type(e.value) is ProviderError and str(e.value) == text          # (ii) raise-site detail stays
    clients, skipped = P.resolve_route(env=env, route=name)                  # (i) caught text is sanitized
    assert clients == [] and skipped == [GEN]
    row = {r["name"]: r for r in P.profile_status(env=env)}[name]
    assert row["ready"] is False and row["reason"] == GEN


def test_resolve_unknown_profile_raise_text_lists_known_names_and_caught_text_is_generic(monkeypatch):
    monkeypatch.setattr(A, "route_modules", lambda q, k=3: [])
    monkeypatch.setattr(A, "tools_for_modules", lambda m, limit=24: [])
    env = env_with(BASE)
    with pytest.raises(ProviderError) as e:
        P.resolve("nope", env=env)
    msg = str(e.value)
    assert msg.startswith("unknown model profile 'nope'; known: [") and f"'{NAME}'" in msg and "'ollama'" in msg
    res = A.ask("q", profile="nope", env=env)
    assert res.skipped == [GEN] and res.error == GEN
    no_leak(json.dumps(res.to_dict()))


def test_parse_route_raise_text_lists_route_and_known_names_and_caught_text_is_generic():
    env = env_with(BASE)
    with pytest.raises(ProviderError) as e:
        P.parse_route(env=env, route="ollama,zz-route")
    msg = str(e.value)
    assert msg.startswith("model route has unknown profiles ['zz-route']; known: [") and f"'{NAME}'" in msg
    assert error_text(e.value) == GEN


def test_parse_route_unknown_name_is_generic_through_the_cli(monkeypatch, capsys):
    monkeypatch.setenv(PROFILES, json.dumps([BASE]))
    monkeypatch.setenv("SUGARCODE_MODEL_ROUTE", "ollama,zz-secret-route")
    rc = main(["models", "check"])
    cap = capsys.readouterr()
    assert rc == 1 and cap.err == "" and json.loads(cap.out) == {"error": GEN}
    assert "zz-secret-route" not in cap.out and NAME not in cap.out


def test_model_profile_constructor_raise_text_echoes_its_name_and_stays():
    with pytest.raises(ProviderError) as e:
        ModelProfile(name=NAME, base_url="u", model="m", kind="cloud")
    assert str(e.value) == f"profile {NAME!r}: kind must be one of {P.KINDS}"
    with pytest.raises(ProviderError) as e2:
        ModelProfile(name=NAME, base_url="u", model="m", kind="local", transport="grpc")
    assert str(e2.value) == f"profile {NAME!r}: transport must be one of {P.TRANSPORTS}"
    assert error_text(e.value) == GEN and error_text(e2.value) == GEN


# ---------------------------------------------------------------- chat() raise sites (231-253), real ChatClient
class _Resp:
    def __init__(self, raw):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.raw


def _client():
    return ChatClient(profile=NAME, base_url=URL, model="m", kind="self_hosted")


def _serve_bytes(monkeypatch, raw):
    monkeypatch.setattr(P.urllib.request, "urlopen", lambda req, timeout=None: _Resp(raw))


def _serve_exc(monkeypatch, exc):
    def fake(req, timeout=None):
        raise exc
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)


def _chat_text(client):
    with pytest.raises(ProviderError) as e:
        client.chat([{"role": "user", "content": "q"}])
    assert type(e.value) is ProviderError
    return str(e.value)


def _ask_skipped(monkeypatch, client):
    monkeypatch.setattr(A, "route_modules", lambda q, k=3: [])
    monkeypatch.setattr(A, "tools_for_modules", lambda m, limit=24: [])
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: ([client], []))
    res = A.ask("q", route="x", env={})
    assert res.answer is None
    no_leak(json.dumps(res.to_dict()))
    return res.skipped


def test_chat_http_error_raise_text_keeps_profile_code_and_body_prefix(monkeypatch):
    _serve_exc(monkeypatch, urllib.error.HTTPError(URL, 503, "x", {}, io.BytesIO((BODY + "A" * 500).encode())))
    assert _chat_text(_client()) == f"{NAME} HTTP 503: " + (BODY + "A" * 500)[:400]
    _serve_exc(monkeypatch, urllib.error.HTTPError(URL, 503, "x", {}, io.BytesIO(BODY.encode())))
    assert _ask_skipped(monkeypatch, _client()) == [GEN]


def test_chat_unreachable_raise_text_keeps_profile_endpoint_and_reason(monkeypatch):
    _serve_exc(monkeypatch, urllib.error.URLError("refused"))
    assert _chat_text(_client()) == f"{NAME} unreachable at {URL}: refused."
    assert _ask_skipped(monkeypatch, _client()) == [GEN]


@pytest.mark.parametrize("exc,reason", [(TimeoutError("slow"), "slow"), (OSError("no route"), "no route")])
def test_chat_timeout_and_oserror_raise_text_keeps_reason(monkeypatch, exc, reason):
    _serve_exc(monkeypatch, exc)
    assert _chat_text(_client()) == f"{NAME} unreachable at {URL}: {reason}."
    assert _ask_skipped(monkeypatch, _client()) == [GEN]


def test_chat_unreadable_body_raise_text_has_profile_and_prefix_and_caught_text_is_generic(monkeypatch):
    _serve_bytes(monkeypatch, b"not json " + BODY.encode())
    assert _chat_text(_client()).startswith(f"{NAME} returned an unreadable response: ")
    assert _ask_skipped(monkeypatch, _client()) == [GEN]


CHAT_SHAPE_CASES = [
    ("[]", f"{NAME} returned a list body, expected an object"),
    (json.dumps({"choices": [], "x": BODY}), f"{NAME} returned no choices: {{'choices': [], 'x': '{BODY}'}}"),
    (json.dumps({"choices": "abc"}), f"{NAME} returned choices of type str, expected a list"),
    (json.dumps({"choices": [1]}), f"{NAME} returned a first choice of type int, expected an object"),
    (json.dumps({"choices": [{"message": 5}]}), f"{NAME} returned a message of type int, expected an object"),
]


@pytest.mark.parametrize("raw,text", CHAT_SHAPE_CASES)
def test_chat_shape_raise_text_stays_and_caught_text_is_generic(monkeypatch, raw, text):
    _serve_bytes(monkeypatch, raw.encode())
    assert _chat_text(_client()) == text
    assert _ask_skipped(monkeypatch, _client()) == [GEN]


# ---------------------------------------------------------------- (iii) CLI preflight: values excluded, key names retained
def _cli(argv, capsys):
    rc = main(argv)
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def test_preflight_unknown_field_key_name_is_kept_and_values_and_name_are_not(monkeypatch, capsys):
    item = dict(BASE, api_key_env=ENVLABEL, zz_field=BODY)
    monkeypatch.setenv(PROFILES, json.dumps([item]))
    rc, out, err = _cli(["models", "list"], capsys)
    assert rc == 1 and err == ""
    assert json.loads(out) == {"error": "SUGARCODE_MODEL_PROFILES item 0: unknown fields ['zz_field']"}
    no_leak(out)


def test_preflight_missing_field_names_are_kept_and_values_and_name_are_not(monkeypatch, capsys):
    item = {k: v for k, v in dict(BASE, api_key_env=ENVLABEL).items() if k != "model"}
    monkeypatch.setenv(PROFILES, json.dumps([item]))
    rc, out, err = _cli(["models", "check"], capsys)
    assert rc == 1 and err == ""
    assert json.loads(out) == {"error": "SUGARCODE_MODEL_PROFILES item 0: missing fields ['model']"}
    no_leak(out)


# ---------------------------------------------------------------- (iv) shared / tool-call text AS IS, model names stay
def test_shared_unknown_tool_text_echoes_the_model_name_repr():
    assert shared._run_shared_call({"name": "ghost_tool", "arguments": {}}, 0, {"a__b"}) == \
        {"error": "model called 'ghost_tool', which was not offered"}


@pytest.mark.parametrize("call,text", [
    (5, "malformed tool call: tool call 3 must be an object, got int"),
    ({"name": 5}, "malformed tool call: tool call 3 name must be a string, got int"),
    ({"name": "a", "id": 7}, "malformed tool call: tool call 3 id must be a string when present, got int")])
def test_shared_malformed_call_text_as_is(call, text):
    assert shared._run_shared_call(call, 3, {"a"}) == {"error": text}


def test_shared_ask_end_to_end_unknown_tool_result_keeps_the_model_name():
    res = SimpleNamespace(provider="p", model="m", text="t", tool_calls=[{"name": "ghost_tool", "arguments": {}}])
    router = SimpleNamespace(run=lambda task: SimpleNamespace(ok=True, attempts=[], result=res))
    out = shared.shared_ask("design a CRISPR guide for TP53", router=router)
    assert out["tool_results"] == [{"error": "model called 'ghost_tool', which was not offered"}]


def test_call_tool_unknown_unexpected_and_missing_text_as_is(monkeypatch):
    fake = tools.Tool(name="m__f", module="m", function="f", description="d",
                      parameters={"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"]})
    monkeypatch.setattr(tools, "catalog", lambda: {"m__f": fake})
    assert tools.call_tool("ghost__x", {}) == {"error": "unknown tool 'ghost__x'"}
    assert tools.call_tool("m__f", {"b": 1}) == {"error": "unexpected arguments ['b']; allowed ['a']"}
    assert tools.call_tool("m__f", {}) == {"error": "missing required arguments ['a']"}


# ---------------------------------------------------------------- (v) shared_jev: uncaught ValueError, characterized only
def test_shared_jev_wrong_product_raises_uncaught_value_error_not_provider_error():
    with pytest.raises(ValueError) as e:
        shared.shared_jev(env={"INSTINCT_PRODUCT": "atlas"})
    assert not isinstance(e.value, ProviderError)
