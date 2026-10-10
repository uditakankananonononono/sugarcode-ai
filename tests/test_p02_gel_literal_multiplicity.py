"""One source-derived literal gel-output finding. Authored NOT RUN."""
from sugarcode.bio.restriction import gel_bands


def test_literal_duplicate_sizes_keep_order_count_and_full_dicts():
    assert gel_bands([100, 100, 10000]) == [
        {'size': 10000, 'log10_bp': 4.0, 'rel_migration': 0.1},
        {'size': 100, 'log10_bp': 2.0, 'rel_migration': 0.9},
        {'size': 100, 'log10_bp': 2.0, 'rel_migration': 0.9},
    ]
