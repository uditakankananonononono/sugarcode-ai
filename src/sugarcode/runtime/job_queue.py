"""Durable local trusted-script queue. Never claims exactly-once effects.

Single SQLite claim, cancelled pending jobs never execute. A process crash
can leave effects partly done; explicit stale reconciliation marks uncertain,
never retries. This is NOT isolation: only trusted scripts belong here.
"""
import hashlib,math,os,signal,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path

class Queue:
    def __init__(self,path):
        self.path=Path(path)
        with self._db() as db:db.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,code TEXT,sha256 TEXT,state TEXT,timeout REAL,heartbeat REAL,stdout TEXT,stderr TEXT,exit_code INTEGER)')
    def _db(self):
        db=sqlite3.connect(self.path,timeout=5);db.row_factory=sqlite3.Row;return db
    def submit(self,job_id,code,*,timeout=30):
        if not isinstance(job_id,str) or not job_id or not isinstance(code,str) or len(code.encode())>1_048_576 or type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<=0:raise ValueError('invalid bounded job')
        with self._db() as db:
            try:db.execute('INSERT INTO jobs VALUES (?,?,?,\'pending\',?,NULL,NULL,NULL,NULL)',(job_id,code,hashlib.sha256(code.encode()).hexdigest(),timeout))
            except sqlite3.IntegrityError as exc:raise ValueError('job id already exists, no retries') from exc
        return job_id
    def get(self,job_id):
        with self._db() as db:r=db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        if not r:raise KeyError(job_id)
        return dict(r)
    def cancel(self,job_id):
        with self._db() as db:return db.execute("UPDATE jobs SET state='cancelled' WHERE id=? AND state='pending'",(job_id,)).rowcount==1
    def claim(self):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE');r=db.execute("SELECT * FROM jobs WHERE state='pending' ORDER BY rowid LIMIT 1").fetchone()
            if not r:return None
            db.execute("UPDATE jobs SET state='running',heartbeat=? WHERE id=?",(time.time(),r['id']))
        return self.get(r['id'])
    def reconcile(self,*,stale_before):
        with self._db() as db:return db.execute("UPDATE jobs SET state='uncertain' WHERE state='running' AND heartbeat<?",(stale_before,)).rowcount
    def run_next(self):
        job=self.claim()
        if not job:return None
        if hashlib.sha256(job['code'].encode()).hexdigest()!=job['sha256']:
            with self._db() as db:db.execute("UPDATE jobs SET state='failed',stderr='stored script checksum mismatch' WHERE id=?",(job['id'],))
            return job['id']
        with tempfile.TemporaryDirectory(prefix='sugar-job-') as directory,tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
            script=Path(directory)/'job.py';script.write_text(job['code'])
            launcher="import resource,runpy,sys;resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576));resource.setrlimit(resource.RLIMIT_NOFILE,(64,64));runpy.run_path(sys.argv[1],run_name='__main__')"
            try:proc=subprocess.Popen([sys.executable,'-I','-c',launcher,str(script)],cwd=directory,env={'PATH':'/usr/bin','HOME':directory},stdout=out,stderr=err,start_new_session=True)
            except OSError as exc:
                with self._db() as db:db.execute("UPDATE jobs SET state='failed',stderr=? WHERE id=? AND state='running'",(type(exc).__name__,job['id']))
                return job['id']
            deadline=time.monotonic()+job['timeout'];state=None
            while proc.poll() is None:
                if time.monotonic()>=deadline:
                    try:os.killpg(proc.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    proc.wait();state='timed_out';break
                with self._db() as db:db.execute("UPDATE jobs SET heartbeat=? WHERE id=? AND state='running'",(time.time(),job['id']))
                time.sleep(min(.1,max(.001,deadline-time.monotonic())))
            state=state or ('succeeded' if proc.returncode==0 else 'failed')
            out.seek(0);err.seek(0);stdout=out.read(1_048_576).decode(errors='replace');stderr=err.read(1_048_576).decode(errors='replace')
            with self._db() as db:db.execute('UPDATE jobs SET state=?,stdout=?,stderr=?,exit_code=? WHERE id=? AND state=\'running\'',(state,stdout,stderr,proc.returncode,job['id']))
        return job['id']
