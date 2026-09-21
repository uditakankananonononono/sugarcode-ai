import unittest,tempfile
from sugarcode.modules.molecule_eval import *
class MoleculeEvalTests(unittest.TestCase):
 def test_validity_uniqueness_and_invalid_audit(self):
  r=evaluate_library(["CCO","CCO","c1ccccc1","C1CC"])
  self.assertEqual(r["valid_count"],3); self.assertEqual(r["unique_graph_count"],2); self.assertEqual(r["invalid_records"][0]["index"],3)
 def test_novelty_and_diversity_bounded(self):
  r=evaluate_library(["CCO","CCN","c1ccccc1"],reference_smiles=["CCO","CCC"])
  for k in ("internal_diversity","fingerprint_novelty_to_reference"):
   self.assertGreaterEqual(r[k]["estimate"],0); self.assertLessEqual(r[k]["estimate"],1)
 def test_comparison_zero_for_same_library(self):
  s=["CCO","CCN","c1ccccc1","CCCC"]
  r=compare_libraries(s,s); self.assertAlmostEqual(r["mean_property_js_divergence_bits"],0)
 def test_pareto(self):
  rs=[{"activity":8,"tox":3},{"activity":7,"tox":1},{"activity":6,"tox":4}]
  self.assertEqual(pareto_front(rs,{"activity":"max","tox":"min"}),[0,1])
 def test_offline(self):
  with tempfile.TemporaryDirectory() as d:
   c=ChEMBLReferenceClient(d,offline=True)
   with self.assertRaisesRegex(ChEMBLReferenceUnavailable,"offline cache miss"):c.approved_reference()
if __name__=="__main__":unittest.main()
