from sugarcode.extra_doc.authoritarian1774 import concentration

def test_audpin_quarters_1774():
    assert concentration([('a',1),('b',3)]) == {
        'shares': [('a',(1,4)),('b',(3,4))], 'concentration': (5,8),
        'claim': 'PARTIAL', 'regime_inferred': False}

def test_audpin_three_1774():
    assert concentration([('x',2),('y',2),('z',4)]) == {
        'shares': [('x',(1,4)),('y',(1,4)),('z',(1,2))], 'concentration': (3,8),
        'claim': 'PARTIAL', 'regime_inferred': False}

def test_audpin_zero_share_1774():
    assert concentration([('m',0),('n',5)]) == {
        'shares': [('m',(0,1)),('n',(1,1))], 'concentration': (1,1),
        'claim': 'PARTIAL', 'regime_inferred': False}
