import math
from sugarcode.modules.robotic_flow import *
T=[{'source':'A1','dest':'B1','volume_ul':10,'liquid':'water','contamination_group':'a'},{'source':'A2','dest':'B2','volume_ul':5,'liquid':'enzyme_mix','contamination_group':'b'}]
TASK=[{'id':'a','instrument':'pipette','duration_min':5},{'id':'b','instrument':'reader','duration_min':10,'after':['a']}]
def test_legacy(): assert pipette_plan(T)['steps'] and schedule_run(TASK)['timeline']
def test_fluid_error(): assert droplet_error(10,6)['relative_error']>droplet_error(10,1)['relative_error']
def test_control(): assert environmental_control(37,[35,36,36.8])['final_error']>0
def test_anomaly(): assert sensor_anomalies([1,1,1,10],1)['anomalies']
def test_lineage(): assert sample_lineage(['a'],[{'op':'mix','inputs':['a'],'output':'b'}])['traceable']
def test_reagent(): assert not reagent_status(20,5)['usable']
def test_contamination(): assert contamination_control(T)['tip_changes']==1
def test_corrective(): assert corrective_action({'severity':'critical'})['requires_human_review']
def test_report_honest(): assert 'no computer vision' in robotic_report(T,TASK)['model_status']
def test_diagnostics():
 d=robotic_diagnostics(robotic_report(T,TASK)); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
