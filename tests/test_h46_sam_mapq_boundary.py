"""One supplied-record filter literal, not parser or mapping validation."""
from sugarcode.bio.sam import filter_records


def test_mapq_equal_kept_high_unmapped_excluded():
    sam = {'records': [
        {'qname': 'below', 'mapq': 24, 'flags': {'unmapped': False}},
        {'qname': 'equal', 'mapq': 25, 'flags': {'unmapped': False}},
        {'qname': 'high', 'mapq': 60, 'flags': {'unmapped': True}},
    ]}
    assert [r['qname'] for r in filter_records(sam, min_mapq=25)['records']] == ['equal']
