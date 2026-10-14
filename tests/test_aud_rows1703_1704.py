import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import regulation_register1703 as m03, permit_register1704 as m04

class Aud(unittest.TestCase):
    def test_audpin_behavior_1703(self):
        got = m03.records([('a','pending',2),('b','disputed',1)])
        self.assertEqual(got['records'], (('a','pending',2),('b','disputed',1)))
        self.assertEqual(got['statuses'], (('pending',1,2),('documented',0,0),('disputed',1,1)))
        self.assertEqual(got['disputed'], ('b',))
    def test_audpin_refusals_1703(self):
        with self.assertRaises(ValueError): m03.records([('a','open',1)])
        with self.assertRaises(ValueError): m03.records([('a','pending',1),('a','pending',2)])
        with self.assertRaises(ValueError): m03.records([])
    def test_audpin_behavior_1704(self):
        got = m04.records([('a','draft',2),('b','returned',1)])
        self.assertEqual(got['records'], (('a','draft',2),('b','returned',1)))
        self.assertEqual(got['statuses'], (('draft',1,2),('submitted',0,0),('returned',1,1)))
        self.assertEqual(got['returned'], ('b',))
    def test_audpin_refusals_1704(self):
        with self.assertRaises(ValueError): m04.records([('a','pending',1)])
        with self.assertRaises(ValueError): m04.records([('a','draft',-1)])
        with self.assertRaises(ValueError): m04.records([('a','draft',1),('a','draft',2)])
    def test_audpin_extra_1703_1704(self):
        self.assertEqual(m03.records([('a','pending',0)])['disputed'], ())
        self.assertEqual(m04.records([('a','submitted',3)])['statuses'], (('draft',0,0),('submitted',1,3),('returned',0,0)))

if __name__ == '__main__': unittest.main()
