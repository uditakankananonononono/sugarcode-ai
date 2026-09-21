"""Module-local ChEMBL dataset client with cache, throttle and offline mode."""
from __future__ import annotations
import hashlib,json,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path

class ChEMBLUnavailable(RuntimeError): pass

class ChEMBLQSARClient:
    BASE="https://www.ebi.ac.uk/chembl/api/data"
    def __init__(self, cache_dir=None, *, offline=False, min_interval=.35, timeout=25):
        self.cache=Path(cache_dir or Path.home()/".sugarcode_cache"/"qsar_bench_chembl")
        self.offline=offline; self.min_interval=min_interval; self.timeout=timeout; self._last=0.0
    def _get(self,path,params=None):
        query=urllib.parse.urlencode(params or {},doseq=True); url=f"{self.BASE}/{path}"+(f"?{query}" if query else "")
        key=hashlib.sha256(url.encode()).hexdigest(); file=self.cache/f"{key}.json"; self.cache.mkdir(parents=True,exist_ok=True)
        if file.exists(): return json.loads(file.read_text())
        if self.offline: raise ChEMBLUnavailable(f"offline cache miss: {url}")
        wait=self.min_interval-(time.monotonic()-self._last)
        if wait>0: time.sleep(wait)
        last=None
        for delay in (0,1,2):
            if delay: time.sleep(delay)
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"sugarcode-ai-qsar-bench/1.0"})
                with urllib.request.urlopen(req,timeout=self.timeout) as r: raw=r.read()
                data=json.loads(raw); file.write_bytes(raw); self._last=time.monotonic(); return data
            except (urllib.error.URLError,TimeoutError,json.JSONDecodeError) as e: last=e
        raise ChEMBLUnavailable(f"ChEMBL request failed after 3 attempts: {last}")
    def target_dataset(self,target_chembl_id,*,limit=1000,standard_types=("IC50","Ki","Kd")):
        """Fetch equality-qualified binding data with structures and pChEMBL.

        Duplicates are aggregated by median pChEMBL per canonical SMILES and
        years are retained for temporal validation. Records lacking pChEMBL,
        canonical SMILES, an exact '=' relation, or a requested type are
        counted and excluded rather than imputed.
        """
        if not target_chembl_id.startswith("CHEMBL"): raise ValueError("target ID must start CHEMBL")
        page=self._get("activity.json",{"target_chembl_id":target_chembl_id,"standard_type__in":",".join(standard_types),
          "pchembl_value__isnull":"false","limit":min(limit,1000)})
        acts=page.get("activities",[])[:limit]; ids=sorted({a.get("molecule_chembl_id") for a in acts if a.get("molecule_chembl_id")})
        structures={}
        for start in range(0,len(ids),100):
            data=self._get("molecule.json",{"molecule_chembl_id__in":",".join(ids[start:start+100]),"limit":100})
            for m in data.get("molecules",[]): structures[m.get("molecule_chembl_id")]=(m.get("molecule_structures") or {}).get("canonical_smiles")
        grouped={}; excluded={"non_exact_relation":0,"missing_pchembl":0,"missing_structure":0,"invalid_value":0}
        for a in acts:
            if str(a.get("standard_relation") or "").strip()!="=": excluded["non_exact_relation"]+=1; continue
            if a.get("pchembl_value") is None: excluded["missing_pchembl"]+=1; continue
            smi=structures.get(a.get("molecule_chembl_id"))
            if not smi: excluded["missing_structure"]+=1; continue
            try: val=float(a["pchembl_value"])
            except (TypeError,ValueError): excluded["invalid_value"]+=1; continue
            grouped.setdefault(smi,[]).append((val,a.get("document_year"),a.get("molecule_chembl_id")))
        rows=[]
        for smi,items in grouped.items():
            vals=sorted(x[0] for x in items); n=len(vals); median=vals[n//2] if n%2 else (vals[n//2-1]+vals[n//2])/2
            years=[int(x[1]) for x in items if x[1]]
            rows.append({"smiles":smi,"pchembl_median":median,"replicate_count":n,"year":max(years) if years else None,
              "molecule_chembl_ids":sorted({x[2] for x in items})})
        rows.sort(key=lambda r:(r["year"] is None,r["year"] or 0,r["smiles"]))
        return {"target_chembl_id":target_chembl_id,"records":rows,"excluded":excluded,
          "source":"ChEMBL REST API live-or-content-addressed-cache","endpoint_definition":"exact-relation pChEMBL for "+",".join(standard_types),
          "limitations":["Assay confidence and target mapping must be reviewed for the intended study.","External prospective validation: Missing."]}
