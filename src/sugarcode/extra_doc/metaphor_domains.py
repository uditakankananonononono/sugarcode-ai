"""Row 737, Metaphors: source-domain mix of supplied metaphor uses.

metaphor_domains takes uses, a list or tuple of 0 to 12 (label, domain)
pairs, and max_domains, a nonbool int from 1 to 5 (default 2). A label is a
string of 1 to 16 characters, distinct across uses. A domain is 'war',
'journey', 'building', 'nature' or 'machine'.
Returns counts ((domain, count) in the order war, journey, building, nature,
machine), distinct (number of domains with a count above 0), dominant (the
domain with the highest count, the earlier domain in that order on a tie,
None with no uses) and mixed (distinct > max_domains).
Checks, in this order: max_domains, uses type, uses size, each pair (shape,
label, domain), duplicate labels.
NOT_CLAIMED: real metaphor quality, meaning, style, audience fit,
production readiness.
"""
SCOPE = 'PARTIAL: source-domain tally of supplied metaphor labels, no text is read'
NOT_CLAIMED = ('real metaphor quality', 'meaning', 'style',
               'audience fit', 'production readiness')

DOMAINS = ('war', 'journey', 'building', 'nature', 'machine')


def metaphor_domains(uses, max_domains=2):
    if type(max_domains) is not int or not 1 <= max_domains <= 5:
        raise ValueError('max_domains must be a nonbool integer between 1 and 5')
    if type(uses) not in (list, tuple):
        raise TypeError('uses must be a list or tuple')
    if len(uses) > 12:
        raise ValueError('uses must contain at most 12 entries')
    labels = []
    counts = {d: 0 for d in DOMAINS}
    for u in uses:
        if type(u) not in (list, tuple) or len(u) != 2:
            raise ValueError('each use must be a (label, domain) pair')
        label, dom = u
        if type(label) is not str or not 1 <= len(label) <= 16:
            raise ValueError('each label must be a string of 1 to 16 characters')
        if type(dom) is not str or dom not in counts:
            raise ValueError('domain must be war, journey, building, nature or machine')
        labels.append(label)
        counts[dom] += 1
    if len(set(labels)) != len(labels):
        raise ValueError('labels must be distinct')
    distinct = sum(1 for d in DOMAINS if counts[d] > 0)
    dominant = None
    top = 0
    for d in DOMAINS:
        if counts[d] > top:
            top = counts[d]
            dominant = d
    return {'counts': [(d, counts[d]) for d in DOMAINS], 'distinct': distinct,
            'dominant': dominant, 'mixed': distinct > max_domains}
