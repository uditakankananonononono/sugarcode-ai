from sugarcode.extra_doc.poverty1783 import audit_gap

def test_audpin_mixed_1783():
    assert audit_gap([('a',0),('b',500),('c',1000)],1000) == {
        'below': ['a','b'], 'shortfalls': [('a',1000),('b',500),('c',0)],
        'normalized_gap': (1,2), 'claim': 'PARTIAL', 'poverty_inferred': False}

def test_audpin_symmetric_1783():
    assert audit_gap([('a',250),('b',750)],1000) == {
        'below': ['a','b'], 'shortfalls': [('a',750),('b',250)],
        'normalized_gap': (1,2), 'claim': 'PARTIAL', 'poverty_inferred': False}
