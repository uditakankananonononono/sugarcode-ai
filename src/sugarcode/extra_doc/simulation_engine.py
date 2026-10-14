"""Simulation Engine - exact discrete-event simulation of a multi-server FIFO queue.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness: the arrivals are the caller's own scenario. Input: customers, 1..200
[arrival, service] integer pairs with arrival 0..1000000 non-decreasing and service
1..10000; servers, an int 1..4.

Model: customers are served first come first served, ties in arrival order broken by
input order. Each customer takes the server that becomes free earliest (ties to the
lowest server number) and starts at max(arrival, that server's free time), finishing
start + service later. The result reports, per customer, the server, start, finish and
wait (start - arrival); the makespan (last finish); per-server busy time; the exact
average wait and utilisation (total busy time / (servers * makespan)) as Fraction
strings; the maximum wait; and the maximum number of customers waiting (arrived but not
started) at any instant, counted just after an arrival.

Scope: PARTIAL for the Simulation Engine line. Exact simulation of one specified
queueing scenario given as data. It is not a general simulation framework: no random
arrivals, no other service disciplines, no priorities, no routing networks.

Not claimed: that the scenario models any real system, that the averages generalise to
other arrivals, that the server count is adequate, or anything about the real world.
Every claim flag in the result is False.
"""
from fractions import Fraction

MAX_CUSTOMERS = 200
MAX_ARRIVAL = 1000000
MAX_SERVICE = 10000
MAX_SERVERS = 4
_TOP = frozenset({"customers", "servers"})

NOT_CLAIMED = (
    "the scenario models any real system",
    "the averages generalise to other arrivals",
    "the server count is adequate",
    "real-world outcome",
)
CLAIMS = {"models_real_system": False, "generalises": False, "capacity_adequate": False, "real_world": False}


class SimError(ValueError):
    pass


def _int(v, lo, hi, name):
    if type(v) is not int:
        raise SimError(f"{name} must be an int")
    if v < lo or v > hi:
        raise SimError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise SimError("data keys must be exactly customers, servers")
    raw = data["customers"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_CUSTOMERS:
        raise SimError("customers must be a list of 1..200 [arrival, service] pairs")
    cust, prev = [], 0
    for c in raw:
        if not isinstance(c, list) or len(c) != 2:
            raise SimError("customer must be an [arrival, service] pair")
        a = _int(c[0], 0, MAX_ARRIVAL, "arrival")
        s = _int(c[1], 1, MAX_SERVICE, "service")
        if a < prev:
            raise SimError("arrivals must be non-decreasing")
        prev = a
        cust.append((a, s))
    k = _int(data["servers"], 1, MAX_SERVERS, "servers")
    return cust, k


def simulation_engine(data):
    cust, k = _validate(data)
    free = [0] * k
    busy = [0] * k
    rows = []
    for a, s in cust:
        srv = min(range(k), key=lambda j: (free[j], j))
        start = max(a, free[srv])
        free[srv] = start + s
        busy[srv] += s
        rows.append({"server": srv, "arrival": a, "start": start, "finish": start + s, "wait": start - a})
    makespan = max(r["finish"] for r in rows)
    waits = [r["wait"] for r in rows]
    peak = 0
    for i, (a, _) in enumerate(cust):
        peak = max(peak, sum(1 for j in range(i + 1) if rows[j]["start"] > a))
    return {
        "status": "completed",
        "customers": rows,
        "makespan": makespan,
        "busy_time": busy,
        "average_wait": str(Fraction(sum(waits), len(waits))),
        "max_wait": max(waits),
        "utilisation": str(Fraction(sum(busy), k * makespan)),
        "max_queue_length": peak,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
