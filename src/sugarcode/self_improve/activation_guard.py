"""Optional new wrapper. Legacy engine/gate paths remain unchanged.

Local acceptance receipts and one-shot action claims; consumed effects are
never automatically retried if activation/rollback fails after claim.
"""
import hashlib,json,sqlite3,time
from pathlib import Path
from .gate import APPROVED
class ActivationGuard:
 def __init__(self,engine,database):
  self.engine=engine;self.database=Path(database)
  with self._db() as db:
   db.execute('CREATE TABLE IF NOT EXISTS evaluations(key TEXT PRIMARY KEY,code_hash TEXT,test_hash TEXT,passed INTEGER,at REAL,exit_code INTEGER)')
   db.execute('CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY,action TEXT,target TEXT,code_hash TEXT,test_hash TEXT,consumed INTEGER DEFAULT 0)')
 def _db(self):return sqlite3.connect(self.database)
 def evaluate(self,key):
  candidate=self.engine._candidates[key];result=self.engine.evaluate(key)
  with self._db() as db:db.execute('INSERT OR REPLACE INTO evaluations VALUES (?,?,?,?,?,?)',(key,candidate.code_sha256,candidate.test_sha256,int(result.passed),time.time(),result.exit_code))
  return result
 def _receipt(self,key,code_hash,test_hash):
  with self._db() as db:r=db.execute('SELECT code_hash,test_hash,passed FROM evaluations WHERE key=?',(key,)).fetchone()
  if r!=(code_hash,test_hash,1):raise PermissionError('matching actual passing evaluation required')
 def propose(self,key):
  c=self.engine._candidates[key];self._receipt(key,c.code_sha256,c.test_sha256)
  aid=self.engine.propose(key)
  with self._db() as db:db.execute('INSERT INTO approvals(id,action,target,code_hash,test_hash) VALUES (?,?,?,?,?)',(aid,'activate',key,c.code_sha256,c.test_sha256))
  return aid
 def _claim(self,aid,action,target,code_hash=None,test_hash=None):
  if self.engine.gate.decision(aid)!=APPROVED:raise PermissionError('approved human gate required')
  with self._db() as db:
   r=db.execute('SELECT action,target,code_hash,test_hash,consumed FROM approvals WHERE id=?',(aid,)).fetchone()
   if not r or r!=(action,target,code_hash,test_hash,0):raise PermissionError('wrong action/target/evidence or consumed approval')
   if db.execute('UPDATE approvals SET consumed=1 WHERE id=? AND consumed=0',(aid,)).rowcount!=1:raise PermissionError('approval claim lost')
 def activate(self,key,aid):
  p=self.engine.registry.get_proposal(key)
  code=hashlib.sha256(Path(p['code_file']).read_bytes()).hexdigest();test=hashlib.sha256(Path(p['test_file']).read_bytes()).hexdigest()
  self._receipt(key,code,test);self._claim(aid,'activate',key,code,test)
  return self.engine.activate(key,approval_id=aid)
 def request_rollback(self,name):
  aid=self.engine.request_rollback(name)
  with self._db() as db:db.execute('INSERT INTO approvals(id,action,target) VALUES (?,?,?)',(aid,'rollback',name))
  return aid
 def rollback(self,name,aid):
  self._claim(aid,'rollback',name)
  return self.engine.rollback(name,approval_id=aid)
