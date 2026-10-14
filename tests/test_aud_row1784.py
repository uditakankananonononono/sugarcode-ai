from sugarcode.extra_doc.exclusion1784 import audit_access

def test_audpin_mixed_1784():
    assert audit_access(['a','b','c'],[('r1',['a','c']),('r2',[]),('r3',['a','b','c'])]) == {
        'missing': [('r1',['b']),('r2',['a','b','c']),('r3',[])],
        'no_access': ['r2'], 'full_access': ['r3'],
        'claim': 'PARTIAL', 'exclusion_inferred': False}
