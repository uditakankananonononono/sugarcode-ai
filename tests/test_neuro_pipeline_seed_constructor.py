import os
import subprocess
import sys
import numpy as np
import pytest
from sugarcode.modules.neuro_pipeline import seed_gate as module


def test_refusal_before_constructor(monkeypatch):
    def forbidden(*a,**k): raise AssertionError('constructor reached')
    monkeypatch.setattr(module.core.MLP,'__init__',forbidden)
    for seed in (True,np.bool_(True),-1,2**63):
        error=TypeError if isinstance(seed,(bool,np.bool_)) else ValueError
        message='^seed must be an integer$' if error is TypeError else '^seed must be between 0 and 9223372036854775807$'
        with pytest.raises(error,match=message): module.MLP(3,2,1,seed)


def test_real_constructor_edges():
    for seed in (0,2**63-1,np.int64(0),np.int64(2**63-1)):
        m=module.MLP(3,2,1,seed)
        expected=module.core.MLP(3,2,1,int(seed))
        assert np.array_equal(m.W1,expected.W1)
        assert np.array_equal(m.W2,expected.W2)
    assert np.array_equal(module.MLP(3,2,1).W1,module.core.MLP(3,2,1,42).W1)


def test_deep_list_subprocess():
    code="""from sugarcode.modules.neuro_pipeline import seed_gate as m
seed=0
for _ in range(100000): seed=[seed]
def forbidden(*a,**k): raise AssertionError('constructor reached')
m.core.MLP.__init__=forbidden
try: m.MLP(3,2,1,seed)
except TypeError as exc: assert str(exc)=='seed must be an integer'
else: raise AssertionError('deep seed accepted')
print('deep-list refused')
"""
    p=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=15,env={**os.environ,'PYTHONPATH':'src'})
    assert p.returncode==0,(p.returncode,p.stderr[-1000:])
    assert 'deep-list refused' in p.stdout
