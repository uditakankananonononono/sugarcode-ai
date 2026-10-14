import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.organization1760 import audit_structure
import pytest

class TestAud:
    def test_audpin_depths_reports_1760(self):
        got = audit_structure([('b','a'),('a',None),('c','b')])
        assert got['root'] == 'a'
        assert got['depths'] == [('b',1),('a',0),('c',2)]
        assert got['direct_reports'] == [('b',['c']),('a',['b']),('c',[])]
        assert got['organization_validated'] is False
    def test_audpin_cycle_refused_1760(self):
        with pytest.raises(ValueError): audit_structure([('a','b'),('b','a'),('c',None)])
    def test_audpin_two_roots_refused_1760(self):
        with pytest.raises(ValueError): audit_structure([('a',None),('b',None)])
