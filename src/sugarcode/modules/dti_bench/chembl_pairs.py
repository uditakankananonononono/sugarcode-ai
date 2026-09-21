"""Module-local ChEMBL target-pair retrieval with cache/throttle/offline control."""
from __future__ import annotations
import hashlib,json,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
class ChEMBLPairUnavailable(RuntimeError): pass
class ChEMBLPairClient:
    BASE="https://www.ebi.ac.uk/chembl/api/data"
    def __init__(self,cache_dir=None,*,offline=False,min_interval=.35,timeout=25):
        self.cache=Path(cache_dir or Path.home()/".sugarcode_cache"/"dti_bench_chembl"); self.offline=offline; self.min_interval=min_interval; self.timeout=timeout; self._last=0.
    def _get(self,path,params=None):
        url=f"{self.BASE}/{path}"+("?"+urllib.parse.urlencode(params or {},doseq=True) if params else ""); f=self.cache/(hashlib.sha256(url.encode()).hexdigest()+".json"); self.cache.mkdir(parents=True,exist_ok=True)
        if f.exists(): return json.loads(f.read_text())
        if self.offline: raise ChEMBLPairUnavailable(f"offline cache miss: {url}")
        wait=self.min_interval-(time.monotonic()-self._last)
        if wait>0: time.sleep(wait)
        last=None
        for delay in (0,1,2):
            if delay: time.sleep(delay)
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"sugarcode-ai-dti-bench/1.0"})
                with urllib.request.urlopen(req,timeout=self.timeout) as r: raw=r.read()
                data=json.loads(raw); f.write_bytes(raw); self._last=time.monotonic(); return data
            except (urllib.error.URLError,TimeoutError,json.JSONDecodeError) as e: last=e
        raise ChEMBLPairUnavailable(f"ChEMBL request failed after 3 attempts: {last}")
    def target_sequence(self,target_id):
        target=self._get(f"target/{target_id}.json"); comps=target.get("target_components") or []
        seqs=[]
        for c in comps:
            seq=c.get("target_component_sequence") or c.get("sequence")
            if seq: seqs.append(seq)
        if not seqs: raise ChEMBLPairUnavailable(f"target {target_id} has no protein sequence in ChEMBL")
        if len(seqs)>1: raise ChEMBLPairUnavailable(f"target {target_id} is multi-component; explicit component policy required")
        return seqs[0]
    def pairs(self,target_ids,*,per_target=200,standard_types=("IC50","Ki","Kd")):
        """Retrieve exact single-protein pChEMBL pairs, median aggregated.

        Returns source IDs, assay metadata, years and exclusion counts. Multi-
        component targets fail closed because assigning one sequence would be
        scientifically ambiguous.
        """
        rows=[]; excluded={"non_exact":0,"missing_value":0,"missing_structure":0}
        for tid in target_ids:
            seq=self.target_sequence(tid)
            page=self._get("activity.json",{"target_chembl_id":tid,"standard_type__in":",".join(standard_types),"pchembl_value__isnull":"false","limit":min(per_target,1000)})
            acts=page.get("activities",[])[:per_target]; ids=sorted({a.get("molecule_chembl_id") for a in acts if a.get("molecule_chembl_id")}); structures={}
            for start in range(0,len(ids),100):
                mols=self._get("molecule.json",{"molecule_chembl_id__in":",".join(ids[start:start+100]),"limit":100})
                for m in mols.get("molecules",[]): structures[m.get("molecule_chembl_id")]=(m.get("molecule_structures") or {}).get("canonical_smiles")
            grouped={}
            for a in acts:
                if str(a.get("standard_relation") or "").strip()!="=": excluded["non_exact"]+=1; continue
                try: value=float(a["pchembl_value"])
                except (KeyError,TypeError,ValueError): excluded["missing_value"]+=1; continue
                smi=structures.get(a.get("molecule_chembl_id"))
                if not smi: excluded["missing_structure"]+=1; continue
                grouped.setdefault(smi,[]).append((value,a))
            for smi,items in grouped.items():
                vals=sorted(v for v,_ in items); n=len(vals); med=vals[n//2] if n%2 else sum(vals[n//2-1:n//2+1])/2
                years=[int(a["document_year"]) for _,a in items if a.get("document_year")]
                rows.append({"smiles":smi,"sequence":seq,"target_chembl_id":tid,"pchembl_median":med,"replicate_count":n,"year":max(years) if years else None,
                  "molecule_chembl_ids":sorted({a.get("molecule_chembl_id") for _,a in items}),"assay_chembl_ids":sorted({a.get("assay_chembl_id") for _,a in items if a.get("assay_chembl_id")})})
        return {"records":rows,"excluded":excluded,"source":"ChEMBL REST API live-or-SHA256-URL-cache","limitations":["Assay confidence and target-mapping review remains required.","Prospective validation: Missing."]}
