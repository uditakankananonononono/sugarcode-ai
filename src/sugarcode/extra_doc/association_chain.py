"""Row 868, Associative Thinking - Connects concepts: strongest-link chain.

association_chain takes links, a list or tuple of 1 to 10 (a, b, strength)
tuples, start, a concept, and steps, a nonbool int from 1 to 6 (default 3). a
and b are concepts and strength is a nonbool int from 1 to 9. A concept is a
printable ASCII string of 1 to 12 characters (control characters are
refused). The two concepts of a link differ, no pair repeats in either order,
and the links name at most 8 concepts. start is named in links.
A link joins its two concepts in both directions. Starting from start, each
step moves along the strongest link to a concept not yet in the chain, ties to
the smaller concept name, and stops early when no such link exists.
Returns chain (start and the concepts reached, in order), strengths (the
strength of each step taken), total (the strengths added up) and stopped
(True when the chain ended before the requested number of steps).
Checks, in this order: steps, links type, links size, each link (shape, a, b,
strength, concepts differ), distinct pairs, concept count, start, start named.
NOT_CLAIMED: real associative thinking, meaning of the links, learner memory,
free association, production readiness.
"""

SCOPE = 'PARTIAL: greedy strongest-link walk over supplied weighted links, no association is thought'
NOT_CLAIMED = ('real associative thinking', 'meaning of the links', 'learner memory',
               'free association', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def association_chain(links, start, steps=3):
    if type(steps) is not int or not 1 <= steps <= 6:
        raise ValueError('steps must be a nonbool integer between 1 and 6')
    if type(links) not in (list, tuple):
        raise TypeError('links must be a list or tuple')
    if not 1 <= len(links) <= 10:
        raise ValueError('links must contain 1 to 10 entries')
    rows = []
    for e in links:
        if type(e) not in (list, tuple) or len(e) != 3:
            raise ValueError('each link must be an (a, b, strength) tuple')
        a, b, strength = e
        if not _label(a):
            raise ValueError('each first concept must be a printable ASCII string of 1 to 12 characters')
        if not _label(b):
            raise ValueError('each second concept must be a printable ASCII string of 1 to 12 characters')
        if type(strength) is not int or not 1 <= strength <= 9:
            raise ValueError('strength must be a nonbool integer between 1 and 9')
        if a == b:
            raise ValueError('the concepts of a link must differ')
        rows.append((a, b, strength))
    if len({frozenset(r[:2]) for r in rows}) != len(rows):
        raise ValueError('links must be distinct')
    near = {}
    for a, b, strength in rows:
        near.setdefault(a, []).append((b, strength))
        near.setdefault(b, []).append((a, strength))
    if len(near) > 8:
        raise ValueError('links must name at most 8 concepts')
    if not _label(start):
        raise ValueError('start must be a printable ASCII string of 1 to 12 characters')
    if start not in near:
        raise ValueError('start must be named in links')
    chain = [start]
    taken = []
    for _ in range(steps):
        options = [(-s, n) for n, s in near[chain[-1]] if n not in chain]
        if not options:
            break
        s, n = min(options)
        chain.append(n)
        taken.append(-s)
    return {'chain': chain, 'strengths': taken, 'total': sum(taken), 'stopped': len(taken) < steps}
