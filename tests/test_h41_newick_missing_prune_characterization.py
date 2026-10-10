"""Three missing/mixed length merge findings, no phylogenetic validation."""
from copy import deepcopy

import pytest

from sugarcode.bio.newick import parse_newick, prune


@pytest.mark.parametrize('literal,length', [
    ('((A,B:1)I,C:4)R;', None),
    ('((A:2,B:1)I,C:4)R;', 2.0),
    ('((A,B:1)I:3,C:4)R;', 3.0),
])
def test_prune_missing_or_mixed_lengths_exact_tree(literal, length):
    original = parse_newick(literal)
    before = deepcopy(original)
    assert prune(original, ['B']) == {
        'name': 'R', 'length': None, 'children': [
            {'name': 'A', 'length': length, 'children': []},
            {'name': 'C', 'length': 4.0, 'children': []},
        ],
    }
    assert original == before
