import sys,os
from pathlib import Path
import pytest
from sugarcode.self_improve.plans import Candidate,FeaturePlan

def candidate(test):
 return Candidate(FeaturePlan('tools','identity','text_transform','identity','identity'), 'def run(items,params=None): return items\n',test)

def test_real_containment(tmp_path, real_containment):
 from sugarcode.self_improve.isolation import IsolatedRunner
 secret=tmp_path/'owner-secret';secret.write_text('PRIVATE CANARY')
 test=f'''import os,socket
from pathlib import Path
from feature import run
def test_boundaries():
 assert not Path({str(secret)!r}).exists()
 assert not Path('/home/sandbox/projects').exists()
 assert os.readlink('/proc/self/ns/net')!={os.readlink('/proc/self/ns/net')!r}
 assert os.readlink('/proc/self/ns/pid')!={os.readlink('/proc/self/ns/pid')!r}
 assert os.getenv('SUGARCODE_SECRET') is None
 assert run(['actual'])==['actual']
 Path('/work/scratch').write_text('permitted')
 try: Path('/usr/forbidden').write_text('no')
 except OSError: pass
 else: raise AssertionError('runtime writable')
 s=socket.socket();s.settimeout(.2)
 try: s.connect(('1.1.1.1',443))
 except OSError: pass
 else: raise AssertionError('network allowed')
'''
 result=IsolatedRunner().run(candidate(test))
 assert result.passed, result.stderr+result.stdout
 assert secret.read_text()=='PRIVATE CANARY'
 assert not (tmp_path/'scratch').exists()

def test_unavailable_refuses(tmp_path):
 from sugarcode.self_improve.isolation import IsolatedRunner,IsolationUnavailable
 with pytest.raises(IsolationUnavailable):IsolatedRunner(bwrap='/nonexistent').run(candidate(''))

def test_timeout_and_failure(real_containment):
 from sugarcode.self_improve.isolation import IsolatedRunner
 result=IsolatedRunner(timeout_seconds=1).run(candidate('import time\ntime.sleep(10)'))
 assert not result.passed and result.timed_out
 result=IsolatedRunner().run(candidate('def test_bad(): assert False'))
 assert not result.passed and not result.timed_out
