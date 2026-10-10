"""AUTHORED, NOT RUN. H01: ChatClient.chat must turn a wrong-shaped (but valid JSON) response body into a typed
ProviderError instead of AttributeError/KeyError, so agent.ask can fall back to the next profile.
urlopen is replaced by a stub; no network."""
import json

import pytest

from sugarcode.llm import agent as A
from sugarcode.llm import providers as P
from sugarcode.llm.providers import ChatClient, ProviderError


class _Resp:
    def __init__(self, raw):
        self._raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._raw


def _client(name="p1", url="http://stub.test/v1"):
    return ChatClient(profile=name, base_url=url, model="m", kind="cloud")


@pytest.fixture
def serve(monkeypatch):
    """serve(body) makes every urlopen return json.dumps(body); serve_by_url({prefix: body}) routes by URL."""
    def _raw(body):
        return body if isinstance(body, bytes) else json.dumps(body).encode()

    def serve(body):
        monkeypatch.setattr(P.urllib.request, "urlopen", lambda req, timeout=None: _Resp(_raw(body)))

    def serve_by_url(table):
        def fake(req, timeout=None):
            for prefix, body in table.items():
                if req.full_url.startswith(prefix):
                    return _Resp(_raw(body))
            raise AssertionError("unexpected url " + req.full_url)
        monkeypatch.setattr(P.urllib.request, "urlopen", fake)

    serve.by_url = serve_by_url
    return serve


def refused(serve, body, needle):
    serve(body)
    with pytest.raises(ProviderError) as e:
        _client().chat([{"role": "user", "content": "q"}])
    assert needle in str(e.value)
    assert type(e.value) is ProviderError or isinstance(e.value, ProviderError)


# ---- well-formed and compatible shapes still work ----
def test_valid_message_returned_unchanged(serve):
    msg = {"role": "assistant", "content": "hi", "tool_calls": [{"id": "c1"}]}
    serve({"choices": [{"message": msg}]})
    assert _client().chat([]) == msg


@pytest.mark.parametrize("first", [{}, {"message": None}, {"finish_reason": "stop"}, {"message": {}}])
def test_missing_or_none_message_is_empty_dict(serve, first):
    serve({"choices": [first]})
    assert _client().chat([]) == {}


def test_extra_keys_ignored(serve):
    serve({"id": "x", "choices": [{"index": 0, "message": {"content": "a"}, "finish_reason": "stop"}, {"x": 1}], "usage": {}})
    assert _client().chat([]) == {"content": "a"}


# ---- body must be an object ----
@pytest.mark.parametrize("body", [[], [1], ["choices"], "x", "", 3, 0, True, False, None, 1.5])
def test_non_object_body_refused(serve, body):
    refused(serve, body, "body")


# ---- choices ----
@pytest.mark.parametrize("choices", [{"a": 1}, "abc", 5, True, 1.5])
def test_truthy_non_list_choices_refused(serve, choices):
    refused(serve, {"choices": choices}, "choices")


@pytest.mark.parametrize("body", [{"choices": []}, {"choices": None}, {}, {"choices": {}}, {"choices": ""},
                                  {"choices": 0}, {"choices": False}])
def test_missing_or_falsey_choices_keep_the_no_choices_error(serve, body):
    refused(serve, body, "no choices")


# ---- first choice ----
@pytest.mark.parametrize("first", [1, "x", None, [], ["a"], 0, True, 1.5])
def test_non_dict_first_choice_refused(serve, first):
    refused(serve, {"choices": [first]}, "first choice")


def test_only_the_first_choice_is_checked(serve):
    serve({"choices": [{"message": {"content": "ok"}}, "garbage", 5]})
    assert _client().chat([]) == {"content": "ok"}


# ---- message: present non-dict is refused, falsey included; absent/None is not ----
@pytest.mark.parametrize("message", ["hi", "", 0, 5, False, True, [], ["a"], 1.5])
def test_present_non_dict_message_refused_including_falsey(serve, message):
    refused(serve, {"choices": [{"message": message}]}, "message")


# ---- unchanged behaviour from G03 and before ----
def test_invalid_json_still_unreadable(serve):
    refused(serve, b"{not json", "unreadable")


# ---- ask() falls back instead of raising ----
@pytest.mark.parametrize("bad_body", [[], {"choices": "x"}, {"choices": [5]}, {"choices": [{"message": ""}]}])
def test_ask_falls_back_to_next_profile_and_records_the_shape_error(monkeypatch, serve, bad_body):
    bad, good = _client("bad", "http://bad.test/v1"), _client("good", "http://good.test/v1")
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: ([bad, good], []))
    serve.by_url({"http://bad.test": bad_body,
                  "http://good.test": {"choices": [{"message": {"content": "answer"}}]}})
    res = A.ask("codon optimize a protein for E. coli expression", route="bad,good", env={})
    assert res.profile == "good" and res.answer == "answer"
    assert any(s == "ProviderError: model provider error (details withheld)" for s in res.skipped)  # H09 generic, no profile prefix
    assert not any("bad" in s for s in res.skipped)


def test_ask_with_only_malformed_profile_reports_error_not_exception(monkeypatch, serve):
    bad = _client("bad", "http://bad.test/v1")
    monkeypatch.setattr(A, "resolve_route", lambda env=None, route=None, allow_paid=None: ([bad], []))
    serve.by_url({"http://bad.test": ["nope"]})
    res = A.ask("codon optimize a protein for E. coli expression", route="bad", env={})
    assert res.answer is None and res.error and any(s == "ProviderError: model provider error (details withheld)" for s in res.skipped)  # H09
