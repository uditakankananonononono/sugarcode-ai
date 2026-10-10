"""One supplied nested-interval literal, not independent merge validation."""
from sugarcode.bio.bed import merge_intervals


def test_nested_end_does_not_shrink_active_interval():
    records = [
        {'chrom': 'c', 'start': 11, 'end': 12},
        {'chrom': 'c', 'start': 2, 'end': 3},
        {'chrom': 'c', 'start': 0, 'end': 10},
    ]
    assert merge_intervals(records) == [
        {'chrom': 'c', 'start': 0, 'end': 10},
        {'chrom': 'c', 'start': 11, 'end': 12},
    ]
