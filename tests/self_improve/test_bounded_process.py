import os
from pathlib import Path
import sys
import pytest
from sugarcode.self_improve.bounded_process import run_bounded_process,OUTPUT_BYTES


def run(script,**kw):return run_bounded_process([sys.executable,'-u','-c',script],timeout_seconds=kw.pop('timeout_seconds',5),**kw)


@pytest.mark.parametrize('stream',[1,2])
@pytest.mark.parametrize('size',[OUTPUT_BYTES,OUTPUT_BYTES+1])
def test_real_exact_limit_and_one_over(stream,size):
 r=run(f'import os;os.write({stream},b"x"*{size})')
 assert r.overflow_stream==(None if size==OUTPUT_BYTES else ('stdout' if stream==1 else 'stderr'))
 assert r.max_retained_bytes<=8000 and len(r.stdout)<=4000 and len(r.stderr)<=4000
 assert (r.stdout_observed if stream==1 else r.stderr_observed)==size


@pytest.mark.parametrize('stream',[1,2])
def test_infinite_flood_bounded_storage_and_killed(stream):
 r=run(f'import os\nwhile True:os.write({stream},b"z"*65536)')
 assert r.overflow_stream==('stdout' if stream==1 else 'stderr') and r.exit_code<0
 assert r.max_retained_bytes<=8000
 assert (r.stdout_observed if stream==1 else r.stderr_observed)==OUTPUT_BYTES+1


def test_both_streams_interleaving_tail_and_invalid_utf8():
 r=run('import os\nfor i in range(100):os.write(1,b"a"*100);os.write(2,b"\\xff"*100)')
 assert r.exit_code==0 and r.overflow_stream is None
 assert r.stdout==b'a'*4000 and r.stderr==b'\xff'*4000


def test_empty_success_and_nonzero_failure():
 assert run('pass').exit_code==0
 r=run('import os;os.write(2,b"reason");raise SystemExit(3)')
 assert r.exit_code==3 and r.stderr==b'reason'


def test_deadline_includes_pipe_after_direct_child_exit(tmp_path):
 marker=tmp_path/'ready'
 script=f'''import os,time
pid=os.fork()
if pid==0:
 open({str(marker)!r},'w').write('ready')
 time.sleep(30)
else:os._exit(0)
'''
 r=run(script,timeout_seconds=.5)
 assert marker.exists() and r.timed_out
 assert r.overflow_stream is None


@pytest.mark.parametrize('timeout',[0,-1,True,float('nan'),float('inf'),'1'])
def test_invalid_timeout_no_launch(timeout,monkeypatch):
 from sugarcode.self_improve import bounded_process
 monkeypatch.setattr(bounded_process.subprocess,'Popen',lambda *a,**k:pytest.fail('launched'))
 with pytest.raises(ValueError):run('pass',timeout_seconds=timeout)


def test_cap_plus_one_read_requests_and_short_reads(monkeypatch):
 from sugarcode.self_improve import bounded_process
 original=os.read;observed=[];children=[]
 original_launch=bounded_process.subprocess.Popen
 def launch(*a,**kw):
  child=original_launch(*a,**kw);children.append(child);return child
 monkeypatch.setattr(bounded_process.subprocess,'Popen',launch)
 def short(fd,n):
  data=original(fd,min(n,7))
  if children and fd in (children[0].stdout.fileno(),children[0].stderr.fileno()):observed.append((n,len(data)))
  return data
 monkeypatch.setattr(bounded_process.os,'read',short)
 r=run('import os;os.write(1,b"x"*101)',output_bytes=100)
 assert r.overflow_stream=='stdout' and r.stdout_observed==101
 assert max(n for n,size in observed)<=101


def test_same_group_descendant_killed_on_timeout(tmp_path):
 marker=tmp_path/'pid'
 script=f'''import os,time
pid=os.fork()
if pid==0:
 open({str(marker)!r},'w').write(str(os.getpid()))
 while True:time.sleep(1)
else:
 while not os.path.exists({str(marker)!r}):time.sleep(.001)
 while True:time.sleep(1)
'''
 r=run(script,timeout_seconds=.5);assert r.timed_out
 pid=int(marker.read_text())
 status=Path(f'/proc/{pid}/status')
 import time
 from process_terminal_poll_h27 import poll_terminal_status
 observation=poll_terminal_status(status.read_text,monotonic=time.monotonic,sleep=time.sleep,timeout=2.0,expected_pid=pid,expected_name=Path(sys.executable).name)
 assert observation["terminal"], observation


def test_read_exception_kills_and_reaps_direct_child(monkeypatch,tmp_path):
 from sugarcode.self_improve import bounded_process
 children=[];original=bounded_process.subprocess.Popen
 def launch(*a,**kw):
  child=original(*a,**kw);children.append(child);return child
 monkeypatch.setattr(bounded_process.subprocess,'Popen',launch)
 original_read=os.read
 def fail(fd,n):
  if children and fd in (children[0].stdout.fileno(),children[0].stderr.fileno()):raise OSError('read refusal')
  return original_read(fd,n)
 monkeypatch.setattr(bounded_process.os,'read',fail)
 with pytest.raises(OSError):run('import os,time;os.write(1,b"ready");time.sleep(30)')
 assert children[0].returncode is not None and children[0].returncode<0


def test_overflow_issues_group_sigkill_and_reaps(monkeypatch):
 from sugarcode.self_improve import bounded_process
 sent=[];original=bounded_process.os.killpg
 def kill(pid,sig):sent.append((pid,sig));return original(pid,sig)
 monkeypatch.setattr(bounded_process.os,'killpg',kill)
 r=run('import os,time;os.write(1,b"x"*101);time.sleep(.2)',output_bytes=100)
 assert r.overflow_stream=='stdout' and r.exit_code<0
 assert len(sent)==1 and sent[0][1]==bounded_process.signal.SIGKILL
