import json
from pathlib import Path
import pytest
from sugarcode.self_improve.registry import FeatureRegistry

def test_real_isolated_dispatch_and_private_path(tmp_path, real_containment):
 from sugarcode.self_improve.isolated_dispatch import dispatch
 r=FeatureRegistry('tools',tmp_path/'state');secret=tmp_path/'secret';secret.write_text('OWNER CANARY')
 code=f'''def run(items,params=None):
 from pathlib import Path
 import socket
 assert not Path({str(secret)!r}).exists()
 s=socket.socket();s.settimeout(.1)
 try:s.connect(('1.1.1.1',443))
 except OSError:pass
 else:raise RuntimeError('network accessible')
 return {{'reversed':list(reversed(items)),'parameter':params['x']}}
'''
 r.save_proposal('reverse',name='reverse',kind='text_transform',code=code,test_code='',gap_signature='reverse');r.activate('reverse',approval_id='local-test')
 assert dispatch(r,'reverse',['a','b'],{'x':2})=={'reversed':['b','a'],'parameter':2}
 assert secret.read_text()=='OWNER CANARY'

def test_tamper_refused(tmp_path):
 from sugarcode.self_improve.isolated_dispatch import dispatch
 r=FeatureRegistry('tools',tmp_path);r.save_proposal('x',name='x',kind='text_transform',code='def run(items,params=None): return items',test_code='',gap_signature='x');entry=r.activate('x',approval_id='test')
 Path(entry['file']).write_text('tamper')
 with pytest.raises(ValueError):dispatch(r,'x',[])

def test_timeout_refused(tmp_path, real_containment):
 from sugarcode.self_improve.isolated_dispatch import dispatch
 r=FeatureRegistry('tools',tmp_path);r.save_proposal('x',name='x',kind='text_transform',code='def run(items,params=None):\n import time\n time.sleep(10)',test_code='',gap_signature='x');r.activate('x',approval_id='test')
 with pytest.raises(TimeoutError):dispatch(r,'x',[],timeout_seconds=.5)

@pytest.mark.parametrize('timeout',[float('nan'),float('inf'),True,'bad'])
def test_invalid_timeout_rejected_before_registry_access(timeout):
 from sugarcode.self_improve.isolated_dispatch import dispatch
 class NeverAccess:
  def _active_entry(self,name):raise AssertionError('validation must precede access')
 with pytest.raises(ValueError):dispatch(NeverAccess(),'x',[],timeout_seconds=timeout)
