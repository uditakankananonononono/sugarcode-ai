"""One forced-offset summary literal, not measured quality accuracy."""
from sugarcode.bio.fastq import stats


def test_forced64_literal_whole_summary():
    assert stats([{'id': 'r', 'sequence': 'ACGT', 'quality': 'IIII'}], offset=64) == {
        'reads': 1, 'bases': 4, 'offset': 64,
        'length': {'min': 4, 'max': 4, 'mean': 4.0},
        'gc': 0.5, 'n_fraction': 0.0, 'mean_phred': 9.0,
        'per_position_mean_phred': [9.0, 9.0, 9.0, 9.0],
        'offset_note': None,
    }
