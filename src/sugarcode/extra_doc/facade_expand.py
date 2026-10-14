"""Row 662 Facade Pattern (PARTIAL): expanding facade calls into the subsystem calls they stand for.

subsystem is a list of 1..32 distinct operation names. facade is a dict of 1..16 facade operation names, each
mapped to a list of 1..8 subsystem names (repeats allowed, every one must be in subsystem). calls is a list of
1..100 facade names. expand returns the subsystem calls in order, how many subsystem calls were made, how many
facade calls, and the difference. Names are 1..30 characters of a-z, 0-9 and underscore starting with a letter
(ASCII only). These ranges are this module's own choices. It expands a supplied table. It builds no objects,
runs no code and says nothing about whether a facade is a good design."""
import re

MAX_SUB, MAX_FACADE, MAX_STEPS, MAX_CALLS = 32, 16, 8, 100
NOT_CLAIMED = ("an implementation of the pattern", "design quality", "runtime behaviour",
               "performance gain", "interface stability")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def _name(label, v):
    if type(v) is not str or _NAME.fullmatch(v) is None:
        raise ValueError(f"{label}: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")
    return v


def expand(subsystem, facade, calls):
    if type(subsystem) is not list or not 1 <= len(subsystem) <= MAX_SUB:
        raise ValueError(f"subsystem: list of 1 to {MAX_SUB} required")
    for i, n in enumerate(subsystem):
        _name(f"subsystem[{i}]", n)
    if len(set(subsystem)) != len(subsystem):
        raise ValueError("subsystem: names must be distinct")
    if type(facade) is not dict or not 1 <= len(facade) <= MAX_FACADE:
        raise ValueError(f"facade: dict of 1 to {MAX_FACADE} required")
    for k, steps in facade.items():
        _name("facade key", k)
        if type(steps) is not list or not 1 <= len(steps) <= MAX_STEPS:
            raise ValueError(f"facade[{k}]: list of 1 to {MAX_STEPS} required")
        for i, s in enumerate(steps):
            _name(f"facade[{k}][{i}]", s)
            if s not in subsystem:
                raise ValueError(f"facade[{k}][{i}]: not a subsystem name")
    if type(calls) is not list or not 1 <= len(calls) <= MAX_CALLS:
        raise ValueError(f"calls: list of 1 to {MAX_CALLS} required")
    for i, c in enumerate(calls):
        _name(f"calls[{i}]", c)
        if c not in facade:
            raise ValueError(f"calls[{i}]: not a facade name")
    sequence = [s for c in calls for s in facade[c]]
    return {"subsystem_calls": sequence, "subsystem_call_count": len(sequence), "facade_call_count": len(calls),
            "calls_saved": len(sequence) - len(calls),
            "facade_validated": False, "not_claimed": NOT_CLAIMED}
