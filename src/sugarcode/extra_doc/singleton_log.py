"""Row 666 Singleton Pattern (bounded implementation): replaying a creation log to find where "only one instance" breaks.

events is a list of 1..100 (key, action) tuples. key is 1..30 characters of a-z, 0-9 and underscore starting
with a letter (ASCII only); action is exactly "create" or "get". The first create of a key makes its instance. A
second create of the same key is a duplicate_create violation. A get of a key that was never created is a
get_before_create violation. Violations are listed as (event_index, kind) in event order, and the keys are listed
in order of first creation. These ranges are this module's own choices. It replays supplied events. It creates
no objects, guards no threads and says nothing about whether a singleton is a good design."""
import re

MAX_EVENTS = 100
ACTIONS = ("create", "get")
NOT_CLAIMED = ("an implementation of the pattern", "thread safety", "object creation",
               "design quality", "runtime behaviour")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def replay(events):
    if type(events) is not list or not 1 <= len(events) <= MAX_EVENTS:
        raise ValueError(f"events: list of 1 to {MAX_EVENTS} required")
    for i, ev in enumerate(events):
        if type(ev) is not tuple or len(ev) != 2:
            raise ValueError(f"events[{i}]: (key, action) tuple required")
        if type(ev[0]) is not str or _NAME.fullmatch(ev[0]) is None:
            raise ValueError(f"events[{i}] key: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")
        if type(ev[1]) is not str or ev[1] not in ACTIONS:
            raise ValueError(f"events[{i}] action: 'create' or 'get' required")
    created, violations = [], []
    for i, (key, action) in enumerate(events):
        if action == "create":
            if key in created:
                violations.append((i, "duplicate_create"))
            else:
                created.append(key)
        elif key not in created:
            violations.append((i, "get_before_create"))
    return {"created_keys": created, "violations": violations, "single_instance_holds": not violations,
            "singleton_validated": False, "not_claimed": NOT_CLAIMED}
