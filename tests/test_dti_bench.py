import unittest, tempfile
import numpy as np
from sugarcode.modules.dti_bench import protein_features,pair_features,fit_dti,predict_dti,validate_dti,ChEMBLPairClient,ChEMBLPairUnavailable

S1="MKTIIALSYIFCLVFADYKDDDDK"
S2="MNNNKLAILGATNAVAAHAAEAGADK"
S3="MARGKKIGYSAPRQTMEEDLQKLAEAGVEVEVK"
class DTIBenchTests(unittest.TestCase):
 def test_protein_features(self):
  x=protein_features(S1); self.assertEqual(len(x),50); self.assertAlmostEqual(sum(x[:20]),1.0)
  with self.assertRaises(ValueError): protein_features("SHORT")
 def test_pair_is_target_conditioned(self):
  self.assertFalse(np.array_equal(pair_features("CCO",S1,ligand_bits=32,interaction_dims=4),pair_features("CCO",S2,ligand_bits=32,interaction_dims=4)))
 def data(self):
  sm=["CC","CCC","CCCC","CCO","CCCO","CCN","CCCN","c1ccccc1","c1ccncc1","CC(=O)O","CCOC","CCS"]
  seq=[S1]*4+[S2]*4+[S3]*4; ids=["T1"]*4+["T2"]*4+["T3"]*4; y=[4+i*.2 for i in range(12)]
  return sm,seq,ids,y
 def test_fit_predict_support(self):
  sm,sq,ids,y=self.data(); m=fit_dti(sm,sq,y,ligand_bits=32,interaction_dims=4); r=predict_dti(m,[sm[0]],[sq[0]])[0]
  self.assertTrue(np.isfinite(r["prediction"])); self.assertEqual(r["applicability_domain"],"inside")
 def test_cold_target_split(self):
  sm,sq,ids,y=self.data(); r=validate_dti(sm,sq,y,ids,strategy="cold_target",test_fraction=.25,ligand_bits=32,interaction_dims=4)
  tr={ids[i] for i in r["train_indices"]}; te={ids[i] for i in r["test_indices"]}; self.assertTrue(tr.isdisjoint(te)); self.assertIn("Missing",r["limitations"][-1])
 def test_time_split_latest(self):
  sm,sq,ids,y=self.data(); r=validate_dti(sm,sq,y,ids,strategy="time",years=list(range(2010,2022)),test_fraction=.25,ligand_bits=32,interaction_dims=4)
  self.assertEqual(r["test_indices"],[9,10,11])
 def test_offline_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   c=ChEMBLPairClient(d,offline=True)
   with self.assertRaisesRegex(ChEMBLPairUnavailable,"offline cache miss"): c.pairs(["CHEMBL203"])
if __name__=="__main__": unittest.main()

def test_target_sequence_falls_back_to_component_resource():
    from sugarcode.modules.dti_bench.chembl_pairs import ChEMBLPairClient
    c=ChEMBLPairClient(offline=True)
    def fake_get(path,params=None):
        assert path.endswith('.json')
        if path.startswith('target_component/'):
            return {'sequence':'MSEQ'}
        return {'target_components':[{'component_id':147,'component_type':'PROTEIN'}]}
    c._get=fake_get
    assert c.target_sequence('CHEMBL203')=='MSEQ'
def test_target_sequence_multi_component_fails_closed():
    from sugarcode.modules.dti_bench.chembl_pairs import ChEMBLPairClient, ChEMBLPairUnavailable
    c=ChEMBLPairClient(offline=True)
    c._get=lambda path,params=None:{'target_components':[{'component_id':1},{'component_id':2}]} if not path.startswith('target_component/') else {'sequence':'M'}
    try:
        c.target_sequence('CHEMBL999'); assert False
    except ChEMBLPairUnavailable: pass
