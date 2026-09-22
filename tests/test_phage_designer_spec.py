from sugarcode.modules.phage_designer import *
def test_legacy(): assert design_fiber('OmpC')['validation'] and design_lysin()['domains']
def test_adsorption(): assert adsorption_kinetics(100,100,.1)['adsorbed_fraction']>0
def test_host_range(): assert host_range({'a':{'OmpC':1}},design_fiber('OmpC'))['predicted_hosts']==['a']
def test_escape(): assert escape_probability(1e-8,2,1e8)['escape_probability']>0
def test_cocktail(): assert cocktail_design([{'target_receptor':'x','predicted_hosts':['a']}],['a'])['covered_fraction']==1
def test_report(): assert 'no trained host-range' in phage_report('OmpC',{'a':{'OmpC':1}})['model_status']
