import math
from sugarcode.modules.biofactory_1_a import *
def test_legacy_protocol(): assert generate_protocol('golden_gate')['steps']
def test_dag_dependencies():
 r=workflow_dag([{'op':'a'},{'op':'b'}]); assert r['edges']==[{'source':0,'target':1,'material_flow':True}]
def test_schedule_makespan(): assert schedule_resources(generate_protocol('gibson'))['makespan_min']>0
def test_bayesian_update_uncertainty(): assert bayesian_condition(.5,1,[.8,.9],.1)['posterior_variance']<1
def test_pid_response(): assert pid_control(1,[0,.5,.9])['controls'][0]>pid_control(1,[0,.5,.9])['controls'][-1]
def test_reagent_compensation(): assert reagent_activity(1,10,5)['compensation_factor']>1
def test_assay_quality(): assert assay_quality([10,11,9],[1,1.1,.9])['robust']
def test_failure_reroute(): assert reroute_on_failure(workflow_dag([{'op':'a'},{'op':'b'}]),0,{'op':'retry'})['fallback_id']==2
def test_log_machine_readable(): assert experiment_log(generate_protocol('gibson'),{'ok':1})['machine_readable']
def test_report_honest(): assert 'no AI optimizer' in dbtl_report('gibson')['model_status']
def test_diagnostics():
 d=factory_diagnostics(dbtl_report('gibson')); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
