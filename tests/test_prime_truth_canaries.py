"""Exact construction must reject requests it cannot encode, not fabricate lengths."""
import pytest
from sugarcode.modules.prime_design.core import design_pegrna, design_edit
SPACER = 'ACGTACGTACGTACGTACGT'
REGION = 'ACGT'*40

@pytest.mark.parametrize('edit_seq,rtt', [('ACGT',10), ('ACGT'*4,20), ('',10), ('ACGT'*5,0), ('ACGT'*5,True)])
def test_rtt_requested_length_is_not_silently_truncated_or_defaulted(edit_seq,rtt):
    with pytest.raises(ValueError):
        design_pegrna(SPACER,edit_seq,rtt_len=rtt)

@pytest.mark.parametrize('edit', [
    {'type':'deletion','position':4,'ref':'TT','alt':''},
    {'type':'deletion','position':158,'ref':'GTAC','alt':''},
    {'type':'deletion','position':4,'ref':'','alt':''},
    {'type':'deletion','position':4,'ref':'AC','alt':'G'},
    {'type':'insertion','position':4,'ref':'A','alt':'G'},
    {'type':'insertion','position':4,'ref':'','alt':''},
    {'type':'substitution','position':4,'ref':'','alt':'G'},
    {'type':'substitution','position':4,'ref':'AC','alt':''},
    {'type':'substitution','position':True,'ref':'C','alt':'G'},
])
def test_edits_validate_reference_and_shape_before_constructing(edit):
    with pytest.raises(ValueError):
        design_edit(REGION,edit)

def test_insertion_at_terminal_boundary_supported():
    result=design_edit(REGION,{'type':'insertion','position':len(REGION),'ref':'','alt':'T'})
    assert result['edited_region']==REGION+'T'

def test_ambiguous_input_is_not_silently_cleaned_for_oligos():
    with pytest.raises(ValueError):
        design_pegrna(SPACER,'ACGTNNNNACGT')

def test_pe3_candidates_are_actual_sgrnas_not_just_pam_positions():
    from sugarcode.bio.sequence import reverse_complement
    region = 'CCTGGGTCAATCCTTGGGGCCCAGACTGAGCACGTGATGGCAGAGGAAAG'+'ATAT'*15+'CCA'+'ACGT'*10
    result = design_edit(region, {'type':'insertion','position':34,'ref':'','alt':'CTT'})
    assert result['nicking_sgrna_candidates']
    primary = result['pegrna_designs'][0]
    for nick in result['nicking_sgrna_candidates']:
        assert len(nick['spacer']) == 20
        assert nick['strand'] != primary['pam_strand']
        assert 40 <= abs(nick['nick_position']-primary['nick_position']) <= 120
        start = nick['position']+3
        assert nick['spacer'] == reverse_complement(region[start:start+20])
        assert nick['primary_pam_position'] == primary['pam_position']

def test_plus_and_minus_insertion_designs_are_reverse_complement_symmetric():
    from sugarcode.bio.sequence import reverse_complement
    region = 'CCTGGGTCAATCCTTGGGGCCCAGACTGAGCACGTGATGGCAGAGGAAAG'
    plus = design_edit(region, {'type':'insertion','position':34,'ref':'','alt':'CTT'})
    minus = design_edit(reverse_complement(region), {'type':'insertion','position':len(region)-34,'ref':'','alt':'AAG'})
    target=plus['pegrna_designs'][0]
    matches=[d for d in minus['pegrna_designs'] if d['spacer']==target['spacer']]
    assert matches
    assert matches[0]['rt_template']==target['rt_template']
    assert matches[0]['pbs']==target['pbs']

def test_long_deletion_crossing_pbs_nick_boundary_is_not_encodable():
    region = 'CCTGGGTCAATCCTTGGGGCCCAGACTGAGCACGTGATGGCAGAGGAAAG'
    result = design_edit(region, {'type':'deletion','position':29,'ref':region[29:40],'alt':''})
    assert all(not (29 < d['nick_position'] < 40) for d in result['pegrna_designs'])

def test_each_rtt_actually_reaches_full_edited_allele_and_homology():
    region = 'CCTGGGTCAATCCTTGGGGCCCAGACTGAGCACGTGATGGCAGAGGAAAG'+'ATAT'*15
    pos=50
    result=design_edit(region,{'type':'substitution','position':pos,'ref':region[pos],'alt':'G'})
    for d in result['pegrna_designs']:
        if d['pam_strand']=='+':
            assert d['nick_position']+d['rtt_length'] >= pos+1+3
        else:
            assert d['nick_position']-d['rtt_length'] <= pos-3
