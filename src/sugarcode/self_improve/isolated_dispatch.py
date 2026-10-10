"""Opt-in real isolated feature execution with JSON-only result protocol.

Legacy in-process dispatch unchanged. Reads/hash-checks once, executes copied
bytes in disposable namespace, no source reload TOCTOU. Does not close gate,
registry transaction/crash/revoke races; no host effect authorization claim.
"""
import hashlib,json,math,os,signal,subprocess,sys,tempfile
from pathlib import Path
from .isolation import IsolatedRunner,IsolationUnavailable
from .isolated_result_codec import decode_child_result

_LAUNCHER='''import resource,json,sys,importlib.util,contextlib
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
payload=json.load(open('/work/input.json'))
with open('/work/noise.log','w') as log,contextlib.redirect_stdout(log):
 spec=importlib.util.spec_from_file_location('feature','/work/feature.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 result=module.run(payload['items'],payload['params'])
print(json.dumps({'result':result},allow_nan=False))
'''

def dispatch(registry,name,items,params=None,*,timeout_seconds=10):
    if not isinstance(items,list) or (params is not None and not isinstance(params,dict)):raise ValueError('JSON list/object required')
    if type(timeout_seconds) not in (int,float) or not math.isfinite(timeout_seconds) or timeout_seconds<=0:raise ValueError('positive timeout required')
    entry=registry._active_entry(name);path=registry._contained(Path(entry['file']))
    code=path.read_bytes()
    if hashlib.sha256(code).hexdigest()!=entry['sha256']:raise ValueError('active feature checksum mismatch')
    encoded=json.dumps({'items':items,'params':params or {}},allow_nan=False).encode()
    if len(code)>1_048_576 or len(encoded)>1_048_576:raise ValueError('input/code cap exceeded')
    runner=IsolatedRunner(timeout_seconds=timeout_seconds)
    with tempfile.TemporaryDirectory(prefix='sugar-dispatch-') as directory:
        work=Path(directory);(work/'feature.py').write_bytes(code);(work/'input.json').write_bytes(encoded)
        cmd=runner._command(work)
        try:probe=subprocess.run(cmd+[sys.executable,'-I','-c','pass'],capture_output=True,timeout=5)
        except (OSError,subprocess.TimeoutExpired) as exc:raise IsolationUnavailable('containment probe failed') from exc
        if probe.returncode:raise IsolationUnavailable('containment unavailable')
        with tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
            child=subprocess.Popen(cmd+[sys.executable,'-I','-c',_LAUNCHER],stdout=stdout,stderr=stderr,start_new_session=True)
            try:child.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                child.wait();raise TimeoutError('isolated dispatch timeout')
            stdout.seek(0);raw=stdout.read(1_048_577)
            if child.returncode or len(raw)>1_048_576:raise RuntimeError('isolated feature failed or result exceeded cap')
            return decode_child_result(raw)
