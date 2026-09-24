import pytest
import math
from sugarcode.modules.neuro_hub_dashboard import *
R=[{'module':'a','importable':True,'latency_ms':10},{'module':'b','importable':False,'latency_ms':30}]
def test_health(): assert platform_health(R)['global_flux']==.5
def test_flux_trend(): assert compute_flux_series([{'timestamp':1,'modules_online':1,'modules_total':2},{'timestamp':2,'modules_online':2,'modules_total':2}])['trend']==.5
def test_search(): assert unified_search('gene variant',[{'module':'a','text':'gene variant'},{'module':'b','text':'image'}])['results'][0]['module']=='a'
def test_project(): assert project_state('x','a','completed')['completion']==1
def test_snapshot_honest(): assert 'no neural inference model' in dashboard_snapshot(R)['model_status']
def test_diagnostics():
 d=dashboard_diagnostics(dashboard_snapshot(R)); assert len(d)==9 and all(math.isfinite(x) for x in d.values())


def test_audit_edge_cases_zero_modules_and_unknown_state():
 from sugarcode.modules.neuro_hub_dashboard import compute_flux_series, project_state
 r=compute_flux_series([{"timestamp":1,"modules_online":0,"modules_total":0},{"timestamp":2,"modules_online":3,"modules_total":4}])
 assert r["global_flux"]==[0,.75] and r["trend"]==.75
 with pytest.raises(ValueError,match="unknown project state"): project_state("p","m","weird")
