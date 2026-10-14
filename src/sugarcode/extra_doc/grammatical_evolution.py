"""Row 939, Grammatical Evolution: mapping supplied codons.

Evolves grammar-based solutions. Each row pairs a rule name of
1 to 8 characters with a codon, an integer from 0 to 10.
Reported: the row total, the distinct rule count, the codon
sum, and choices - a mapping of each rule to its codon sum
modulo 4, the production it picks. Caps (checked before any
work): 0 to 100 rows.
NOT_CLAIMED: real grammatical evolution, evolutionary
computation, grammar design, program synthesis, optimization,
production readiness.
"""
SCOPE = 'PARTIAL: codon mapping over supplied rows, no real evolution'
NOT_CLAIMED = ('real grammatical evolution', 'evolutionary computation',
               'grammar design', 'program synthesis', 'optimization',
               'production readiness')

MAX_ROWS = 100
MAX_NAME = 8
MAX_CODON = 10
PRODUCTIONS = 4


def map_codons(rules):
    """Map codon sums to productions over named rules."""
    if type(rules) not in (list, tuple):
        raise TypeError('rules must be a list or tuple')
    if len(rules) > MAX_ROWS:
        raise ValueError('rules must contain at most 100 entries')
    rows = []
    for row in rules:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each row must be a (rule, codon) row')
        rule, codon = row
        if type(rule) is not str or not 1 <= len(rule) <= MAX_NAME:
            raise ValueError('rule must be a string of 1 to 8 characters')
        if type(codon) is not int or not 0 <= codon <= MAX_CODON:
            raise ValueError('codon must be an integer from 0 to 10')
        rows.append((rule, codon))
    sums = {}
    for rule, codon in rows:
        sums[rule] = sums.get(rule, 0) + codon
    choices = {rule: total % PRODUCTIONS for rule, total in sums.items()}
    return {'total': len(rows), 'rules': len(sums),
            'codons': sum(codon for rule, codon in rows),
            'choices': choices}
