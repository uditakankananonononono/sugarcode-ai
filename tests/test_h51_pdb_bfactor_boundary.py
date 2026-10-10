"""One supplied-atom filter literal, not structure or parser validation."""
from sugarcode.bio.pdb import select


def test_bfactor_equal_kept_missing_and_below_excluded():
    structure = {'atoms': [
        {'serial': 1, 'model': 1, 'bfactor': 9},
        {'serial': 2, 'model': 1, 'bfactor': 10},
        {'serial': 3, 'model': 1, 'bfactor': None},
    ]}
    assert [a['serial'] for a in select(structure, min_bfactor=10)] == [2]
