"""Row 685, Example Mapping (Bounded: one exact card-completeness rule): check an example map is ready to hand over.

check_example_map(rules, questions) takes rules as a list of (rule, examples), examples a tuple of example names, and questions
as a list of (question, resolved) with resolved an exact bool. It returns:
  no_examples   sorted rule names that have no example;
  shared        sorted example names that appear under more than one rule (an example repeated inside one rule is refused);
  open_questions sorted names of questions whose resolved is False;
  ready         True when there is at least one rule, no rule lacks an example, and no question is open.
Caps: 0 to 16 rules with unique names, 0 to 8 examples each, 0 to 16 questions with unique names. Names are 1 to 24 lowercase
identifier characters.
Order of checks: rules (list type, count, then each in order: tuple type, 2 items, rule name type and shape, examples tuple
type, count, each example type and shape, repeat inside the rule), duplicate rule name, questions (list type, count, then each
in order: tuple type, 2 items, name type and shape, resolved exact bool), duplicate question name, and only then the analysis.

NOT_CLAIMED: this checks counts and flags on a supplied map. It does not judge whether rules or examples are good, whether a
story is small enough, or whether a question was really answered. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _name(v):
    if type(v) is not str:
        raise TypeError('name must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError('name must be 1 to 24 lowercase identifier characters')


def check_example_map(rules, questions):
    if type(rules) is not list:
        raise TypeError('rules must be an exact list')
    if len(rules) > 16:
        raise ValueError('rule count must be at most 16')
    for r in rules:
        if type(r) is not tuple:
            raise TypeError('each rule must be an exact tuple')
        if len(r) != 2:
            raise ValueError('each rule must have 2 items')
        _name(r[0])
        if type(r[1]) is not tuple:
            raise TypeError('examples must be an exact tuple')
        if len(r[1]) > 8:
            raise ValueError('example count must be at most 8')
        for e in r[1]:
            _name(e)
        if len(set(r[1])) != len(r[1]):
            raise ValueError('repeated example in a rule')
    if len({r[0] for r in rules}) != len(rules):
        raise ValueError('duplicate rule name')
    if type(questions) is not list:
        raise TypeError('questions must be an exact list')
    if len(questions) > 16:
        raise ValueError('question count must be at most 16')
    for q in questions:
        if type(q) is not tuple:
            raise TypeError('each question must be an exact tuple')
        if len(q) != 2:
            raise ValueError('each question must have 2 items')
        _name(q[0])
        if type(q[1]) is not bool:
            raise TypeError('resolved must be an exact bool')
    if len({q[0] for q in questions}) != len(questions):
        raise ValueError('duplicate question name')
    owners = {}
    for r, ex in rules:
        for e in ex:
            owners[e] = owners.get(e, 0) + 1
    no_examples = sorted(r for r, ex in rules if not ex)
    open_q = sorted(q for q, done in questions if not done)
    return {'no_examples': no_examples, 'shared': sorted(e for e, n in owners.items() if n > 1),
            'open_questions': open_q, 'ready': bool(rules) and not no_examples and not open_q}
