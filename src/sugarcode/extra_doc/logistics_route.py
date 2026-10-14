"""Row 455 logistics optimization: the cheapest round trip from a depot through every stop.

dist is a square matrix of whole travel costs, dist[i][j] being the cost of going from stop i to stop j (it may
be asymmetric; the diagonal is ignored), with stop 0 the depot. The module finds, exactly, the cheapest tour
that leaves stop 0, visits every other stop once and returns to stop 0, by dynamic programming over subsets
(Held-Karp) for 2 to 12 stops. Among tours of equal cost the one whose stop sequence is lexicographically
smallest is reported. It optimises only the cost matrix it is given: no time windows, capacities, vehicle
count, traffic or fuel model."""

MAX_STOPS = 12
MAX_COST = 1_000_000
STATUS_NOTE = ("PARTIAL: exact cheapest round trip over a supplied cost matrix only; no time windows, "
               "capacities, vehicles or traffic")


def best_tour(dist):
    if not isinstance(dist, (list, tuple)):
        raise ValueError("dist: list required")
    n = len(dist)
    if not 2 <= n <= MAX_STOPS:
        raise ValueError(f"dist: 2 to {MAX_STOPS} stops required")
    for i, row in enumerate(dist):
        if not isinstance(row, (list, tuple)):
            raise ValueError(f"dist[{i}]: list required")
        if len(row) != n:
            raise ValueError(f"dist[{i}]: {n} entries required")
    d = []
    for i, row in enumerate(dist):
        out = []
        for j, v in enumerate(row):
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError(f"dist[{i}][{j}]: integer required")
            if not 0 <= v <= MAX_COST:
                raise ValueError(f"dist[{i}][{j}]: must be within 0 to {MAX_COST}")
            out.append(v)
        d.append(out)
    m = n - 1                                   # stops 1..n-1 are bits 0..m-1
    full = (1 << m) - 1
    INF = float("inf")
    # g[mask][i]: cheapest cost to finish (visit the rest, return to 0) standing at stop i with mask visited
    g = [[INF] * n for _ in range(1 << m)]
    for mask in range(full, -1, -1):
        for i in range(n):
            if i and not mask >> (i - 1) & 1:
                continue
            if mask == full:
                g[mask][i] = d[i][0]
                continue
            best = INF
            for j in range(1, n):
                if not mask >> (j - 1) & 1:
                    c = d[i][j] + g[mask | 1 << (j - 1)][j]
                    if c < best:
                        best = c
            g[mask][i] = best
    total = g[0][0]
    order, mask, cur = [0], 0, 0
    while mask != full:
        for j in range(1, n):                   # ascending: first optimal choice is the lexicographically smallest
            if not mask >> (j - 1) & 1 and d[cur][j] + g[mask | 1 << (j - 1)][j] == g[mask][cur]:
                order.append(j)
                mask |= 1 << (j - 1)
                cur = j
                break
    order.append(0)
    return {"cost": total, "order": order, "stops": n, "status_note": STATUS_NOTE}
