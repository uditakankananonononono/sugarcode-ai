"""AUTHORED, NOT RUN. H03: characterization, do not unify.

Pins TODAY's behaviour of two slug rules that differ on purpose-or-accident:
- events.GapEventStore._path: keep chars that are isalnum() or in "-_"; refuse if the filtered text != slug or is empty (plain ValueError).
- proposal_preflight_r01._identity: exact str only; remove "-" and "_" then require str.isalnum() (ProposalPreflightError, a ValueError subclass).
Where they disagree (only-punctuation slugs, str subclasses, non-str inputs) the test says so. A failing test here means a rule changed;
that is a decision, not a cleanup. No source edits accompany this file.
"""
import pytest

from sugarcode.self_improve.events import GapEvent, GapEventStore
from sugarcode.self_improve.proposal_preflight_r01 import ProposalPreflightError, _identity


def events_accepts(tmp_path, slug):
    try:
        GapEventStore(tmp_path)._path(slug)
        return True
    except ValueError:
        return False


def preflight_accepts(slug):
    try:
        _identity(slug, "module_slug")
        return True
    except ProposalPreflightError:
        return False


# slug, events accepts, preflight accepts
CASES = [
    # both accept
    ("abc123", True, True), ("a-b_c", True, True), ("módulo", True, True), ("中文", True, True),
    ("Démo_1", True, True), ("²", True, True), ("٣", True, True), ("a-", True, True), ("_a", True, True),
    # DIVERGENCE: events accepts, preflight refuses (nothing alphanumeric once - and _ are removed)
    ("-", True, False), ("--", True, False), ("---", True, False), ("_", True, False), ("__", True, False),
    ("-_", True, False), ("_-_-", True, False),
    # both refuse
    ("", False, False), ("a b", False, False), ("../escape", False, False), ("a.b", False, False),
    ("a/b", False, False), ("a\\b", False, False), ("a\n", False, False), (" a", False, False),
    ("a\u2028b", False, False), ("a\x00", False, False), ("a\U0001f642", False, False),
]


@pytest.mark.parametrize("slug,events,preflight", CASES)
def test_rules_as_they_are_today(tmp_path, slug, events, preflight):
    assert events_accepts(tmp_path, slug) is events
    assert preflight_accepts(slug) is preflight


def test_divergence_set_is_exactly_the_punctuation_only_slugs():
    diverging = [slug for slug, e, p in CASES if e != p]
    assert diverging == ["-", "--", "---", "_", "__", "-_", "_-_-"]
    assert all(slug.replace("-", "").replace("_", "") == "" for slug in diverging)


def test_events_accepted_path_is_the_slug_plus_suffix(tmp_path):
    store = GapEventStore(tmp_path)
    assert store._path("---") == tmp_path / "---.gap-events.jsonl"
    assert store._path("módulo") == tmp_path / "módulo.gap-events.jsonl"


def test_exception_types_differ_in_class_but_share_valueerror(tmp_path):
    with pytest.raises(ValueError) as e1:
        GapEventStore(tmp_path)._path("../escape")
    assert type(e1.value) is ValueError and "unsafe module slug" in str(e1.value)
    with pytest.raises(ValueError) as e2:
        _identity("../escape", "module_slug")
    assert type(e2.value) is ProposalPreflightError and "unsafe module_slug" in str(e2.value)
    assert not isinstance(e1.value, ProposalPreflightError)


def test_empty_slug_refused_by_both_with_their_own_types(tmp_path):
    with pytest.raises(ValueError) as e1:
        GapEventStore(tmp_path)._path("")
    assert type(e1.value) is ValueError
    with pytest.raises(ProposalPreflightError):
        _identity("", "module_slug")


def test_str_subclass_events_accepts_preflight_refuses(tmp_path):
    class S(str):
        pass
    assert events_accepts(tmp_path, S("abc")) is True
    with pytest.raises(ProposalPreflightError) as e:
        _identity(S("abc"), "module_slug")
    assert "exact string" in str(e.value)


@pytest.mark.parametrize("bad", [None, 5])
def test_non_str_events_type_error_preflight_typed_refusal(tmp_path, bad):
    with pytest.raises(TypeError):
        GapEventStore(tmp_path)._path(bad)
    with pytest.raises(ProposalPreflightError) as e:
        _identity(bad, "module_slug")
    assert "exact string" in str(e.value)


def test_gap_event_itself_does_not_validate_the_slug_shape():
    GapEvent(module_slug="../escape", signature="x")  # only the store refuses it
    GapEvent(module_slug="", signature="x")
    with pytest.raises(Exception):
        GapEvent(module_slug=5, signature="x")


def test_append_public_surface_follows_the_events_rule(tmp_path):
    store = GapEventStore(tmp_path)
    store.append(GapEvent(module_slug="---", signature="x"))
    assert (tmp_path / "---.gap-events.jsonl").exists()
    with pytest.raises(ValueError):
        store.append(GapEvent(module_slug="../escape", signature="x"))
    assert not any(p.name.startswith("..") for p in tmp_path.iterdir())
