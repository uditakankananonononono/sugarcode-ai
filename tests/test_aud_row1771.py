import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.movement1771 import audit_attendance

class TestAud:
    def test_audpin_attendance_overlap_1771(self):
        got = audit_attendance([('e1',['a','b']),('e2',['b','c']),('e3',['b'])])
        assert got['participants'] == ['a','b','c']
        assert got['attendance'] == [('a',1),('b',3),('c',1)]
        assert got['overlap'] == [('e1','e2',1),('e2','e3',1)]
        assert got['movement_validated'] is False
    def test_audpin_empty_event_1771(self):
        got = audit_attendance([('e1',[]),('e2',['a'])])
        assert got['participants'] == ['a'] and got['overlap'] == [('e1','e2',0)]
