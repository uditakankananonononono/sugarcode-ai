import itertools
import re
import pytest
from sugarcode.extra_doc import name_lint as nl

L = nl.lint
NC = ("a real linter", "language rules", "correctness of any code",
      "scoping or imports", "runtime behaviour")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"
AC = "'def' or 'use' required"


class Li(list):
    pass


class Tu(tuple):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        L(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def oracle(events):                         # independent: look backward and forward from every event
    out = []
    for i, (a, n) in enumerate(events):
        if a == "use" and not any(x == ("def", n) for x in events[:i]):
            out.append((i, "use_before_def"))
        if a == "def":
            if any(x == ("def", n) for x in events[:i]):
                out.append((i, "redefined"))
            nxt = next((j for j in range(i + 1, len(events)) if events[j] == ("def", n)), len(events))
            if not any(events[j] == ("use", n) for j in range(i + 1, nxt)):
                out.append((i, "unused"))
    return sorted(out)


def test_constants():
    assert nl.MAX_EVENTS == 100 and nl.ACTIONS == ("def", "use") and nl.NOT_CLAIMED == NC


def test_hand_literals():
    ev = [("use", "a"), ("def", "a"), ("use", "a"), ("def", "b"), ("def", "b"), ("use", "b"), ("def", "c")]
    assert L(ev)["issues"] == [(0, "use_before_def"), (3, "unused"), (4, "redefined"), (6, "unused")]
    assert L(ev)["clean"] is False
    assert L([("def", "a"), ("use", "a")])["issues"] == [] and L([("def", "a"), ("use", "a")])["clean"] is True
    assert L([("def", "a")])["issues"] == [(0, "unused")]
    assert L([("use", "a")])["issues"] == [(0, "use_before_def")]
    assert L([("def", "a"), ("use", "a"), ("def", "a")])["issues"] == [(2, "redefined"), (2, "unused")]
    assert L([("def", "a"), ("def", "a"), ("use", "a")])["issues"] == [(0, "unused"), (1, "redefined")]
    assert L([("def", "a"), ("use", "a"), ("use", "a")])["issues"] == []


def test_shape_and_untouched():
    ev = [("def", "a")]
    r = L(ev)
    assert ev == [("def", "a")]
    assert r == {"issues": [(0, "unused")], "clean": False, "lint_validated": False, "not_claimed": NC}


def test_exhaustive_against_oracle():
    atoms = [("def", "a"), ("use", "a"), ("def", "b"), ("use", "b")]
    for n in range(1, 7):
        for ev in itertools.product(atoms, repeat=n):
            assert L(list(ev))["issues"] == oracle(list(ev)), ev


def test_caps_accepted():
    assert L([("use", "a")] * 100)["issues"][-1] == (99, "use_before_def")
    assert L([("def", "a" * 30), ("use", "a" * 30)])["clean"] is True


BAD = [None, 5, "", "A", "1a", "_a", "a-b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD)
def test_name_refusals(bad):
    refuse(f"events[0] name: {NM}", [("def", bad)])
    refuse(f"events[1] name: {NM}", [("def", "a"), ("use", bad)])


@pytest.mark.parametrize("bad", [None, 1, "", "Def", "DEF", "def ", "use\n", "d\u0435f", St("def"), b"def", "define"])
def test_action_refusals(bad):
    refuse(f"events[0] action: {AC}", [(bad, "a")])
    refuse(f"events[1] action: {AC}", [("def", "a"), (bad, "a")])


@pytest.mark.parametrize("bad", [[], ("def",), ("def", "a", 1), Tu(("def", "a")), ["def", "a"], None, "ab"])
def test_event_shape(bad):
    refuse("events[0]: (action, name) tuple required", [bad])
    refuse("events[1]: (action, name) tuple required", [("def", "a"), bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([("def", "a")]), [], [("def", "a")] * 101])
def test_events_shape(bad):
    refuse("events: list of 1 to 100 required", bad)


def test_check_order():
    refuse("events: list of 1 to 100 required", None)
    refuse("events[0]: (action, name) tuple required", [None, ("bad", "A")])
    refuse(f"events[0] action: {AC}", [("bad", "A")])
