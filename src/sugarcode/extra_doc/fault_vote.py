"""Fault Tolerance - exact replicated-result voting that masks up to f faulty replicas.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: results, an
exact list of 3..9 entries, one per replica, each an int -1000..1000 (the replica's answer) or None
(the replica crashed and gave nothing); f, an int 0..4 (faults to tolerate) with len(results) at
least 2 * f + 1. The data keys are exactly f, results.

The decision is the answer that at least f + 1 replicas gave, provided exactly one answer reaches
f + 1; with none or with two answers at f + 1 there is no decision (None). The result gives "decision",
"votes" (a list of [answer, count] pairs in ascending answer order, crashed replicas left out),
"crashed" (how many entries are None), "dissenters" (answers given that differ from the decision; all
answers given when there is no decision), and "masked" (a decision exists and at least one replica
crashed or dissented).

Scope: PARTIAL for the Fault Tolerance line. One vote over supplied answers. No real failure
detection, no retry, no recovery, no timing, no real system.

Not claimed: that this makes any system fault tolerant, that f faults of a real kind are covered, that
replica answers are independent, or anything about the real world. Every claim flag in the result is
False.
"""
NOT_CLAIMED = (
    "this makes any system fault tolerant",
    "f faults of a real kind are covered",
    "replica answers are independent",
    "real-world outcome",
)
CLAIMS = {"fault_tolerant_system": False, "real_faults_covered": False, "independent": False, "real_world": False}


class VoteError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"f", "results"}:
        raise VoteError("data keys must be exactly f, results")
    r = data["results"]
    if type(r) is not list or not 3 <= len(r) <= 9:
        raise VoteError("results must be a list of 3 to 9 entries")
    for v in r:
        if v is None:
            continue
        if type(v) is not int:
            raise VoteError("result must be an int or None")
        if not -1000 <= v <= 1000:
            raise VoteError("result must be -1000 to 1000")
    f = data["f"]
    if type(f) is not int:
        raise VoteError("f must be an int")
    if not 0 <= f <= 4:
        raise VoteError("f must be 0 to 4")
    if len(r) < 2 * f + 1:
        raise VoteError("results must hold at least 2*f+1 entries")
    return list(r), f


def fault_vote(data):
    r, f = _validate(data)
    tally = {}
    crashed = 0
    for v in r:
        if v is None:
            crashed += 1
        else:
            tally[v] = tally.get(v, 0) + 1
    votes = [[k, tally[k]] for k in sorted(tally)]
    winners = [k for k in tally if tally[k] >= f + 1]
    decision = winners[0] if len(winners) == 1 else None
    dissent = [v for v in r if v is not None and v != decision]
    return {
        "status": "completed",
        "decision": decision,
        "votes": votes,
        "crashed": crashed,
        "dissenters": dissent,
        "masked": decision is not None and (crashed > 0 or len(dissent) > 0),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
