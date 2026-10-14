"""Row 956: Acoustic Metamaterials - Sound manipulation.

PARTIAL: Adds supplied signed abstract signal pairs and reports exact cancellations.
Caps are module-local choices without physical units. No physical
validity or production readiness claimed.
"""
NOT_CLAIMED = ('physical_sound_manipulation', 'physical_validity', 'production_readiness')


def evaluate(rows):
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ValueError('rows: tuple of 1 to 20 integer pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (left, right) required')
        value,mask = row
        if type(value) is not int or not -100 <= value <= 100:
            raise ValueError(f'rows[{i}].left: whole number -100 to 100 required')
        if type(mask) is not int or not -100 <= mask <= 100:
            raise ValueError(f'rows[{i}].right: whole number -100 to 100 required')
    residuals = tuple(left+right for left,right in rows)
    cancelled = tuple(i for i in range(len(residuals)) if residuals[i] == 0)
    return {'abstract_signal_cancel_validated': False, 'not_claimed': NOT_CLAIMED,
            'residuals': residuals, 'cancelled_positions': cancelled, 'magnitude_total': sum(abs(v) for v in residuals)}
