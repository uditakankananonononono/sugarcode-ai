import pytest
from sugarcode.self_improve.isolation import IsolatedRunner,IsolationUnavailable
from sugarcode.self_improve.plans import Candidate,FeaturePlan


def candidate(test):
 return Candidate(FeaturePlan('m','demo','keyword_filter','d','g'),'def run(items,params=None):return items',test)


@pytest.mark.parametrize('stream',[1,2])
@pytest.mark.parametrize('size',[1048576,1048577])
def test_real_isolated_exact_and_oneover_raw_pipe(real_containment,stream,size):
 test=f'import os\nos.write({stream},b"x"*{size})\nos._exit(0)'
 class Uncaptured(IsolatedRunner):
  def _command(self,work):return super()._command(work)+['--setenv','PYTEST_ADDOPTS','-s']
 r=Uncaptured().run(candidate(test))
 assert r.output_limit_exceeded==(size>1048576)
 assert r.passed==(size==1048576)
 assert r.output_limit_stream==(('stdout' if stream==1 else 'stderr') if size>1048576 else None)
 assert len(r.stdout.encode())<=12000 and len(r.stderr.encode())<=12000
 if size>1048576:assert 'output byte limit exceeded' in r.stderr


def test_inherited_pipe_deadline_result_mapping(monkeypatch,real_containment):
 from sugarcode.self_improve import isolation
 from sugarcode.self_improve.bounded_process import CapturedProcess
 monkeypatch.setattr(isolation,'run_bounded_process',lambda *a,**kw:CapturedProcess(0,b'',b'',True,None,0,0,0))
 r=IsolatedRunner().run(candidate(''))
 assert r.timed_out and not r.passed and r.exit_code==0
 assert not r.output_limit_exceeded


def test_real_timeout_kill_keeps_negative_actual_exit(real_containment):
 r=IsolatedRunner(timeout_seconds=.5).run(candidate('import time;time.sleep(30)'))
 assert r.timed_out and r.exit_code<0 and not r.output_limit_exceeded


def test_unavailable_probe_refuses_without_candidate_capture(monkeypatch):
 from sugarcode.self_improve import isolation
 monkeypatch.setattr(isolation,'run_bounded_process',lambda *a,**k:pytest.fail('candidate launched'))
 with pytest.raises(IsolationUnavailable):IsolatedRunner(bwrap='/nonexistent').run(candidate(''))


def test_regular_file_rlimit_kept(real_containment):
 test='''def test_limit():
 from pathlib import Path
 try:Path('/work/too-big').write_bytes(b'x'*1048577)
 except OSError:pass
 else:raise AssertionError('filesize limit removed')
'''
 r=IsolatedRunner().run(candidate(test));assert r.passed,r.stdout+r.stderr


@pytest.mark.parametrize('kind',['keyword_filter','scoring_rule','text_transform','aggregator','threshold_alert','field_extractor'])
def test_real_isolated_six_ordinary_templates(real_containment,kind):
 from sugarcode.self_improve.codegen import synthesize_code
 from sugarcode.self_improve.testsynth import synthesize_tests
 from sugarcode.self_improve.engine import _KIND_SAMPLES
 params={'keyword_filter':{'keywords':['grant']},'scoring_rule':{'weights':{'grant':1}},'field_extractor':{'fields':{'email':r'[\w.+-]+@[\w-]+\.[\w.]+'}}}.get(kind,{})
 plan=FeaturePlan('m','demo',kind,'d','g',params)
 c=Candidate(plan,synthesize_code(plan),synthesize_tests(plan,_KIND_SAMPLES[kind]))
 r=IsolatedRunner().run(c);assert r.passed,r.stdout+r.stderr
 assert not r.output_limit_exceeded


def test_failed_containment_probe_no_capture_fallback(monkeypatch):
 from sugarcode.self_improve import isolation
 from types import SimpleNamespace
 monkeypatch.setattr(IsolatedRunner,'_command',lambda self,work:['wrapper'])
 monkeypatch.setattr(isolation.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stderr=b'refused'))
 monkeypatch.setattr(isolation,'run_bounded_process',lambda *a,**k:pytest.fail('candidate capture launched after containment refusal'))
 with pytest.raises(IsolationUnavailable):IsolatedRunner().run(candidate(''))
