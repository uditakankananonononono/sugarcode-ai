"""Row 356 Critical Design: finite assumption-dependency challenge (exact).

A design lists named assumptions and claims; each claim states which assumptions
it depends on (a claim holds only if all of them hold). For every assumption the
module reports which claims fall if that assumption is negated, then ranks the
assumptions by how many claims they carry (most first, input order on ties).
Also lists unused assumptions (no claim depends on them) and unconditional claims
(depend on no assumption). 1 to 8 assumptions, 1 to 10 claims, each claim lists at
most 8 assumptions; ids are 1 to 40 character strings and unique within their kind.
Caps are implementation choices, not spec values. Dependencies are caller inputs.
NOT_CLAIMED: that any assumption is true or false, that the dependency list is
complete or correct, social, ethical or political critique quality, user research,
design quality or value, probability, deployment.
"""

NOT_CLAIMED = ('assumption truth', 'dependency list is complete or correct', 'critique quality',
               'user research', 'design quality or value', 'probability', 'deployment')


def _id(v):
    if type(v) is not str:
        raise TypeError('ids must be str')
    if not 1 <= len(v) <= 40:
        raise ValueError('ids must be 1 to 40 characters')
    return v


def challenge_assumptions(assumptions, claims):
    if type(assumptions) not in (list, tuple) or type(claims) not in (list, tuple):
        raise TypeError('assumptions and claims must be lists or tuples')
    if not 1 <= len(assumptions) <= 8:
        raise ValueError('assumption count must be between 1 and 8')
    if not 1 <= len(claims) <= 10:
        raise ValueError('claim count must be between 1 and 10')
    names = [_id(a) for a in assumptions]
    if len(set(names)) != len(names):
        raise ValueError('assumption ids must be unique')
    parsed = []
    for claim in claims:
        if type(claim) not in (list, tuple) or len(claim) != 2:
            raise ValueError('each claim must be (id, assumption_ids)')
        if type(claim[1]) not in (list, tuple) or len(claim[1]) > 8:
            raise ValueError('assumption ids must be a list or tuple of at most 8 ids')
        deps = [_id(d) for d in claim[1]]
        if len(set(deps)) != len(deps):
            raise ValueError('a claim may list each assumption once')
        parsed.append((_id(claim[0]), deps))
    if len({p[0] for p in parsed}) != len(parsed):
        raise ValueError('claim ids must be unique')
    if any(d not in names for p in parsed for d in p[1]):
        raise ValueError('claims may only depend on listed assumptions')
    falls = {a: [cid for cid, deps in parsed if a in deps] for a in names}
    ranking = sorted(range(len(names)), key=lambda i: (-len(falls[names[i]]), i))
    return {'falls_if_negated': falls,
            'ranking': [names[i] for i in ranking],
            'most_critical': [n for n in names if len(falls[n]) == len(falls[names[ranking[0]]])] if falls[names[ranking[0]]] else [],
            'unused_assumptions': [n for n in names if not falls[n]],
            'unconditional_claims': [cid for cid, deps in parsed if not deps],
            'assumptions_validated': False, 'not_claimed': NOT_CLAIMED}
