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
