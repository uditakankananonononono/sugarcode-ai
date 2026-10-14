"""Row 571, Reasoning Engine: exact forward chaining over if-then rules on named facts.

forward_chain(facts, rules) takes
  facts  names known to be true;
  rules  (premises, conclusion) pairs: when every name in premises is true, conclusion becomes true (a rule with no
         premises always applies).
Rules are applied in rounds. In round n every rule whose premises were all true at the end of round n-1 fires; a
conclusion not yet known becomes true in round n. It returns, exactly:
  facts    every true name once all rounds are done, sorted;
  derived  [name, round, rule_index] for each newly derived name, sorted by (round, name); rule_index counts from 0 and
           is the lowest-numbered rule that fires for that name in its round;
  rounds   how many rounds derived something (0 when nothing new is derived).
Caps: facts a list or tuple of 0 to 100 names; rules a list or tuple of 0 to 100 pairs; each premises a list or tuple of
0 to 8 names with no repeats; names are str of 1 to 30 characters from A-Z, a-z, 0-9, '_' and '-'; no repeated fact;
at most 100 distinct names in all. A rule may name a conclusion that is already a fact or a premise of itself.
Order of checks: facts (type, count, then each name in order: type, characters, repeat), then rules (type, count, then
each rule in order: pair shape, premises type, premises count, each premise's type and characters, repeated premise,
conclusion type and characters), then the name cap, and only then the rounds are run.

NOT_CLAIMED: propositional bookkeeping only. It does not say any rule is true in the world, that a derived name is
correct beyond the rules supplied, or that the rule set is complete or consistent; there is no negation, no
variables and no uncertainty. No clinical or wet-lab claim.
"""

MAX_FACTS = 100
MAX_RULES = 100
MAX_PREMISES = 8
MAX_NAMES = 100
NAME_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be a str')
    if not 1 <= len(v) <= 30 or any(ch not in NAME_CHARS for ch in v):
        raise ValueError(what + ' must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -')
    return v


def forward_chain(facts, rules):
    if type(facts) not in (list, tuple):
        raise TypeError('facts must be a list or tuple')
    if not 0 <= len(facts) <= MAX_FACTS:
        raise ValueError('fact count must be between 0 and 100')
    known = []
    for f in facts:
        n = _name(f, 'fact')
        if n in known:
            raise ValueError('facts must not repeat')
        known.append(n)
    if type(rules) not in (list, tuple):
        raise TypeError('rules must be a list or tuple')
    if not 0 <= len(rules) <= MAX_RULES:
        raise ValueError('rule count must be between 0 and 100')
    parsed = []
    for r in rules:
        if type(r) not in (list, tuple) or len(r) != 2:
            raise TypeError('each rule must be a (premises, conclusion) pair')
        prem = r[0]
        if type(prem) not in (list, tuple):
            raise TypeError('premises must be a list or tuple')
        if not 0 <= len(prem) <= MAX_PREMISES:
            raise ValueError('premise count must be between 0 and 8')
        ps = []
        for p in prem:
            n = _name(p, 'premise')
            if n in ps:
                raise ValueError('premises must not repeat')
            ps.append(n)
        parsed.append((ps, _name(r[1], 'conclusion')))
    names = set(known) | {c for _, c in parsed} | {p for ps, _ in parsed for p in ps}
    if len(names) > MAX_NAMES:
        raise ValueError('at most 100 distinct names are supported')
    true = set(known)
    derived = []
    rnd = 0
    while True:
        rnd += 1
        new = {}
        for i, (ps, c) in enumerate(parsed):
            if c not in true and c not in new and all(p in true for p in ps):
                new[c] = i
        if not new:
            break
        true |= set(new)
        derived.extend([c, rnd, i] for c, i in new.items())
    derived.sort(key=lambda d: (d[1], d[0]))
    return {'facts': sorted(true), 'derived': derived, 'rounds': rnd - 1}
