import numpy as np
import pytest
from sugarcode.modules.qsar_bench import descriptors,morgan_fingerprint,fit_qsar,predict,validate_qsar
from sugarcode.modules.qsar_bench.chembl_client import ChEMBLQSARClient,ChEMBLUnavailable

def test_descriptors_formula_and_graph():
    d=descriptors("CCO")
    assert d["molecular_weight"]==pytest.approx(46.069,abs=.01)
    assert d["heavy_atoms"]==3 and d["hbd_heuristic"]==1 and d["hba_heuristic"]==1
    assert descriptors("c1ccccc1")["ring_rank"]==1

def test_parser_rejects_bad_smiles():
    with pytest.raises(ValueError): descriptors("C1CC")
    with pytest.raises(ValueError): descriptors("")

def test_fingerprint_is_stable_and_structure_sensitive():
    a=morgan_fingerprint("CCO",n_bits=128); b=morgan_fingerprint("CCO",n_bits=128); c=morgan_fingerprint("c1ccccc1",n_bits=128)
    assert np.array_equal(a,b) and not np.array_equal(a,c)

def test_fit_predict_and_ad_output():
    s=["CC","CCC","CCCC","CCO","CCCO","CCN","CCCN","c1ccccc1"]
    y=[1,2,3,1.2,2.2,1.3,2.3,4]
    m=fit_qsar(s,y,n_bits=64)
    r=predict(m,["CCO","CCCCCCCCCCCC"])
    assert all(np.isfinite(x["prediction"]) for x in r)
    assert set(r[0]) >= {"max_training_tanimoto","applicability_domain","ad_threshold"}

def test_validation_audit_fields_and_disjoint_split():
    s=["CC","CCC","CCCC","CCCCC","CCO","CCCO","CCCCO","CCN","CCCN","CCCCN","c1ccccc1","c1ccncc1"]
    y=np.linspace(4,8,len(s))
    r=validate_qsar(s,y,strategy="random",test_fraction=.25,n_bits=64)
    assert set(r["train_indices"]).isdisjoint(r["test_indices"])
    assert r["metrics"]["n"]==3 and "Missing" in r["limitations"][-1]

def test_time_split_holds_out_latest():
    s=["CC","CCC","CCCC","CCCCC","CCO","CCCO","CCN","CCCN"]
    r=validate_qsar(s,list(range(8)),strategy="time",years=list(range(2010,2018)),test_fraction=.25,n_bits=32)
    assert r["test_indices"]==[6,7]

def test_offline_cache_miss_is_explicit(tmp_path):
    c=ChEMBLQSARClient(tmp_path,offline=True)
    with pytest.raises(ChEMBLUnavailable,match="offline cache miss"):
        c.target_dataset("CHEMBL203")
