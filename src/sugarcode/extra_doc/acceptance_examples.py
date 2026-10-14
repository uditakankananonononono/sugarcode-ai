"""Row 688: Acceptance Test-Driven Development - Tests from user perspective.

PARTIAL: compares supplied expected/observed integer results for example
cases, reporting mismatches. No user acceptance, test generation or
software validation. Caps of 1-30 pairs and values -1000 to 1000 are
this module's own choices, not a domain standard.
"""
MAX_CASES = 30
LIMIT = 1000
NOT_CLAIMED = ('user_acceptance', 'test_generation', 'software_validation')


def examples(cases):
    if type(cases) is not tuple or not 1 <= len(cases) <= MAX_CASES:
        raise ValueError('cases: tuple of 1 to 30 pairs required')
    for i,row in enumerate(cases):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'cases[{i}]: pair (expected, observed) required')
        for name,value in zip(('expected','observed'),row):
            if type(value) is not int or not -LIMIT <= value <= LIMIT:
                raise ValueError(f'cases[{i}].{name}: whole number -1000 to 1000 required')
    mismatches = tuple(i for i in range(len(cases)) if cases[i][0] != cases[i][1])
    differences = tuple(observed - expected for expected,observed in cases)
    return {'acceptance_examples_validated': False, 'not_claimed': NOT_CLAIMED,
            'mismatch_positions': mismatches, 'differences': differences,
            'matched_count': len(cases) - len(mismatches), 'all_match': not mismatches}
