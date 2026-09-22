import math
from sugarcode.modules.promoter_lib import *
def test_legacy(): assert design_promoter()['sequence'] and generate_library()['members']
def test_occupancy(): assert thermodynamic_occupancy(10,1)>thermodynamic_occupancy(.1,1)
def test_repression():
 s=design_promoter()['sequence']; assert promoter_response(s,10)['expression']<promoter_response(s,.1)['expression']
def test_features(): assert sequence_features('AAAAACGT')['homopolymer_max']>=1
def test_host_context():
 s=design_promoter()['sequence']; assert host_context(s,'e_coli')['activity']>host_context(s,'yeast')['activity']
def test_motif(): assert motif_compatibility('AAAACCCC',{'x':'AAAA'})['x']['count']==1
def test_noise(): assert expression_noise(10)['fano']==6
def test_calibration(): assert library_calibration([1,2,3],[2,4,6])['rmse']<1e-9
def test_report_honest(): assert 'no trained sequence model' in promoter_report()['model_status']
def test_diagnostics():
 d=promoter_diagnostics(promoter_report()); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
