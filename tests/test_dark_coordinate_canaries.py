"""Coordinate annotation is real sequence work, not inferred transcription."""
import pytest
from sugarcode.modules.dark_genome.core import decode

def test_overlapping_coding_spans_count_union_not_sum():
    result=decode('ACGT'*100,coding_spans=[(0,200),(100,300)])
    assert result['dark_matter_fraction']==.25

@pytest.mark.parametrize('spans',[[(5,1)],[(-1,4)],[(0,405)],[(0.5,4)],[(True,4)]])
def test_coding_spans_require_valid_half_open_coordinates(spans):
    with pytest.raises(ValueError):
        decode('ACGT'*100,coding_spans=spans)

def test_empty_sequence_has_zero_noncoding_fraction():
    assert decode('')['dark_matter_fraction']==0

def test_motif_overlapping_coding_span_is_not_noncoding():
    result=decode('AAAAATGACTCAAAAA',coding_spans=[(8,12)])
    assert not any(x['tf']=='AP-1' for x in result['tf_motif_hits'])

def test_minus_strand_motif_is_reported_with_original_coordinates():
    from sugarcode.bio.sequence import reverse_complement
    result=decode('AAAAA'+reverse_complement('TGACTCA')+'AAAAA')
    hits=[x for x in result['tf_motif_hits'] if x['tf']=='AP-1']
    assert any(x['position']==5 and x['strand']=='-' and x['end']==12 for x in hits)

def test_short_orf_is_not_a_lncrna_call():
    result=decode('ATG'+'GCT'*30+'TAA')
    assert 'lncrna_candidates' not in result
    assert result['short_noncoding_orf_candidates']
    assert 'not transcript' in result['annotation_status']

def test_cpg_statistics_are_recomputed_for_merged_interval():
    seq='CG'*100 + 'CCGG'*25 + 'AT'*50
    result=decode(seq)
    for island in result['cpg_islands']:
        window=seq[island['start']:island['end']]
        expected=window.count('CG')*len(window)/(window.count('C')*window.count('G'))
        assert island['cpg_obs_exp']==pytest.approx(round(expected,3))

def test_enhancer_cluster_does_not_chain_past_claimed_500_bp_span():
    result=decode('TGACTCA'+'A'*430+'GGGCGG'+'A'*430+'CCAAT')
    assert all(c['end']-c['start'] <= 500 for c in result['enhancer_clusters'])
