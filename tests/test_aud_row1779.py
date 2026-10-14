from sugarcode.extra_doc.class1779 import assign_bands

def test_audpin_boundaries_1779():
    assert assign_bands([5,10,15],[('a',0),('b',5),('c',9),('d',10),('e',1000),('f',14)]) == {
        'bands': [('a',0),('b',1),('c',1),('d',2),('e',3),('f',2)],
        'counts': [(0,1),(1,2),(2,2),(3,1)],
        'claim': 'PARTIAL', 'class_inferred': False}

def test_audpin_single_threshold_1779():
    assert assign_bands([1],[('z',0),('y',1)]) == {
        'bands': [('z',0),('y',1)], 'counts': [(0,1),(1,1)],
        'claim': 'PARTIAL', 'class_inferred': False}
