"""Row 985: CAR-T Therapy - Engineered T cells.

PARTIAL: counts overlap between supplied target indices and supplied
observed indices. No CAR-T design, antigen specificity or clinical
interpretation. Caps of 1-20 indices per tuple and indices 0-100 are
this module's own choices, not a domain standard. Duplicates count once.
"""
MAX_INDICES = 20
MAX_INDEX = 100
NOT_CLAIMED = ('cart_design', 'antigen_specificity', 'clinical_interpretation')


def overlap(targets, observed):
    for name,indices in (('targets',targets),('observed',observed)):
        if type(indices) is not tuple or not 1 <= len(indices) <= MAX_INDICES:
            raise ValueError(f'{name}: tuple of 1 to 20 indices required')
        for i,value in enumerate(indices):
            if type(value) is not int or not 0 <= value <= MAX_INDEX:
                raise ValueError(f'{name}[{i}]: whole number 0 to 100 required')
    target_set = set(targets)
    observed_set = set(observed)
    return {'cart_target_overlap_validated': False, 'not_claimed': NOT_CLAIMED,
            'shared_count': len(target_set & observed_set),
            'missing_count': len(target_set - observed_set),
            'extra_count': len(observed_set - target_set),
            'all_targets_present': target_set <= observed_set}
