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


def test_audit_lactate_flux_positive_and_malate_route_topological():
    from sugarcode.modules.metabodesigner import design_pathway, pathway_flux
    lac = design_pathway("lactate")
    assert pathway_flux(lac["route"], "lactate", "glucose")["objective_flux"] > 0
    assert pathway_flux(design_pathway("malate")["route"], "malate", "glucose")["objective_flux"] > 0
    r = design_pathway("malate")
    avail = {"glucose"}
    for step in r["route"]:
        assert all(s.lower() in avail for s in step["substrates"]), step["reaction"]
        avail |= {p.lower() for p in step["products"]}
    ids = [s["reaction"] for s in r["route"]]
    assert ids.index("R_PDH") < ids.index("R_CS") < ids.index("R_ICL") < ids.index("R_MLS")
