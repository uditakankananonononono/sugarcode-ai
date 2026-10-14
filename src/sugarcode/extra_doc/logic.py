"""Row 749, Logic: deriving facts by bounded modus ponens.

Reasons validly by closure. Facts are strings of 1 to 8 characters;
each rule pairs an antecedent with a consequent, both strings of 1 to
8 characters. Derivation repeats passes over the rules in order,
adding a rule's consequent whenever its antecedent is known, until a
pass adds nothing (at most 25 passes). Reported: the derived facts
(the closure minus the initial facts, sorted), the number of passes
run, and the size of the closure. Caps (checked before any work):
0 to 20 facts, 0 to 20 rules.
NOT_CLAIMED: real theorem proving, first-order logic, soundness
proofs, negation, quantifiers, SAT solving, production readiness.
"""
SCOPE = 'PARTIAL: propositional modus ponens over supplied facts and rules'
NOT_CLAIMED = ('real theorem proving', 'first-order logic', 'soundness proofs',
               'negation', 'quantifiers', 'SAT solving', 'production readiness')

MAX_FACTS = 20
MAX_RULES = 20
MAX_SYMBOL = 8
MAX_PASSES = 25


def derive(facts, rules):
    if type(facts) not in (list, tuple):
        raise TypeError('facts must be a list or tuple')
    if len(facts) > MAX_FACTS:
        raise ValueError('facts must contain at most 20 entries')
    for fact in facts:
        if type(fact) is not str or not 1 <= len(fact) <= MAX_SYMBOL:
            raise ValueError('facts must be strings of 1 to 8 characters')
    if type(rules) not in (list, tuple):
        raise TypeError('rules must be a list or tuple')
    if len(rules) > MAX_RULES:
        raise ValueError('rules must contain at most 20 rows')
    rows = []
    for row in rules:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each rule must be an (antecedent, consequent) row')
        antecedent, consequent = row
        if type(antecedent) is not str or not 1 <= len(antecedent) <= MAX_SYMBOL:
            raise ValueError('antecedent must be a string of 1 to 8 characters')
        if type(consequent) is not str or not 1 <= len(consequent) <= MAX_SYMBOL:
            raise ValueError('consequent must be a string of 1 to 8 characters')
        rows.append((antecedent, consequent))
    known = set(facts)
    passes = 0
    while passes < MAX_PASSES:
        added = False
        for antecedent, consequent in rows:
            if antecedent in known and consequent not in known:
                known.add(consequent)
                added = True
        passes += 1
        if not added:
            break
    return {'derived': sorted(known - set(facts)), 'passes': passes,
            'total': len(known)}
