"""Row 615 service mesh (PARTIAL): dividing a whole number of requests among services by weight.

requests is a whole number from 0 to 1e9. weights is a list of 1 to 20 (service, weight) pairs: service a unique
non-empty string up to 30 characters, weight a whole number from 0 to 1e6, with at least one weight above 0. split
(requests, weights) gives each service its exact share requests * weight / total as a whole number by the largest
remainder method: every service first gets the floor of its share, and the requests left over go one each to the
services with the largest fractional remainders, ties going to the earlier pair in the list. The counts always add
up to requests and no service is more than one request from its exact share. Rows come back in input order. This
divides numbers on paper; it does not route real traffic, retry, or check that any service is healthy."""

MAX_REQUESTS = 10**9
MAX_SERVICES = 20
MAX_NAME = 30
MAX_WEIGHT = 10**6
STATUS_NOTE = ("PARTIAL: arithmetic split of a supplied request count only; no real traffic routing, retries "
               "or health checks")


def _int(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def split(requests, weights):
    requests = _int(requests, "requests", 0, MAX_REQUESTS)
    if not isinstance(weights, (list, tuple)):
        raise ValueError("weights: list required")
    if not 1 <= len(weights) <= MAX_SERVICES:
        raise ValueError(f"weights: 1 to {MAX_SERVICES} entries required")
    rows = []
    seen = set()
    for i, row in enumerate(weights):
        if not isinstance(row, (list, tuple)):
            raise ValueError(f"weights[{i}]: (service, weight) required")
        if len(row) != 2:
            raise ValueError(f"weights[{i}]: 2 entries required")
        name, w = row
        if not isinstance(name, str) or not name or len(name) > MAX_NAME:
            raise ValueError(f"weights[{i}] service: non-empty string up to {MAX_NAME} characters required")
        w = _int(w, f"weights[{i}] weight", 0, MAX_WEIGHT)
        if name in seen:
            raise ValueError(f"weights[{i}] service: duplicate")
        seen.add(name)
        rows.append((name, w))
    total = sum(w for _, w in rows)
    if total == 0:
        raise ValueError("weights: at least one weight above 0 required")
    shares = [requests * w // total for _, w in rows]
    rems = [requests * w % total for _, w in rows]
    left = requests - sum(shares)
    order = sorted(range(len(rows)), key=lambda k: (-rems[k], k))
    for k in order[:left]:
        shares[k] += 1
    return {"split": [{"service": rows[k][0], "requests": shares[k]} for k in range(len(rows))],
            "total_weight": total, "status_note": STATUS_NOTE}
