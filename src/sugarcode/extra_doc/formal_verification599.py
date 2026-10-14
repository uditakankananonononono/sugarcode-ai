"""Row 599 Formal Verification - Proves correctness.

SCOPED exhaustive reachable-state safety check of a supplied finite transition
relation. The checked property is absence of supplied bad states from states
reachable from a single start. This proves only that finite model property,
not program refinement, unmodeled behavior, liveness, safety of real systems or
correctness of the source code. No solver or external service.
"""
import re


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if not 1<=len(value)<=24 or re.fullmatch(r'[a-z][a-z0-9_]*',value) is None:
        raise ValueError('bounded lowercase identifier required')


def verify_reachability(start, transitions, bad_states):
    """Transitions list1..64 tuple(source,destination); bad list0..32 labels.
    At most32 states across start/transitions/bad; duplicate edges/bad refused.
    Return sorted reachable states and shortest lexicographic bad witness path.
    """
    _label(start)
    if type(transitions) is not list or type(bad_states) is not list:
        raise TypeError('exact transition and bad-state lists required')
    if not 1<=len(transitions)<=64 or not 0<=len(bad_states)<=32:
        raise ValueError('transition or bad-state count outside cap')
    for row in transitions:
        if type(row) is not tuple:
            raise TypeError('exact tuple transition required')
        if len(row)!=2:
            raise ValueError('transition arity must be two')
        for value in row:
            _label(value)
    for value in bad_states:
        _label(value)
    if len(set(transitions))!=len(transitions) or len(set(bad_states))!=len(bad_states):
        raise ValueError('duplicate transition or bad state')
    states={start,*bad_states,*[state for edge in transitions for state in edge]}
    if len(states)>32:
        raise ValueError('state count must be at most32')
    paths={start:(start,)}
    queue=[start]
    for current in queue:
        neighbors=sorted(dst for src,dst in transitions if src==current)
        for destination in neighbors:
            if destination not in paths:
                paths[destination]=paths[current]+(destination,)
                queue.append(destination)
    violations=[paths[state] for state in bad_states if state in paths]
    witness=min(violations,key=lambda path:(len(path),path)) if violations else None
    return {'safe_in_model':witness is None,'reachable':sorted(paths),
            'counterexample':list(witness) if witness is not None else None}
