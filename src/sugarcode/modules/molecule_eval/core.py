"""Generation metrics that avoid unsupported synthetic/clinical claims."""
from __future__ import annotations
import math
import numpy as np
from sugarcode.modules.qsar_bench.chemistry import parse_smiles,descriptors,morgan_fingerprint


def _tan(a,b):
    x=float(a@b); u=float(a.sum()+b.sum()-x); return x/u if u else 1.0

def _canonical_graph_key(smiles):
    """Order-invariant graph digest for deduplication, not canonical SMILES."""
    import hashlib
    m=smiles if hasattr(smiles,"atoms") else parse_smiles(smiles); labels=[f"{a.element}:{int(a.aromatic)}:{a.charge}" for a in m.atoms]
    for _ in range(4):
        new=[]
        for i in range(len(m.atoms)):
            nei=[]
            for a,b,o in m.bonds:
                if a==i: nei.append(f"{o}:{labels[b]}")
                elif b==i: nei.append(f"{o}:{labels[a]}")
            new.append(hashlib.sha256((labels[i]+"|"+";".join(sorted(nei))).encode()).hexdigest())
        labels=new
    edges=sorted(f"{o}:{min(labels[a],labels[b])}:{max(labels[a],labels[b])}" for a,b,o in m.bonds)
    return hashlib.sha256((";".join(sorted(labels))+"|"+";".join(edges)).encode()).hexdigest()


def _iter_pairs(n,max_pairs,rng):
    """Yield (i, j), i < j, in row-major order: all pairs if there are at most
    ``max_pairs``, else a seeded sample of ``max_pairs``. The full pair list is
    never built, so memory is O(n + max_pairs)."""
    total=n*(n-1)//2
    if total<=max_pairs:
        for i in range(n):
            for j in range(i+1,n): yield i,j
        return
    take=np.sort(rng.choice(total,max_pairs,replace=False))  # same draw as the old list-based code
    starts=np.array([i*(2*n-i-1)//2 for i in range(n)],dtype=np.int64)  # first linear index of row i
    rows=np.searchsorted(starts,take,side="right")-1
    for k,i in zip(take.tolist(),rows.tolist()): yield i,i+1+(k-int(starts[i]))


def _ci(values, statistic, seed, samples=400):
    if not values:return {"estimate":None,"ci95":[None,None]}
    rng=np.random.default_rng(seed); arr=np.asarray(values)
    est=float(statistic(arr)); boots=[]
    for _ in range(samples): boots.append(float(statistic(arr[rng.integers(0,len(arr),len(arr))])))
    return {"estimate":est,"ci95":[float(np.quantile(boots,.025)),float(np.quantile(boots,.975))]}


def evaluate_library(smiles,*,reference_smiles=None,n_bits=256,seed=29,max_pairs=10000):
    """Evaluate parser acceptance, graph-key uniqueness, diversity and reference novelty.

    "valid" means the qsar_bench parser accepted the string: tokens, brackets and
    bond-symbol placement and maximum valence are checked, aromatic-ring
    kekulizability is not ("c1cccc1" counts as valid). Pair sampling is deterministic for a fixed seed and at most
    max_pairs pairs are scored. Novelty is fingerprint novelty,
    reported as 1 minus maximum reference Tanimoto; it does not prove chemical
    novelty or patent freedom-to-operate.
    """
    if not smiles: raise ValueError("library is empty")
    valid=[]; invalid=[]; keys=[]; stereo_ignored=0
    for i,s in enumerate(smiles):
        try:
            mol=parse_smiles(s); keys.append(_canonical_graph_key(mol)); valid.append((i,s)); stereo_ignored+=bool(mol.ignored)
        except (ValueError,TypeError) as e: invalid.append({"index":i,"smiles":s,"reason":str(e)})
    unique={}
    for (i,s),k in zip(valid,keys): unique.setdefault(k,(i,s))
    us=[x[1] for x in unique.values()]; fps=[morgan_fingerprint(s,n_bits=n_bits) for s in us]
    rng=np.random.default_rng(seed); distances=[1-_tan(fps[i],fps[j]) for i,j in _iter_pairs(len(fps),max_pairs,rng)]
    novelty=[]
    if reference_smiles:
        refs=[]
        for s in reference_smiles:
            try: refs.append(morgan_fingerprint(s,n_bits=n_bits))
            except (ValueError,TypeError): pass
        if refs:
            novelty=[1-max(_tan(fp,r) for r in refs) for fp in fps]
    props=[descriptors(s) for s in us]
    summaries={}
    for name in ("molecular_weight","hetero_atoms","hbd_heuristic","hba_heuristic","ring_rank","aromatic_fraction","fraction_csp3"):
        vals=[p[name] for p in props]
        summaries[name]={"mean":float(np.mean(vals)),"median":float(np.median(vals)),"std":float(np.std(vals)),"min":float(np.min(vals)),"max":float(np.max(vals))} if vals else None
    return {"input_count":len(smiles),"valid_count":len(valid),"invalid_count":len(invalid),"valid_fraction":len(valid)/len(smiles),
      "stereo_ignored_count":stereo_ignored,"unique_graph_count":len(us),"unique_fraction_among_valid":len(us)/len(valid) if valid else 0.,"invalid_records":invalid,
      "internal_diversity":_ci(distances,np.mean,seed),"fingerprint_novelty_to_reference":_ci(novelty,np.mean,seed+1) if reference_smiles else None,
      "property_summary":summaries,"records":[{"smiles":s,"graph_key":k,"descriptors":d} for (k,(i,s)),d in zip(unique.items(),props)],
      "methods":{"fingerprint":"Morgan-style radius 2 hashed circular fingerprint","n_bits":n_bits,"pair_count":len(distances),"max_pairs":max_pairs,"bootstrap_samples":400,"seed":seed},
      "limitations":["Graph keys are molecular-graph digests, not canonical SMILES or tautomer normalization.","Stereochemistry (@, /, \\) is ignored in graph keys, diversity and novelty; stereo_ignored_count counts the valid inputs that carried it.","Fingerprint novelty is not patent novelty or freedom-to-operate.","Synthetic accessibility and experimental validation: Missing."]}


def _js_divergence(a,b,bins=20):
    lo=min(float(np.min(a)),float(np.min(b))); hi=max(float(np.max(a)),float(np.max(b)))
    if lo==hi:return 0.
    p,_=np.histogram(a,bins=bins,range=(lo,hi)); q,_=np.histogram(b,bins=bins,range=(lo,hi)); p=(p+.5)/(p.sum()+.5*bins); q=(q+.5)/(q.sum()+.5*bins); m=(p+q)/2
    return float((np.sum(p*np.log2(p/m))+np.sum(q*np.log2(q/m)))/2)


def compare_libraries(generated,reference,*,n_bits=256,seed=29):
    """Compare generated/reference property distributions with Jensen-Shannon divergence."""
    g=evaluate_library(generated,reference_smiles=reference,n_bits=n_bits,seed=seed); r=evaluate_library(reference,n_bits=n_bits,seed=seed)
    gp=[x["descriptors"] for x in g["records"]]; rp=[x["descriptors"] for x in r["records"]]
    if not gp or not rp: raise ValueError("both libraries need at least one valid molecule")
    js={k:_js_divergence(np.array([x[k] for x in gp]),np.array([x[k] for x in rp])) for k in ("molecular_weight","hetero_atoms","hbd_heuristic","hba_heuristic","ring_rank","aromatic_fraction","fraction_csp3")}
    return {"generated":g,"reference":r,"property_js_divergence_bits":js,"mean_property_js_divergence_bits":float(np.mean(list(js.values()))),
      "interpretation":"0 means matching binned distributions; larger values mean greater separation. Values depend on sample and binning."}


def pareto_front(records,objectives):
    """Return nondominated record indices for named numeric objectives.

    ``objectives`` maps field names to 'min' or 'max'. Missing/non-finite values
    fail closed. Equal records are both retained.
    """
    if not objectives or any(v not in {"min","max"} for v in objectives.values()): raise ValueError("objectives must map fields to min/max")
    vals=[]
    for i,r in enumerate(records):
        row=[]
        for k,direction in objectives.items():
            try:v=float(r[k])
            except (KeyError,TypeError,ValueError): raise ValueError(f"record {i} lacks numeric objective {k}")
            if not math.isfinite(v): raise ValueError(f"record {i} has non-finite objective {k}")
            row.append(v if direction=="max" else -v)
        vals.append(row)
    front=[]
    for i,a in enumerate(vals):
        dominated=any(j!=i and all(x>=y for x,y in zip(b,a)) and any(x>y for x,y in zip(b,a)) for j,b in enumerate(vals))
        if not dominated: front.append(i)
    return front
