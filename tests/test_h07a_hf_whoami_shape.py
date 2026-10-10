"""AUTHORED, NOT RUN. H07a: on a huggingface.co base_url, health() must return a typed error RESULT
{"profile","ok": False,"error": "malformed whoami response: ..."} (model fields dropped, never an exception)
when the whoami body is valid JSON but not an object, or its "name" is not a non-empty str.
401/403/other-HTTP/unreachable whoami results are unchanged strings. Token TRUE iff whoami is a dict with a
non-empty str name (whitespace-only is non-empty; no strip). urlopen is stubbed; no network.
Written before the code change."""
import json
import urllib.error

import pytest

from sugarcode.llm import providers as P
from sugarcode.llm.providers import ChatClient

HF = "https://router.huggingface.co/v1"
TOKEN = "hf_PLANTED_TOKEN_9f3a"
BODY_SECRET = "BODY-SECRET-VALUE"
PREFIX = "malformed whoami response"
MODELS = {"data": [{"id": "m"}]}


class _Resp:
    def __init__(self, raw):
        self._raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._raw


def _client():
    return ChatClient(profile="hf1", base_url=HF, model="m", kind="hosted_free", api_key=TOKEN)


@pytest.fixture
def hf(monkeypatch):
    """hf(whoami=<body or exception>) stubs /models (well-formed) and whoami; returns the urlopen call log."""
    calls = []

    def hf(whoami):
        def fake(req, timeout=None):
            calls.append(req.full_url)
            if req.full_url.endswith("/models"):
                return _Resp(json.dumps(MODELS).encode())
            assert req.full_url == "https://huggingface.co/api/whoami-v2"
            if isinstance(whoami, BaseException):
                raise whoami
            return _Resp(whoami if isinstance(whoami, bytes) else json.dumps(whoami).encode())
        monkeypatch.setattr(P.urllib.request, "urlopen", fake)
        return calls
    return hf


def _assert_malformed(out):
    assert set(out) == {"profile", "ok", "error"}
    assert out["profile"] == "hf1" and out["ok"] is False
    assert out["error"].startswith(PREFIX)
    assert "token_valid" not in out and "model" not in out and "models_available" not in out


def _no_secrets(out):
    text = json.dumps(out)
    assert TOKEN not in text and BODY_SECRET not in text


# ---- non-object whoami bodies ----
@pytest.mark.parametrize("body", [[], [BODY_SECRET], BODY_SECRET, 5, 1.5, None, True, False])
def test_non_object_whoami_is_malformed_result(hf, body):
    hf(body)
    out = _client().health()
    _assert_malformed(out)
    _no_secrets(out)


# ---- dict whoami with a name that is absent or not a non-empty str ----
@pytest.mark.parametrize("body", [
    {}, {"id": "u1"}, {"name": None}, {"name": ""}, {"name": 0}, {"name": False},
    {"name": 5}, {"name": 1.5}, {"name": True}, {"name": [BODY_SECRET]}, {"name": {"k": BODY_SECRET}},
    {"name": []}, {"name": {}}])
def test_dict_without_nonempty_str_name_is_malformed_result(hf, body):
    hf(body)
    out = _client().health()
    _assert_malformed(out)
    _no_secrets(out)


def test_malformed_whoami_does_not_raise_for_any_shape(hf):
    for body in ([], "x", None, {}, {"name": 5}, {"name": [1]}, True):
        hf(body)
        assert isinstance(_client().health(), dict)


# ---- valid token: True ----
def test_valid_name_is_token_true_with_model_fields(hf):
    hf({"name": "alice", "id": "u1"})
    assert _client().health() == {"profile": "hf1", "ok": True, "model": "m", "model_listed": True,
                                  "models_available": 1, "token_valid": True}


@pytest.mark.parametrize("name", [" ", "  \t", "a", "\u00e9"])
def test_any_nonempty_str_name_is_valid_no_strip(hf, name):
    hf({"name": name})
    out = _client().health()
    assert out["token_valid"] is True and out["ok"] is True


# ---- behavior change receipt: a truthy NON-str name used to count as True, now malformed ----
@pytest.mark.parametrize("name", [5, [1], {"a": 1}, True])
def test_truthy_non_str_name_is_no_longer_true(hf, name):
    hf({"name": name})
    out = _client().health()
    assert out.get("token_valid") is not True
    _assert_malformed(out)


# ---- existing whoami outcomes are byte-unchanged and separate from malformed ----
@pytest.mark.parametrize("code", [401, 403])
def test_401_403_stay_token_false_with_model_fields(hf, code):
    hf(urllib.error.HTTPError("https://huggingface.co/api/whoami-v2", code, "x", {}, None))
    out = _client().health()
    assert out == {"profile": "hf1", "ok": False, "model": "m", "model_listed": True,
                   "models_available": 1, "token_valid": False}
    _no_secrets(out)


def test_other_http_code_stays_a_string(hf):
    hf(urllib.error.HTTPError("https://huggingface.co/api/whoami-v2", 500, "x", {}, None))
    out = _client().health()
    assert out["token_valid"] == "HTTP 500" and out["ok"] is False and "error" not in out


def test_unreachable_stays_a_string(hf):
    hf(urllib.error.URLError("refused"))
    out = _client().health()
    assert out["token_valid"] == "unreachable: URLError" and out["ok"] is False and "error" not in out  # H09: class only
    hf(TimeoutError("slow"))
    assert _client().health()["token_valid"] == "unreachable: TimeoutError"  # H09: class only


def test_invalid_json_whoami_stays_an_unreachable_string(hf):
    hf(b"not json")
    out = _client().health()
    assert out["token_valid"].startswith("unreachable: ") and out["ok"] is False and "error" not in out
    _no_secrets(out)


def test_exactly_two_urlopens_on_the_hf_path(hf):
    calls = hf({"name": "alice"})
    _client().health()
    assert calls == [HF + "/models", "https://huggingface.co/api/whoami-v2"]
    calls.clear()
    hf([])
    _client().health()
    assert len(calls) == 2


def test_non_hf_base_url_makes_no_whoami_call(monkeypatch):
    calls = []

    def fake(req, timeout=None):
        calls.append(req.full_url)
        return _Resp(json.dumps(MODELS).encode())
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    out = ChatClient(profile="p", base_url="http://stub.test/v1", model="m", kind="self_hosted").health()
    assert out["ok"] is True and "token_valid" not in out and len(calls) == 1


def test_malformed_models_still_returns_before_whoami(monkeypatch):
    calls = []

    def fake(req, timeout=None):
        calls.append(req.full_url)
        return _Resp(b"[]")
    monkeypatch.setattr(P.urllib.request, "urlopen", fake)
    out = _client().health()
    assert out["ok"] is False and out["error"].startswith("malformed /models response") and len(calls) == 1
