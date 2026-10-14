from sugarcode.extra_doc.gender1778 import audit_allocations

def test_audpin_mixed_1778():
    assert audit_allocations(['a','b'],[('t1','b',5),('t2','b',0),('t3','a',7)]) == {
        'allocations': [('a',1,7),('b',2,5)],
        'claim': 'PARTIAL', 'gender_inferred': False, 'fairness_validated': False}

def test_audpin_empty_category_1778():
    assert audit_allocations(['m','n','o'],[('t','n',3)]) == {
        'allocations': [('m',0,0),('n',1,3),('o',0,0)],
        'claim': 'PARTIAL', 'gender_inferred': False, 'fairness_validated': False}
