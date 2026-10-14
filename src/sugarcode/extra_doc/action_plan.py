"""Row 572, Planning System (PARTIAL: symbolic shortest-plan search only): exact shortest action sequence between two sets of true facts.

plan_actions(initial, goal, actions) takes
  initial  names true at the start;
  goal     names that must all be true at the end;
  actions  (name, needs, adds, removes) quadruples: an action can run when every name in needs is true; running it makes
           every name in adds true and every name in removes false (removals happen first, then additions).
It searches breadth first over all reachable sets of true names and returns, exactly:
  found   True when some sequence of actions reaches the goal (the empty sequence if the goal already holds);
  plan    the action names in order, or None; among shortest plans it is the one whose action positions in the
          actions list read smallest from the left (position 0 first), a deterministic tie break and nothing more;
  length  the number of actions in the plan, or None.
Caps: initial and goal lists or tuples of 0 to 16 names; actions a list or tuple of 0 to 40 quadruples; needs, adds and
removes each a list or tuple of 0 to 6 names with no repeats; names are str of 1 to 30 characters from A-Z, a-z, 0-9,
'_' and '-'; action names are unique (and live in their own namespace, apart from fact names); an action's adds and
removes share no name; at most 16 distinct fact names in all (so at most 65536 states are searched, exhaustively).
Order of checks: initial (type, count, each name, repeat), goal the same, then actions (type, count, then each action
in order: shape, name, repeated action name, then needs, adds, removes each with type, count, names, repeats; then the
adds/removes overlap), then the fact-name cap, and only then the search runs.

NOT_CLAIMED: symbolic bookkeeping only. It does not say the actions are physically possible, safe, cheap or fast,
that the listed needs and effects are the real ones, or that the plan is the best by any measure but number of steps;
there are no costs, durations or uncertainty. No clinical or wet-lab claim.
"""
from collections import deque

MAX_SET = 16
MAX_ACTIONS = 40
MAX_LIST = 6
MAX_FACTS = 16
NAME_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be a str')
    if not 1 <= len(v) <= 30 or any(ch not in NAME_CHARS for ch in v):
        raise ValueError(what + ' must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -')
    return v


def _names(vals, what, limit, item):
    if type(vals) not in (list, tuple):
        raise TypeError(what + ' must be a list or tuple')
    if not 0 <= len(vals) <= limit:
        raise ValueError(what + ' count must be between 0 and %d' % limit)
    out = []
    for v in vals:
        n = _name(v, item)
        if n in out:
            raise ValueError(what + ' must not repeat')
        out.append(n)
    return out


def plan_actions(initial, goal, actions):
    init = _names(initial, 'initial', MAX_SET, 'fact')
    goal_names = _names(goal, 'goal', MAX_SET, 'fact')
    if type(actions) not in (list, tuple):
        raise TypeError('actions must be a list or tuple')
    if not 0 <= len(actions) <= MAX_ACTIONS:
        raise ValueError('action count must be between 0 and 40')
    parsed, used = [], set()
    for a in actions:
        if type(a) not in (list, tuple) or len(a) != 4:
            raise TypeError('each action must be a (name, needs, adds, removes) quadruple')
        nm = _name(a[0], 'action name')
        if nm in used:
            raise ValueError('action names must not repeat')
        used.add(nm)
        needs = _names(a[1], 'needs', MAX_LIST, 'fact')
        adds = _names(a[2], 'adds', MAX_LIST, 'fact')
        rems = _names(a[3], 'removes', MAX_LIST, 'fact')
        if set(adds) & set(rems):
            raise ValueError('an action cannot both add and remove the same fact')
        parsed.append((nm, needs, adds, rems))
    facts = sorted(set(init) | set(goal_names) | {x for p in parsed for part in p[1:] for x in part})
    if len(facts) > MAX_FACTS:
        raise ValueError('at most 16 distinct fact names are supported')
    bit = {f: 1 << i for i, f in enumerate(facts)}

    def mask(names):
        m = 0
        for n in names:
            m |= bit[n]
        return m
    start, want = mask(init), mask(goal_names)
    ops = [(mask(n), mask(a), mask(r)) for _, n, a, r in parsed]
    if start & want == want:
        return {'found': True, 'plan': [], 'length': 0}
    came = {start: None}
    queue = deque([start])
    while queue:
        s = queue.popleft()
        for i, (n, a, r) in enumerate(ops):
            if s & n == n:
                t = (s & ~r) | a
                if t not in came:
                    came[t] = (s, i)
                    if t & want == want:
                        seq = []
                        while came[t] is not None:
                            t, j = came[t]
                            seq.append(parsed[j][0])
                        seq.reverse()
                        return {'found': True, 'plan': seq, 'length': len(seq)}
                    queue.append(t)
    return {'found': False, 'plan': None, 'length': None}
