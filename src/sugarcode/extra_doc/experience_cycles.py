"""Experiential Learning - exact count of complete experience cycles in a caller-recorded stage log.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
log, 1..16 stage names in the order they happened, each one of experience, reflect,
conceptualize, experiment. The data key is exactly log.

The cycle is experience, reflect, conceptualize, experiment, in that order. The log is read
left to right looking for the next stage the cycle needs; a stage that is not the one needed
is set aside, and after experiment the cycle starts again. The result gives "cycles", the
number of complete cycles; "next_needed", the stage the reading was waiting for at the end
of the log; "set_aside", the number of entries that were not the stage needed when read; and
"stages_seen", a dict of stage -> count for each stage present (keys sorted).

Scope: PARTIAL for the Experiential Learning line. One fixed stage order applied to a log the
caller wrote. It does not judge anyone's experience or say what was learned.

Not claimed: that the log is a real record, that a complete cycle means learning, that the
four-stage order is the only valid one, or anything about the real world. Every claim flag in
the result is False.
"""
STAGES = ("experience", "reflect", "conceptualize", "experiment")
NOT_CLAIMED = (
    "the log is a real record",
    "a complete cycle means learning",
    "the four-stage order is the only valid one",
    "real-world outcome",
)
CLAIMS = {"real_record": False, "cycle_is_learning": False, "only_valid_order": False, "real_world": False}


class CycleError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"log"}:
        raise CycleError("data keys must be exactly log")
    v = data["log"]
    if type(v) is not list or not 1 <= len(v) <= 16:
        raise CycleError("log must be a list of 1 to 16 stages")
    for s in v:
        if type(s) is not str or s not in STAGES:
            raise CycleError("stage must be one of experience, reflect, conceptualize, experiment")
    return list(v)


def experience_cycles(data):
    log = _validate(data)
    need = 0
    cycles = 0
    aside = 0
    for s in log:
        if s == STAGES[need]:
            need += 1
            if need == 4:
                cycles += 1
                need = 0
        else:
            aside += 1
    seen = {}
    for s in log:
        seen[s] = seen.get(s, 0) + 1
    return {
        "status": "completed",
        "cycles": cycles,
        "next_needed": STAGES[need],
        "set_aside": aside,
        "stages_seen": {k: seen[k] for k in sorted(seen)},
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
