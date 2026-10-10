from pathlib import Path
import pytest
from sugarcode.self_improve.plans import Candidate,FeaturePlan
from sugarcode.self_improve.sandbox import SandboxRunner,SandboxResult
from sugarcode.self_improve.engine import SelfImprovementEngine


def candidate():
 return Candidate(FeaturePlan('m','demo','keyword_filter','d','g'),
   'def run(items,params=None):return items',
   'import os\ndef test_flood():\n os.write(2,b"x"*(1048576+100000))\n assert False\n')


def test_real_pytest_flood_refuses_cleanup_and_reason(tmp_path):
 result=SandboxRunner(timeout_seconds=10).run(candidate())
 assert not result.passed and result.output_limit_exceeded
 assert result.output_limit_stream in ('stdout','stderr')
 assert 'output byte limit exceeded' in result.stderr
 assert len(result.stdout.encode())<=12000 and len(result.stderr.encode())<=12000
 assert result.workdir==''


def test_output_result_propagates_engine_ledger(tmp_path):
 e=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path)
 c=candidate();e._candidates['k']=c;result=e.evaluate('k')
 assert result.output_limit_exceeded and not result.passed
 row=next(x for x in e.ledger() if x['event']=='feature_evaluated')
 assert row['output_limit_exceeded'] and row['output_limit_stream']==result.output_limit_stream
 assert e.registry.proposals()=={}


def test_additive_fields_preserve_old_positional_result():
 r=SandboxResult(True,0,'out','err',.1,False,'oldpath')
 assert r.workdir=='oldpath' and not r.output_limit_exceeded and r.output_limit_stream is None


def test_keep_workspace_and_timeout_contract():
 from dataclasses import replace
 import shutil
 c=replace(candidate(),test_code='import time\ndef test_wait():time.sleep(30)')
 r=SandboxRunner(timeout_seconds=.5,keep_workdirs=True).run(c)
 assert not r.passed and r.timed_out and r.exit_code==-1
 assert not r.output_limit_exceeded and 'timed out' in r.stderr
 assert Path(r.workdir).exists();shutil.rmtree(r.workdir)
