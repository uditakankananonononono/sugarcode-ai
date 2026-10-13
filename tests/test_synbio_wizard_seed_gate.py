import inspect
import os
import subprocess
import sys
import numpy as np
import pytest
import sugarcode.modules.synbio_wizard.seed_gate as module
NAMES = ['gillespie_expression', 'uncertainty_distribution']


def required(fn):
    args=[]; kwargs={}
    for p in inspect.signature(fn).parameters.values():
        if p.default is inspect.Parameter.empty:
            if p.kind is inspect.Parameter.KEYWORD_ONLY: kwargs[p.name]=None
            else: args.append(None)
    return args,kwargs


@pytest.mark.parametrize('name',NAMES)
def test_refusal_before_dispatch(name,monkeypatch):
    fn=getattr(module,name); args,kwargs=required(fn)
    def forbidden(*a,**k): raise AssertionError('legacy dispatch before seed refusal')
    monkeypatch.setattr(module.core,name,forbidden)
    for seed in (True,np.bool_(True),-1,2**63):
        error=TypeError if isinstance(seed,(bool,np.bool_)) else ValueError
        message='^seed must be an integer$' if error is TypeError else '^seed must be between 0 and 9223372036854775807$'
        with pytest.raises(error,match=message):
            fn(*args,**kwargs,seed=seed)


@pytest.mark.parametrize('name',NAMES)
def test_edges_and_dispatch(name,monkeypatch):
    fn=getattr(module,name); args,kwargs=required(fn)
    signature=inspect.signature(getattr(module.core,name))
    def capture(*a,**k): return signature.bind(*a,**k).arguments
    monkeypatch.setattr(module.core,name,capture)
    for seed in (0,2**63-1,np.int64(0),np.int64(2**63-1),np.uint64(2**63-1)):
        result=fn(*args,**kwargs,seed=seed)
        assert result['seed']==int(seed)
        assert type(result['seed']) is int
    default=inspect.signature(fn).parameters['seed'].default
    assert fn(*args,**kwargs)['seed']==default


def test_deep_list_subprocess():
    code="""import inspect
import sugarcode.modules.synbio_wizard.seed_gate as m
seed=0
for _ in range(100000): seed=[seed]
for name in ['gillespie_expression', 'uncertainty_distribution']:
    fn=getattr(m,name)
    args=[]; kwargs={}
    for p in inspect.signature(fn).parameters.values():
        if p.default is inspect.Parameter.empty:
            if p.kind is inspect.Parameter.KEYWORD_ONLY: kwargs[p.name]=None
            else: args.append(None)
    def forbidden(*a,**k): raise AssertionError('legacy dispatch before seed refusal')
    setattr(m.core,name,forbidden)
    try: fn(*args,**kwargs,seed=seed)
    except TypeError as exc:
        assert str(exc)=='seed must be an integer'
    else: raise AssertionError('deep list accepted')
print('deep-list refused')
"""
    p=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=15,env={**os.environ,'PYTHONPATH':'src'})
    assert p.returncode==0,(p.returncode,p.stderr[-1000:])
    assert 'deep-list refused' in p.stdout
