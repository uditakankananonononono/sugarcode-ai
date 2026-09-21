"""Module-local ChEMBL reference-library client."""
from __future__ import annotations
import hashlib,json,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
class ChEMBLReferenceUnavailable(RuntimeError): pass
class ChEMBLReferenceClient:
 BASE="https://www.ebi.ac.uk/chembl/api/data"
 def __init__(self,cache_dir=None,*,offline=False,min_interval=.35,timeout=25):
  self.cache=Path(cache_dir or Path.home()/".sugarcode_cache"/"molecule_eval_chembl"); self.offline=offline; self.min_interval=min_interval; self.timeout=timeout; self._last=0.
 def _get(self,path,params):
  url=f"{self.BASE}/{path}?"+urllib.parse.urlencode(params); f=self.cache/(hashlib.sha256(url.encode()).hexdigest()+".json"); self.cache.mkdir(parents=True,exist_ok=True)
  if f.exists(): return json.loads(f.read_text())
  if self.offline: raise ChEMBLReferenceUnavailable(f"offline cache miss: {url}")
  wait=self.min_interval-(time.monotonic()-self._last)
  if wait>0:time.sleep(wait)
  last=None
  for delay in (0,1,2):
   if delay:time.sleep(delay)
   try:
    req=urllib.request.Request(url,headers={"User-Agent":"sugarcode-ai-molecule-eval/1.0"})
    with urllib.request.urlopen(req,timeout=self.timeout) as r:raw=r.read()
    data=json.loads(raw); f.write_bytes(raw); self._last=time.monotonic(); return data
   except (urllib.error.URLError,TimeoutError,json.JSONDecodeError) as e:last=e
  raise ChEMBLReferenceUnavailable(f"ChEMBL request failed after 3 attempts: {last}")
 def approved_reference(self,*,limit=1000):
  """Return canonical SMILES for ChEMBL phase-4 molecules and exclusions."""
  data=self._get("molecule.json",{"max_phase":4,"limit":min(limit,1000)}); out=[]; missing=0
  for m in data.get("molecules",[])[:limit]:
   s=(m.get("molecule_structures") or {}).get("canonical_smiles")
   if s:out.append({"chembl_id":m.get("molecule_chembl_id"),"smiles":s,"pref_name":m.get("pref_name")})
   else:missing+=1
  return {"records":out,"excluded_missing_structure":missing,"source":"ChEMBL REST API max_phase=4 live-or-SHA256-URL-cache","limitations":["max_phase=4 is a ChEMBL annotation, not current market status.","Patent freedom-to-operate: Missing."]}
