"""Row 1128, Clinical Trial Matching.

trial_checklist treats x as four-bit required checklist mask and y as
four-bit satisfied mask. Missing bits are required and not satisfied.
Returns missing as sorted (label,missing_mask), counts as sorted (label,
missing_bit_count), within_allowance as sorted labels with missing count at
most allowed_missing. Extra satisfied bits do not count against requirements.
This compares caller checklists only, not clinical eligibility or trial fit.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 15; bool and all subclasses are refused.
allowed_missing defaults to 0, an exact int from 0 to 4.
Validation order: rows type, rows size, allowed_missing, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: clinical eligibility, trial suitability, criterion validity, patient safety, production readiness.
"""

SCOPE = 'PARTIAL: compares supplied required and satisfied checklist masks, no clinical eligibility is determined'
NOT_CLAIMED = ('clinical eligibility', 'trial suitability', 'criterion validity', 'patient safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def trial_checklist(rows, allowed_missing=0):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(allowed_missing) is not int or not 0 <= allowed_missing <= 4:
        raise ValueError('allowed_missing must be a nonbool integer between 0 and 4')
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
    missing = [(n, required & (15 ^ satisfied)) for n, required, satisfied in sorted(clean, key=lambda r: r[0])]
    counts = [(n, value.bit_count()) for n, value in missing]
    return {'missing': missing, 'counts': counts,
            'within_allowance': [n for n, count in counts if count <= allowed_missing]}
