"""Consensus Algorithm - exact majority-quorum commit point over a replicated log.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: nodes, an int
3..7 (cluster size); acks, an exact list of 1..10 rows, one per log entry in log order, each an exact
list of different ints 0..nodes-1 (the nodes that stored that entry; may be empty). The data keys are
exactly acks, nodes.

The quorum is nodes // 2 + 1. An entry is replicated when its row holds at least quorum nodes. The
commit index is the length of the longest prefix of entries that are all replicated (entries commit in
order, so one short entry holds back everything after it). The result gives "quorum", "counts" (the
row lengths), "commit_index", and "held_back" (entries after the commit index that are replicated
but cannot commit yet).

Scope: PARTIAL for the Consensus Algorithm line. A counting rule on supplied acknowledgements. No
leader election, no terms, no messages, no failure, no network, no real consensus.

Not claimed: that this reaches consensus, that a commit index means the nodes agree on state, that
the rule is safe under real failures, or anything about the real world. Every claim flag in the result
is False.
"""
NOT_CLAIMED = (
    "this reaches consensus",
    "a commit index means the nodes agree on state",
    "the rule is safe under real failures",
    "real-world outcome",
)
CLAIMS = {"consensus": False, "agree_on_state": False, "safe_under_failure": False, "real_world": False}


class QuorumError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"acks", "nodes"}:
        raise QuorumError("data keys must be exactly acks, nodes")
    n = data["nodes"]
    if type(n) is not int:
        raise QuorumError("nodes must be an int")
    if not 3 <= n <= 7:
        raise QuorumError("nodes must be 3 to 7")
    acks = data["acks"]
    if type(acks) is not list or not 1 <= len(acks) <= 10:
        raise QuorumError("acks must be a list of 1 to 10 entries")
    for row in acks:
        if type(row) is not list or len(row) > n:
            raise QuorumError("each entry must be a list of at most nodes node ids")
    for row in acks:
        for v in row:
            if type(v) is not int:
                raise QuorumError("node id must be an int")
            if not 0 <= v < n:
                raise QuorumError("node id must be 0 to nodes-1")
        if len(set(row)) != len(row):
            raise QuorumError("node ids in an entry must be different")
    return n, [list(r) for r in acks]


def quorum_commit(data):
    n, acks = _validate(data)
    q = n // 2 + 1
    counts = [len(r) for r in acks]
    commit = 0
    while commit < len(counts) and counts[commit] >= q:
        commit += 1
    held = sum(1 for c in counts[commit:] if c >= q)
    return {
        "status": "completed",
        "quorum": q,
        "counts": counts,
        "commit_index": commit,
        "held_back": held,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
