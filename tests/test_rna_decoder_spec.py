import math
from sugarcode.modules.rna_decoder import *
R='GGACTAAAACGTTTTGATCAGACT'
def test_legacy(): assert modification_map(R)['length']==len(R)
def test_nanopore_signal(): assert nanopore_modification([3],[0])['mean_probability']>.5
def test_multimap(): assert multi_modification_map(R)['site_count']>0
def test_structure(): assert structure_ensemble(R)['windows']
def test_kinetics(): assert modification_kinetics()['occupancy'][-1]>modification_kinetics()['occupancy'][0]
def test_functional(): assert functional_impact(R,multi_modification_map(R)['modifications'])['stability_relative']>0
def test_design_honest():
 d=design_rna(R); assert d['validation'] and 'no trained nanopore' in d['model_status']
def test_diagnostics():
 d=rna_diagnostics(design_rna(R)); assert len(d)==12 and all(math.isfinite(x) for x in d.values())


def test_audit_m6a_map_agrees_with_predict_m6a():
    import random
    from sugarcode.modules.rna_decoder.core import predict_m6a, multi_modification_map
    rng = random.Random(1)
    s = "".join(rng.choice("ACGT") for _ in range(400)) + "GGACT" * 6
    assert sorted(x["position"] for x in predict_m6a(s)) == sorted(
        x["position"] for x in multi_modification_map(s)["modifications"]["m6A"])
