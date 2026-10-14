"""Row 947, Swarm Robotics: relaying a broadcast through the team.

A coordinated team passes a message robot to robot: each supplied hop
carries the broadcast from its sender to its receiver, and the message
spreads from the first sender outward level by level.  broadcast()
reports which robots the message reaches and at how many hops.

Input rows: (sender 1-8, receiver 1-8).  The source is the sender of the
first record, at depth 0.  Output: {'total', 'reached': sorted robots
the message reaches, 'depth': {robot: hop distance}, 'unreached': sorted
robots named in the records but never reached}.  Reported: depth is the
shortest hop count, so a diamond a->b, a->c, b->d, c->d puts d at depth
2; robots behind no relay path from the source stay unreached; a
self-hop reaches only the sender itself.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8

SCOPE = 'PARTIAL: relay reachability only; no formation control modeled'
NOT_CLAIMED = (
    'does not model radio range or signal loss',
    'does not coordinate movement or formations',
    'does not implement consensus on payloads',
    'does not relay messages after all supplied hops',
)


def _check_name(name: Any, row: int, field: str) -> None:
    if not isinstance(name, str) or type(name) is not str:
        raise TypeError(
            f'row {row}: {field} must be str, got {type(name).__name__}')
    if not 1 <= len(name) <= MAX_NAME:
        raise ValueError(f'row {row}: {field} must be 1-8 chars')


def broadcast(rows: Any) -> dict:
    """Return the relay summary for the supplied hops."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    edges = []
    mentioned = set()
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (sender, receiver) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        sender, receiver = row
        _check_name(sender, index, 'sender')
        _check_name(receiver, index, 'receiver')
        edges.append((sender, receiver))
        mentioned.add(sender)
        mentioned.add(receiver)
    depth: dict = {}
    if edges:
        source = edges[0][0]
        adjacency: dict = {}
        for sender, receiver in edges:
            adjacency.setdefault(sender, []).append(receiver)
        depth[source] = 0
        queue = [source]
        for robot in queue:
            for nxt in adjacency.get(robot, []):
                if nxt not in depth:
                    depth[nxt] = depth[robot] + 1
                    queue.append(nxt)
    reached = sorted(depth)
    unreached = sorted(name for name in mentioned if name not in depth)
    return {'total': len(rows), 'reached': reached, 'depth': dict(depth),
            'unreached': unreached}
