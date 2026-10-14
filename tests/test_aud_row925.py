import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import dna_symbol_xor as dx

class Aud(unittest.TestCase):
    def test_audpin_scope_925(self):
        got = dx.xor('ACGT', 'AGCT')
        self.assertEqual(got['dna_symbol_xor_validated'], False)
        self.assertEqual(got['not_claimed'], ('molecular_execution','biological_computation','laboratory_validation'))
    def test_audpin_behavior_925(self):
        got = dx.xor('ACGT', 'AGCT')
        self.assertEqual(got['symbols'], 'ATTA')
        self.assertEqual(got['encoded'], (0, 3, 3, 0))
        self.assertEqual(got['zero_positions'], (0, 3))
    def test_audpin_involution_925(self):
        self.assertEqual(dx.xor('AAAA', 'AAAA')['symbols'], 'AAAA')
        self.assertEqual(dx.xor('AAAA', 'AAAA')['zero_positions'], (0, 1, 2, 3))
        self.assertEqual(dx.xor('TTTT', 'TTTT')['symbols'], 'AAAA')
    def test_audpin_refusals_925(self):
        with self.assertRaises(ValueError): dx.xor('', 'A')
        with self.assertRaises(ValueError): dx.xor('A'*31, 'A'*31)
        with self.assertRaises(ValueError): dx.xor('AA', 'A')
        with self.assertRaises(ValueError): dx.xor('a', 'A')
        with self.assertRaises(ValueError): dx.xor('N', 'A')
        with self.assertRaises(ValueError): dx.xor('x', 'A')  # gap witness: kills ALPHABET->'ACGTx' mutant
    def test_audpin_types_925(self):
        class S(str): pass
        with self.assertRaises(ValueError): dx.xor(S('A'), 'A')
        with self.assertRaises(ValueError): dx.xor(['A'], 'A')
        with self.assertRaises(ValueError): dx.xor(None, 'A')
        with self.assertRaises(ValueError): dx.xor('A', 'A\n')
        self.assertEqual(dx.xor('ACGT'*7+'AC', 'TGCA'*7+'TG')['symbols'], 'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT')

if __name__ == '__main__': unittest.main()
