from sugarcode.modules.cell_free_opt import *
def test_batch(): assert batch_normalize([2,4],[1,2])['mean']==2
def test_sensitivity(): assert resource_sensitivity({'mg_mm':10,'k_mm':100,'pep_mm':18,'template_ng_ul':10,'peg_pct':1.5})['most_sensitive']
def test_pareto(): assert len(pareto_conditions([{'yield_g_l':1,'cost_usd':2},{'yield_g_l':2,'cost_usd':1},{'yield_g_l':3,'cost_usd':3}]))==2
def test_qc(): assert replicate_qc([1,1,1])['passes']
def test_kinetics(): assert kinetics({'yield_g_l':2})['final_g_l']>0
def test_scope(): assert 'wet-lab' in optimization_report(4)['validation_scope']
def test_grid_always_evaluates_documented_optimum():
    from sugarcode.modules.cell_free_opt.core import optimize_cfps
    for step in (1,2,3,4):
        b=optimize_cfps(step)
        assert b['template_ng_ul']==12 and b['mg_mm']==12 and b['k_mm']==120 and b['pep_mm']==20 and b['peg_pct']==2
        assert abs(b['yield_g_l']-2.0)<1e-9
