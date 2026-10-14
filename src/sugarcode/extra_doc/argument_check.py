"""Row 863, Critical Thinking - Evaluates arguments: chained if-then validity.

argument_check takes facts, a list or tuple of 1 to 4 labels, rules, a list or
tuple of 1 to 6 (if_part, then_part) tuples, and conclusion, a label. A label
is a printable ASCII string of 1 to 12 characters (control characters are
refused). Facts are distinct. In a rule the two labels differ, and no rule is
repeated.
Each rule says that when its if_part holds its then_part holds. Starting from
the facts, rules are applied until nothing new holds.
Returns derived (every label that holds, sorted), steps (how many labels were
added beyond the facts), valid (the conclusion is in derived) and unsupported
(the if_parts, sorted, of rules that conclude the conclusion while their if_part
does not hold; this is how an argument that only affirms the consequent shows).
Checks, in this order: facts type, facts size, each fact, distinct facts, rules
type, rules size, each rule (shape, if_part, then_part, labels differ),
distinct rules, conclusion.
NOT_CLAIMED: real critical thinking, truth of premises, informal fallacies,
natural language arguments, production readiness.
"""

SCOPE = 'PARTIAL: forward-chains supplied if-then rules over supplied facts, no argument is judged'
NOT_CLAIMED = ('real critical thinking', 'truth of premises', 'informal fallacies',
               'natural language arguments', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def argument_check(facts, rules, conclusion):
    if type(facts) not in (list, tuple):
        raise TypeError('facts must be a list or tuple')
    if not 1 <= len(facts) <= 4:
        raise ValueError('facts must contain 1 to 4 entries')
    for x in facts:
        if not _label(x):
            raise ValueError('each fact must be a printable ASCII string of 1 to 12 characters')
    if len(set(facts)) != len(facts):
        raise ValueError('facts must be distinct')
    if type(rules) not in (list, tuple):
        raise TypeError('rules must be a list or tuple')
    if not 1 <= len(rules) <= 6:
        raise ValueError('rules must contain 1 to 6 entries')
    pairs = []
    for r in rules:
        if type(r) not in (list, tuple) or len(r) != 2:
            raise ValueError('each rule must be an (if_part, then_part) tuple')
        a, b = r
        if not _label(a):
            raise ValueError('each if_part must be a printable ASCII string of 1 to 12 characters')
        if not _label(b):
            raise ValueError('each then_part must be a printable ASCII string of 1 to 12 characters')
        if a == b:
            raise ValueError('a rule must have different if_part and then_part')
        pairs.append((a, b))
    if len(set(pairs)) != len(pairs):
        raise ValueError('rules must be distinct')
    if not _label(conclusion):
        raise ValueError('conclusion must be a printable ASCII string of 1 to 12 characters')
    holds = set(facts)
    queue = list(facts)
    while queue:
        now = queue.pop()
        for a, b in pairs:
            if a == now and b not in holds:
                holds.add(b)
                queue.append(b)
    return {'derived': sorted(holds), 'steps': len(holds) - len(facts),
            'valid': conclusion in holds,
            'unsupported': sorted(a for a, b in pairs if b == conclusion and a not in holds)}
