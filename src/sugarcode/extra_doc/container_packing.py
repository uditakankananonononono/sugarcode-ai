"""Row 614, Container Orchestration (PARTIAL: one exact step): first-fit-decreasing placement of containers on nodes.

place_containers(nodes, containers) places each container on a node by a fixed rule. A node is (name, cpu, mem) and a
container is (name, cpu, mem): a lowercase identifier name and nonbool int sizes from 1 to 1000000 (cpu in millicores,
mem in MiB, say; the unit is the caller's). Containers are taken in order of cpu largest first, then mem largest first,
then name; each goes to the first node, in name order, that still has at least its cpu and its mem free; one that fits
nowhere is left unplaced and later, smaller ones are still tried. It returns:
  placements   (container, node) pairs sorted by container name;
  unplaced     names of containers placed nowhere, sorted;
  usage        (node, cpu_used, mem_used) for every node, sorted by node name.
Caps: 1 to 16 nodes and 0 to 64 containers; names unique within each list.
Order of checks: nodes first, then containers. For each list: the list type, the size, then each row in order (tuple type,
3 items, name, cpu, mem), then duplicate names. Messages begin with the list name (nodes or containers). Only then the
placement.

NOT_CLAIMED: this is one greedy rule, not an optimal packing (a different order could place more), and says nothing
about a real cluster. It does not read or change any real system, start a container, handle affinity, ports, storage,
priorities, restarts or failure, or check that a request is sensible. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
LIM = 1000000


def _check(rows, what, low, high):
    if type(rows) is not list:
        raise TypeError(what + ': must be an exact list')
    if not low <= len(rows) <= high:
        raise ValueError(what + ': count must be between %d and %d' % (low, high))
    out = []
    for row in rows:
        if type(row) is not tuple:
            raise TypeError(what + ': row must be an exact tuple')
        if len(row) != 3:
            raise ValueError(what + ': row must have 3 items')
        name, cpu, mem = row
        if type(name) is not str:
            raise TypeError(what + ': name must be an exact string')
        if LABEL.fullmatch(name) is None:
            raise ValueError(what + ': name must be 1 to 24 lowercase identifier characters')
        for label, v in (('cpu', cpu), ('mem', mem)):
            if type(v) is not int:
                raise TypeError(what + ': ' + label + ' must be a nonbool int')
            if not 1 <= v <= LIM:
                raise ValueError(what + ': ' + label + ' must be between 1 and 1000000')
        out.append(row)
    if len({r[0] for r in out}) != len(out):
        raise ValueError(what + ': duplicate name')
    return out


def place_containers(nodes, containers):
    ns = sorted(_check(nodes, 'nodes', 1, 16))
    cs = _check(containers, 'containers', 0, 64)
    used = {n[0]: [0, 0] for n in ns}
    placed = []
    unplaced = []
    for name, cpu, mem in sorted(cs, key=lambda c: (-c[1], -c[2], c[0])):
        for node, ncpu, nmem in ns:
            if ncpu - used[node][0] >= cpu and nmem - used[node][1] >= mem:
                used[node][0] += cpu
                used[node][1] += mem
                placed.append((name, node))
                break
        else:
            unplaced.append(name)
    return {'placements': sorted(placed), 'unplaced': sorted(unplaced),
            'usage': [(n[0], used[n[0]][0], used[n[0]][1]) for n in ns]}
