"""Row 696, Branch by Abstraction: step-order check for a large change.

abstraction_steps takes steps, a list or tuple of 0 to max_steps step names,
and max_steps, a nonbool int from 1 to 20 (default 7). A step is 'introduce',
'migrate', 'implement', 'switch' or 'remove'. Each step may be accepted once.
Rules: introduce has no precondition; migrate and implement need introduce;
switch needs migrate and implement; remove needs switch. A step that breaks its
rule is a violation, is ignored and does not change the state.
Returns done (accepted steps in the canonical order introduce, migrate,
implement, switch, remove), violations ((index, step) in input order) and
complete (all five steps accepted with no violation).
Checks, in this order: max_steps, steps type, steps size, each step name.
NOT_CLAIMED: running the change, caller coverage, behaviour equivalence,
rollback safety, production readiness.
"""
SCOPE = 'PARTIAL: precondition order check over supplied step names, no change is run'
NOT_CLAIMED = ('running the change', 'caller coverage', 'behaviour equivalence',
               'rollback safety', 'production readiness')

CANON = ('introduce', 'migrate', 'implement', 'switch', 'remove')
NEEDS = {
    'introduce': (),
    'migrate': ('introduce',),
    'implement': ('introduce',),
    'switch': ('migrate', 'implement'),
    'remove': ('switch',),
}


def abstraction_steps(steps, max_steps=7):
    if type(max_steps) is not int or not 1 <= max_steps <= 20:
        raise ValueError('max_steps must be a nonbool integer between 1 and 20')
    if type(steps) not in (list, tuple):
        raise TypeError('steps must be a list or tuple')
    if len(steps) > max_steps:
        raise ValueError('steps must contain at most max_steps entries')
    for s in steps:
        if type(s) is not str or s not in CANON:
            raise ValueError('each step must be introduce, migrate, implement, switch or remove')
    done = set()
    violations = []
    for i, s in enumerate(steps):
        if s in done or any(n not in done for n in NEEDS[s]):
            violations.append((i, s))
        else:
            done.add(s)
    return {'done': [s for s in CANON if s in done], 'violations': violations,
            'complete': len(done) == 5 and not violations}
