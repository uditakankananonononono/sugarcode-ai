"""AUTHORED, NOT RUN. H07: ChatClient.health() must return a typed error RESULT (never raise) when the
/models body is valid JSON of the wrong shape: a non-object body, a non-list "data", or a non-object member.
Contrast with chat(), which still RAISES ProviderError for a wrong-shaped body (H01).
urlopen is replaced by a stub; no network. Written before the code change."""
import json
import urllib.error

import pytest

from sugarcode.llm import providers as P
from sugarcode.llm.providers import ChatClient, ProviderError

PREFIX = "malformed /models response"


class _Resp:
    def __init__(self, raw):
        self._raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._raw


def _client(url="http://stub.test/v1"):
    return ChatClient(profile="p1", base_url=url, model="m", kind="self_hosted")


@pytest.fixture
def serve(monkeypatch):
    calls = []

    def serve(body):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()

        def fake(req, timeout=None):
            calls.append(req.full_url)
            return _Resp(raw)
        monkeypatch.setattr(P.urllib.request, "urlopen", fake)
        return calls
    return serve


# ---- the new behavior: typed error result, never an exception ----
@pytest.mark.parametrize("body", [[], [1], [{"id": "m"}], "x", 3, 1.5, None, True])
def test_non_object_body_is_error_result(serve, body):
    serve(body)
    out = _client().health()
    assert out["ok"] is False and out["profile"] == "p1"
    assert out["error"].startswith(PREFIX)
    assert set(out) == {"profile", "ok", "error"}


@pytest.mark.parametrize("data", [None, {}, "x", 5, True, {"id": "m"}])
def test_non_list_data_is_error_result(serve, data):
    serve({"data": data})
    out = _client().health()
    assert out["ok"] is False and out["error"].startswith(PREFIX)
    assert set(out) == {"profile", "ok", "error"}


@pytest.mark.parametrize("member", [None, 1, "x", ["id"], True, 1.5])
def test_non_object_member_is_error_result(serve, member):
    serve({"data": [{"id": "m"}, member]})
    out = _client().health()
    assert out["ok"] is False and out["error"].startswith(PREFIX)
    assert set(out) == {"profile", "ok", "error"}


def test_first_member_non_object_is_error_result(serve):
    serve({"data": ["x", {"id": "m"}]})
    assert _client().health()["ok"] is False


def test_error_result_does_not_echo_the_body(serve):
    serve({"data": [{"id": "m"}, "SECRET-BODY-VALUE"]})
    out = _client().health()
    assert "SECRET-BODY-VALUE" not in json.dumps(out)
    serve(["SECRET-BODY-VALUE"])
    assert "SECRET-BODY-VALUE" not in json.dumps(_client().health())


def test_health_never_raises_for_any_of_these_shapes(serve):
    for body in ([], "x", None, {"data": None}, {"data": [None]}, {"data": [[]]}, {"data": 7}):
        serve(body)
        assert isinstance(_client().health(), dict)


def test_huggingface_base_url_malformed_models_skips_the_token_probe(serve):
    calls = serve([])
    out = _client("https://router.huggingface.co/v1").health()
    assert out["ok"] is False and out["error"].startswith(PREFIX)
    assert "token_valid" not in out
    assert len(calls) == 1 and calls[0].endswith("/models")


# ---- chat() contrast: the same wrong-shaped body still RAISES ProviderError there ----
def test_chat_still_raises_provider_error_for_a_list_body(serve):
    serve([])
    with pytest.raises(ProviderError) as e:
        _client().chat([{"role": "user", "content": "q"}])
    assert "list body" in str(e.value)
    serve([])
    assert isinstance(_client().health(), dict)   # health on the same body returns, chat raised


# ---- unchanged behavior ----
def test_well_formed_models_unchanged(serve):
    serve({"data": [{"id": "m"}, {"id": "n"}]})
    assert _client().health() == {"profile": "p1", "ok": True, "model": "m",
                                  "model_listed": True, "models_available": 2}


def test_model_not_listed_unchanged(serve):
    serve({"data": [{"id": "other"}]})
    out = _client().health()
    assert out["ok"] is True and out["model_listed"] is False and out["models_available"] == 1


def test_missing_data_key_still_ok_with_zero_models(serve):
    serve({})
    assert _client().health() == {"profile": "p1", "ok": True, "model": "m",
                                  "model_listed": False, "models_available": 0}


def test_empty_data_list_still_ok(serve):
    serve({"data": []})
    assert _client().health()["models_available"] == 0


def test_invalid_json_body_is_still_an_error_result(serve):
    serve(b"not json")
    out = _client().health()
    assert out["ok"] is False and out["profile"] == "p1" and set(out) == {"profile", "ok", "error"}


def test_http_error_unchanged(monkeypatch):
    def fake(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "x", {}, None)
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    assert _client().health() == {"profile": "p1", "ok": False, "error": "HTTP 503"}


def test_unreachable_unchanged(monkeypatch):
    def fake(req, timeout=None):
        raise urllib.error.URLError("refused")
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    out = _client().health()
    assert out["ok"] is False and out["error"] == "unreachable: URLError" and set(out) == {"profile", "ok", "error"}  # H09: class only, reason text withheld
