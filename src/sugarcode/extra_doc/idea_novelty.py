"""Row 864, Creative Thinking - Generates novel ideas: novelty against known ideas.

idea_novelty takes known, a list or tuple of 1 to 6 ideas, and ideas, a list or
tuple of 1 to 6 ideas. An idea is a string of 1 to 3 words separated by single
spaces, each word 1 to 8 lowercase ASCII letters. The ideas in ideas are
distinct as written.
The vocabulary is every word in known. A candidate idea is new when it has a
word outside the vocabulary, a duplicate when its set of words equals the set
of words of a known idea (order and repeats do not matter), and a remix
otherwise (all words known, but no known idea has that set of words).
Returns ranked (a list of (idea, new_words, kind) for every candidate, where
new_words counts the distinct words outside the vocabulary and kind is 'new',
'remix' or 'duplicate'; most new words first, then remix before duplicate,
then idea text) and counts (how many candidates of each kind, as a dict with
keys new, remix and duplicate).
Checks, in this order: known type, known size, each known idea, ideas type,
ideas size, each candidate idea, distinct candidates.
NOT_CLAIMED: real creative thinking, usefulness of ideas, originality beyond
the supplied list, learner creativity, production readiness.
"""

SCOPE = 'PARTIAL: compares supplied idea words with supplied known ideas, no creativity is judged'
NOT_CLAIMED = ('real creative thinking', 'usefulness of ideas', 'originality beyond the supplied list',
               'learner creativity', 'production readiness')
KIND_ORDER = {'new': 0, 'remix': 1, 'duplicate': 2}


def _idea(x):
    if type(x) is not str:
        return False
    words = x.split(' ')
    if not 1 <= len(words) <= 3:
        return False
    return all(w.isascii() and w.isalpha() and w.islower() and 1 <= len(w) <= 8 for w in words)


def idea_novelty(known, ideas):
    if type(known) not in (list, tuple):
        raise TypeError('known must be a list or tuple')
    if not 1 <= len(known) <= 6:
        raise ValueError('known must contain 1 to 6 entries')
    for k in known:
        if not _idea(k):
            raise ValueError('each known idea must be 1 to 3 lowercase words of 1 to 8 ASCII letters')
    if type(ideas) not in (list, tuple):
        raise TypeError('ideas must be a list or tuple')
    if not 1 <= len(ideas) <= 6:
        raise ValueError('ideas must contain 1 to 6 entries')
    for i in ideas:
        if not _idea(i):
            raise ValueError('each idea must be 1 to 3 lowercase words of 1 to 8 ASCII letters')
    if len(set(ideas)) != len(ideas):
        raise ValueError('ideas must be distinct')
    vocab = {w for k in known for w in k.split(' ')}
    sets = [frozenset(k.split(' ')) for k in known]
    rows = []
    for i in ideas:
        words = frozenset(i.split(' '))
        fresh = len(words - vocab)
        if fresh:
            kind = 'new'
        elif words in sets:
            kind = 'duplicate'
        else:
            kind = 'remix'
        rows.append((-fresh, KIND_ORDER[kind], i, kind))
    rows.sort()
    counts = {'new': 0, 'remix': 0, 'duplicate': 0}
    for _, _, _, kind in rows:
        counts[kind] += 1
    return {'ranked': [(i, -f, kind) for f, _, i, kind in rows], 'counts': counts}
