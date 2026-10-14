"""Row 940, Gene Expression Programming: growing supplied genes.

Evolves expressions. Each row pairs a gene name of 1 to 8
characters with an operator, grow or split.
Reported: the two operator counts, the row total, and expressed
- the sorted genes whose final length reaches at least 6, where
length starts at 1, grow adds 1, and split doubles it. Caps
(checked before any work): 0 to 100 rows.
NOT_CLAIMED: real gene expression programming, evolutionary
computation, expression synthesis, optimization, code
generation, production readiness.
"""
SCOPE = 'PARTIAL: operator folding over supplied rows, no real genes'
NOT_CLAIMED = ('real gene expression programming',
               'evolutionary computation', 'expression synthesis',
               'optimization', 'code generation', 'production readiness')

MAX_ROWS = 100
MAX_NAME = 8
OPERATORS = ('grow', 'split')
EXPRESSED = 6


def express(genes):
    """Fold grow and split rows over named genes."""
    if type(genes) not in (list, tuple):
        raise TypeError('genes must be a list or tuple')
    if len(genes) > MAX_ROWS:
        raise ValueError('genes must contain at most 100 entries')
    rows = []
    for row in genes:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each row must be a (gene, operator) row')
        gene, operator = row
        if type(gene) is not str or not 1 <= len(gene) <= MAX_NAME:
            raise ValueError('gene must be a string of 1 to 8 characters')
        if type(operator) is not str or operator not in OPERATORS:
            raise ValueError("operator must be 'grow' or 'split'")
        rows.append((gene, operator))
    values = {}
    for gene, operator in rows:
        level = values.get(gene, 1)
        values[gene] = level + 1 if operator == 'grow' else level * 2
    expressed = sorted(g for g, v in values.items() if v >= EXPRESSED)
    grow = sum(1 for gene, operator in rows if operator == 'grow')
    return {'grow': grow, 'split': len(rows) - grow,
            'total': len(rows), 'expressed': expressed}
