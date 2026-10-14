"""Row 684, Event Storming (Bounded: one exact timeline-grammar rule): check the order of stickies on an event storming timeline.

check_timeline(stickies) takes stickies as a list of (kind, name) in timeline order; kind is 'actor', 'command', 'policy' or
'event'. The grammar, checked at every position i (0-based), is:
  actor    must be followed at once by a command            else (i, 'actor_without_command');
  command  must be followed at once by an event             else (i, 'command_without_event');
           must come right after an actor or a policy       else (i, 'command_without_trigger');
  policy   must be followed at once by a command            else (i, 'policy_without_command');
           must come right after an event                   else (i, 'policy_without_event');
  event    has no rule of its own.
A position can break two rules, and then both are reported. It returns {'problems': sorted (index, code), 'counts': {kind:
count} for all four kinds, 'events': the event names in timeline order}.
Caps: 0 to 64 stickies; names are 1 to 24 lowercase identifier characters (repeats allowed).
Order of checks: stickies (list type, count, then each in order: tuple type, 2 items, kind type and value, name type and shape),
and only then the grammar.

NOT_CLAIMED: this checks a supplied timeline against this small grammar. It does not find events, judge their names or their
completeness, run a workshop, or say that a model fits any business. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
KINDS = ('actor', 'command', 'policy', 'event')


def check_timeline(stickies):
    if type(stickies) is not list:
        raise TypeError('stickies must be an exact list')
    if len(stickies) > 64:
        raise ValueError('sticky count must be at most 64')
    for s in stickies:
        if type(s) is not tuple:
            raise TypeError('each sticky must be an exact tuple')
        if len(s) != 2:
            raise ValueError('each sticky must have 2 items')
        if type(s[0]) is not str:
            raise TypeError('kind must be an exact string')
        if s[0] not in KINDS:
            raise ValueError("kind must be 'actor', 'command', 'policy' or 'event'")
        if type(s[1]) is not str:
            raise TypeError('name must be an exact string')
        if LABEL.fullmatch(s[1]) is None:
            raise ValueError('name must be 1 to 24 lowercase identifier characters')
    kinds = [k for k, _ in stickies]
    problems = []
    for i, k in enumerate(kinds):
        before = kinds[i - 1] if i > 0 else None
        after = kinds[i + 1] if i + 1 < len(kinds) else None
        if k == 'actor' and after != 'command':
            problems.append((i, 'actor_without_command'))
        elif k == 'command':
            if after != 'event':
                problems.append((i, 'command_without_event'))
            if before not in ('actor', 'policy'):
                problems.append((i, 'command_without_trigger'))
        elif k == 'policy':
            if after != 'command':
                problems.append((i, 'policy_without_command'))
            if before != 'event':
                problems.append((i, 'policy_without_event'))
    return {'problems': sorted(problems), 'counts': {k: kinds.count(k) for k in KINDS},
            'events': [n for k, n in stickies if k == 'event']}
