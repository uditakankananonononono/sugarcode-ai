"""Row 1126, Genomics Interpretation.

allele_inventory treats x as supplied reference read count and y as alternate
read count per caller-named locus. Returns totals as sorted (label,x+y),
sufficient as sorted labels with total at least depth, alternate_dominant as
sorted labels with y>x, unobserved as sorted zero-total labels. Depth is a
caller threshold, not a sequencing-quality or clinical criterion. No genotype,
pathogenicity or genomics interpretation is generated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
depth defaults to 10, an exact int from 1 to 100.
Validation order: rows type, rows size, depth, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: variant pathogenicity, genotype call, sequencing quality, clinical interpretation, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied reference/alternate read counts, no variant interpretation is performed'
NOT_CLAIMED = ('variant pathogenicity', 'genotype call', 'sequencing quality', 'clinical interpretation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def allele_inventory(rows, depth=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(depth) is not int or not 1 <= depth <= 100:
        raise ValueError('depth must be a nonbool integer between 1 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    totals = [(n, reference + alternate) for n, reference, alternate in sorted(clean, key=lambda r: r[0])]
    sufficient = [n for n, count in totals if count >= depth]
    alternate_dominant = sorted(n for n, reference, alternate in clean if alternate > reference)
    unobserved = [n for n, count in totals if count == 0]
    return {'totals': totals, 'sufficient': sufficient,
            'alternate_dominant': alternate_dominant, 'unobserved': unobserved}
