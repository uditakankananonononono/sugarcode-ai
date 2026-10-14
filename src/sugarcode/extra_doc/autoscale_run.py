"""Auto-Scaling - exact threshold autoscaler replayed over a list of integer loads.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: loads, an
exact list of 1..20 ints 0..10000 (one per tick); capacity, an int 1..1000 (load one replica
serves per tick); min_replicas and max_replicas, ints 1..20 with min <= max; start, an int
min_replicas..max_replicas; down_ticks, an int 1..5. The data keys are exactly capacity, down_ticks,
loads, max_replicas, min_replicas, start.

Each tick: desired = the smallest count whose capacity covers the load (ceil(load / capacity)),
held to min_replicas..max_replicas. If desired is above the current count, the count jumps to
desired at once and the low-tick counter resets. If desired is below the current count, the counter
goes up by one and, once it reaches down_ticks, the count drops by exactly 1 and the counter resets.
If equal, the counter resets. Then dropped = max(0, load - count * capacity) for that tick.

The result gives "history" (the count after each tick), "dropped" (per tick), "total_dropped",
"scale_ups" and "scale_downs" (ticks on which the count rose or fell), and "peak" (largest count).

Scope: PARTIAL for the Auto-Scaling line. One fixed policy on a plain list of numbers. No cloud, no
cost, no startup delay, no real service.

Not claimed: that this adjusts any real capacity, that the policy is a good one, that a load list
matches real traffic, or anything about the real world. Every claim flag in the result is False.
"""
NOT_CLAIMED = (
    "this adjusts any real capacity",
    "the policy is a good one",
    "a load list matches real traffic",
    "real-world outcome",
)
CLAIMS = {"real_capacity": False, "good_policy": False, "real_traffic": False, "real_world": False}
KEYS = {"capacity", "down_ticks", "loads", "max_replicas", "min_replicas", "start"}


class ScaleError(ValueError):
    pass


def _int(data, k, lo, hi):
    v = data[k]
    if type(v) is not int:
        raise ScaleError(k + " must be an int")
    if not lo <= v <= hi:
        raise ScaleError(k + " must be %d to %d" % (lo, hi))
    return v


def _validate(data):
    if type(data) is not dict or set(data) != KEYS:
        raise ScaleError("data keys must be exactly capacity, down_ticks, loads, max_replicas, min_replicas, start")
    loads = data["loads"]
    if type(loads) is not list or not 1 <= len(loads) <= 20:
        raise ScaleError("loads must be a list of 1 to 20 loads")
    for v in loads:
        if type(v) is not int:
            raise ScaleError("load must be an int")
        if not 0 <= v <= 10000:
            raise ScaleError("load must be 0 to 10000")
    cap = _int(data, "capacity", 1, 1000)
    lo = _int(data, "min_replicas", 1, 20)
    hi = _int(data, "max_replicas", 1, 20)
    if lo > hi:
        raise ScaleError("min_replicas must not exceed max_replicas")
    start = _int(data, "start", lo, hi)
    dt = _int(data, "down_ticks", 1, 5)
    return list(loads), cap, lo, hi, start, dt


def autoscale_run(data):
    loads, cap, lo, hi, cur, dt = _validate(data)
    low = 0
    hist, drop = [], []
    ups = downs = 0
    for load in loads:
        want = min(hi, max(lo, -(-load // cap)))
        if want > cur:
            cur = want
            low = 0
            ups += 1
        elif want < cur:
            low += 1
            if low >= dt:
                cur -= 1
                low = 0
                downs += 1
        else:
            low = 0
        hist.append(cur)
        drop.append(max(0, load - cur * cap))
    return {
        "status": "completed",
        "history": hist,
        "dropped": drop,
        "total_dropped": sum(drop),
        "scale_ups": ups,
        "scale_downs": downs,
        "peak": max(hist),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
