import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.institution1761 import audit_rules

class TestAud:
    def test_audpin_missing_counts_1761(self):
        got = audit_rules(['r1','r2'],[('i1',['r1']),('i2',[])])
        assert got['missing'] == [('i1',['r2']),('i2',['r1','r2'])]
        assert got['rule_counts'] == [('r1',1),('r2',0)]
        assert got['compliance_validated'] is False
    def test_audpin_all_observed_1761(self):
        got = audit_rules(['r1'],[('i1',['r1']),('i2',['r1'])])
        assert got['missing'] == [('i1',[]),('i2',[])]
        assert got['rule_counts'] == [('r1',2)]
