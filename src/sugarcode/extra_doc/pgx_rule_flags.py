"""Row 1127, Pharmacogenomic Recommendations.

pgx_rule_flags treats x,y as caller-encoded four-bit genotype/rule flag
masks and reports (x&y)&mask. Returns flags as sorted (label,integer_mask),
review as sorted labels with any matched bit, bits as sorted (label,set_bit
indices) with indices zero through three ascending. The flag meanings are
not interpreted; no gene-drug relation, medication or dose is recommended.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 15; bool and all subclasses are refused.
mask defaults to 3, an exact int from 1 to 15.
Validation order: rows type, rows size, mask, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: drug recommendation, gene-drug validity, clinical safety, genotype interpretation, production readiness.
"""

SCOPE = 'PARTIAL: combines caller-supplied genotype and rule flag masks, no drug recommendation is made'
NOT_CLAIMED = ('drug recommendation', 'gene-drug validity', 'clinical safety', 'genotype interpretation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def pgx_rule_flags(rows, mask=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(mask) is not int or not 1 <= mask <= 15:
        raise ValueError('mask must be a nonbool integer between 1 and 15')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 15:
            raise ValueError('x must be a nonbool integer between 0 and 15')
        if type(y) is not int or not 0 <= y <= 15:
            raise ValueError('y must be a nonbool integer between 0 and 15')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    flags = [(n, (genotype & rule) & mask) for n, genotype, rule in sorted(clean, key=lambda r: r[0])]
    return {'flags': flags, 'review': [n for n, value in flags if value != 0],
            'bits': [(n, [i for i in range(4) if value & (1 << i)]) for n, value in flags]}
