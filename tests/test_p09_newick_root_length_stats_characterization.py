"""One supplied-root-length stats finding, authored NOT RUN."""
from sugarcode.bio.newick import stats


def test_supplied_root_length_five_in_full_stats_result():
    root = {
        'name': 'R', 'length': 5.0, 'children': [
            {'name': 'A', 'length': 1.0, 'children': []},
            {'name': 'B', 'length': None, 'children': []},
        ],
    }
    assert stats(root) == {
        'nodes': 3,
        'leaves': 2,
        'internal_nodes': 1,
        'binary': True,
        'total_branch_length': 6.0,
        'edges_missing_length': 1,
        'height': 1.0,
        'leaf_names': ['A', 'B'],
    }
