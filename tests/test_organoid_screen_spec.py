from sugarcode.modules.organoid_screen import *
def test_legacy(): assert screen('colon',['drug_a'])['ranking']
def test_dose(): assert dose_response([.1,1,10],[.9,.5,.1])['ic50_uM']==1
def test_bliss(): assert bliss_synergy(.5,.5,.1)['synergistic']
def test_replicates(): assert replicate_quality([[1,2],[1,2]])['reproducible']
def test_heterogeneity(): assert heterogeneity([0,.1,.9,1])['resistant_fraction']==.5
def test_report(): assert 'not validated' in organoid_report('colon',['drug_a'])['model_status']
