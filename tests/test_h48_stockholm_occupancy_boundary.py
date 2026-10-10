"""One supplied alignment occupancy literal, not format or biology validation."""
from sugarcode.bio.stockholm import filter_columns


def test_full_occupancy_keeps_equal_and_excludes_dash_and_dot():
    records = [{'id': 'a', 'sequence': 'A-.'}, {'id': 'b', 'sequence': 'C-G'}]
    assert filter_columns(records, 1.0) == [
        {'id': 'a', 'sequence': 'A'}, {'id': 'b', 'sequence': 'C'},
    ]
