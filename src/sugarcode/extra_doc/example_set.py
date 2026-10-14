"""Row 738, Examples: kind balance of supplied examples.

example_set takes examples, a list or tuple of 0 to max_examples (name, kind)
pairs, and max_examples, a nonbool int from 1 to 12 (default 6). A name is a
string of 1 to 16 characters, distinct across examples. A kind is 'typical',
'edge' or 'counter'.
Returns counts ((kind, count) in the order typical, edge, counter), missing
(kinds with count 0, in that order), starts_typical (the first example is
typical, False with no example) and ok (nothing missing and starts_typical).
Checks, in this order: max_examples, examples type, examples size, each pair
(shape, name, kind), duplicate names.
NOT_CLAIMED: real clarity, example correctness, learner understanding,
coverage of the idea, production readiness.
"""
SCOPE = 'PARTIAL: kind tally and order check of supplied example labels, no example is judged'
NOT_CLAIMED = ('real clarity', 'example correctness', 'learner understanding',
               'coverage of the idea', 'production readiness')

KINDS = ('typical', 'edge', 'counter')


def example_set(examples, max_examples=6):
    if type(max_examples) is not int or not 1 <= max_examples <= 12:
        raise ValueError('max_examples must be a nonbool integer between 1 and 12')
    if type(examples) not in (list, tuple):
        raise TypeError('examples must be a list or tuple')
    if len(examples) > max_examples:
        raise ValueError('examples must contain at most max_examples entries')
    names = []
    kinds = []
    for e in examples:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise ValueError('each example must be a (name, kind) pair')
        name, kind = e
        if type(name) is not str or not 1 <= len(name) <= 16:
            raise ValueError('each name must be a string of 1 to 16 characters')
        if type(kind) is not str or kind not in KINDS:
            raise ValueError('kind must be typical, edge or counter')
        names.append(name)
        kinds.append(kind)
    if len(set(names)) != len(names):
        raise ValueError('names must be distinct')
    counts = [(k, kinds.count(k)) for k in KINDS]
    missing = [k for k, c in counts if c == 0]
    first = len(kinds) > 0 and kinds[0] == 'typical'
    return {'counts': counts, 'missing': missing, 'starts_typical': first,
            'ok': not missing and first}
