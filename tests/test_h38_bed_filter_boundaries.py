"""Current BED filter threshold findings, not independent interval validation."""
from copy import deepcopy

from sugarcode.bio.bed import filter_records


def test_min_width_equal_and_above_kept_below_dropped():
    records = [{'chrom': 'c', 'start': 0, 'end': width} for width in (9, 10, 11)]
    bed = {'header': ['track name=literal'], 'records': records}
    before = deepcopy(bed)
    assert filter_records(bed, min_width=10) == {
        'header': ['track name=literal'], 'records': records[1:]}
    assert bed == before


def test_min_score_equal_and_above_kept_below_and_missing_dropped():
    records = [{'chrom': 'c', 'start': i, 'end': i+1, 'score': score}
               for i, score in enumerate((9, 10, 11))]
    records.append({'chrom': 'c', 'start': 3, 'end': 4})
    bed = {'header': ['track name=literal'], 'records': records}
    before = deepcopy(bed)
    assert filter_records(bed, min_score=10) == {
        'header': ['track name=literal'], 'records': records[1:3]}
    assert bed == before
