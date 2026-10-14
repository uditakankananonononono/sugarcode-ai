from sugarcode.extra_doc.nationalism1775 import count_symbols

def test_audpin_repeats_membership_1775():
    assert count_symbols(['a','b'],[('d1',['a','a','b']),('d2',['b'])]) == {
        'counts': [('a',2,1),('b',2,2)], 'claim': 'PARTIAL', 'ideology_inferred': False}

def test_audpin_empty_tags_1775():
    assert count_symbols(['z'],[('only',[])]) == {
        'counts': [('z',0,0)], 'claim': 'PARTIAL', 'ideology_inferred': False}

def test_audpin_single_doc_repeats_1775():
    assert count_symbols(['q'],[('d1',['q','q','q'])]) == {
        'counts': [('q',3,1)], 'claim': 'PARTIAL', 'ideology_inferred': False}
