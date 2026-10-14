"""Row 709 Linting : three name-use checks on a supplied sequence of define/use events.

events is a list of 1..100 (action, name) tuples, action exactly "def" or "use", name 1..30 characters of a-z,
0-9 and underscore starting with a letter (ASCII only). Issues are (event_index, kind) sorted by index then
kind:
  use_before_def   a "use" of a name with no earlier "def";
  redefined        a "def" of a name that already has a "def" (the index is the later def);
  unused           a "def" with no "use" of that name after it, reported at the def's index (a def that is later
                   redefined is judged on its own: only uses before the next def of that name count).
These three rules and the ranges are this module's own choices, not the rules of any real linter. It checks a
supplied list. It reads no source code and says nothing about whether code is correct or good."""
import re

MAX_EVENTS = 100
ACTIONS = ("def", "use")
NOT_CLAIMED = ("a real linter", "language rules", "correctness of any code",
               "scoping or imports", "runtime behaviour")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def lint(events):
    if type(events) is not list or not 1 <= len(events) <= MAX_EVENTS:
        raise ValueError(f"events: list of 1 to {MAX_EVENTS} required")
    for i, ev in enumerate(events):
        if type(ev) is not tuple or len(ev) != 2:
            raise ValueError(f"events[{i}]: (action, name) tuple required")
        if type(ev[0]) is not str or ev[0] not in ACTIONS:
            raise ValueError(f"events[{i}] action: 'def' or 'use' required")
        if type(ev[1]) is not str or _NAME.fullmatch(ev[1]) is None:
            raise ValueError(f"events[{i}] name: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")
    issues, open_def = [], {}
    for i, (action, name) in enumerate(events):
        if action == "use":
            if name in open_def:
                open_def[name] = None
            else:
                issues.append((i, "use_before_def"))
        else:
            if name in open_def:
                issues.append((i, "redefined"))
                if open_def[name] is not None:
                    issues.append((open_def[name], "unused"))
            open_def[name] = i
    issues.extend((j, "unused") for j in open_def.values() if j is not None)
    return {"issues": sorted(issues), "clean": not issues,
            "lint_validated": False, "not_claimed": NOT_CLAIMED}
