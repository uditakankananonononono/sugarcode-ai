"""Row 834, Prior Knowledge Activation - Connects to existing: anchor links.

prior_anchors takes known, a list or tuple of 1 to 8 ASCII strings of 1 to 12
characters, distinct, naming what the learner already knows, and concepts, a
list or tuple of 1 to 6 (name, links) tuples. name is an ASCII string of 1 to
12 characters, distinct across concepts. links is a list or tuple of 0 to 4
ASCII strings of 1 to 12 characters, distinct within the tuple.
A link connects a concept to existing knowledge when it is in known.
Returns anchors (a list of (name, connected) per concept in input order, with
connected the links found in known, sorted), orphans (the names with no
connected link, in input order), ignored (how many links name nothing in
known, over all concepts) and linked_percent (the share of concepts with a
connected link, as a percent rounded down).
Checks, in this order: known type, known size, each known entry, distinct
known, concepts type, concepts size, each concept (shape, name, links type,
links size, each link, distinct links), distinct names.
NOT_CLAIMED: real prior knowledge, learner memory, transfer of learning,
curriculum fit, production readiness.
"""

SCOPE = 'PARTIAL: matches supplied concept links to a supplied known list, no knowledge is activated'
NOT_CLAIMED = ('real prior knowledge', 'learner memory', 'transfer of learning',
               'curriculum fit', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and 1 <= len(x) <= 12


def prior_anchors(known, concepts):
    if type(known) not in (list, tuple):
        raise TypeError('known must be a list or tuple')
    if not 1 <= len(known) <= 8:
        raise ValueError('known must contain 1 to 8 entries')
    for k in known:
        if not _label(k):
            raise ValueError('each known entry must be an ASCII string of 1 to 12 characters')
    if len(set(known)) != len(known):
        raise ValueError('known entries must be distinct')
    if type(concepts) not in (list, tuple):
        raise TypeError('concepts must be a list or tuple')
    if not 1 <= len(concepts) <= 6:
        raise ValueError('concepts must contain 1 to 6 entries')
    rows = []
    for c in concepts:
        if type(c) not in (list, tuple) or len(c) != 2:
            raise ValueError('each concept must be a (name, links) tuple')
        name, links = c
        if not _label(name):
            raise ValueError('each name must be an ASCII string of 1 to 12 characters')
        if type(links) not in (list, tuple):
            raise ValueError('links must be a list or tuple')
        if len(links) > 4:
            raise ValueError('links must contain 0 to 4 entries')
        for k in links:
            if not _label(k):
                raise ValueError('each link must be an ASCII string of 1 to 12 characters')
        if len(set(links)) != len(links):
            raise ValueError('links must be distinct')
        rows.append((name, links))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    anchors = []
    ignored = 0
    for name, links in rows:
        hit = sorted(k for k in links if k in known)
        ignored += len(links) - len(hit)
        anchors.append((name, hit))
    orphans = [n for n, hit in anchors if not hit]
    return {'anchors': anchors, 'orphans': orphans, 'ignored': ignored,
            'linked_percent': (len(anchors) - len(orphans)) * 100 // len(anchors)}
