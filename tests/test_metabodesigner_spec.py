import math
from sugarcode.modules.metabodesigner import *
def route():return design_pathway('lactate')['route']
def test_legacy(): assert design_pathway('lactate')['found']
def test_stoich(): assert stoichiometric_matrix(route())['matrix']
def test_flux(): assert pathway_flux(route(),'lactate','glucose')['success']
def test_thermo(): assert thermodynamics(route())['total_dg']<0
def test_balance(): assert carbon_redox(route())['atp_demand']>=0
def test_risk(): assert intermediate_risk(route())
def test_dynamic(): assert dynamic_pathway([1,1])['product_final']>0
def test_chassis(): assert chassis_rank({'glycosylation':1})[0]['chassis']!='e_coli'
def test_report_honest(): assert 'not live KEGG/MetaCyc' in pathway_report('lactate')['model_status']
def test_diagnostics():
 d=metabolic_diagnostics(pathway_report('lactate')); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
