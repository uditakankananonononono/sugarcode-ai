"""Ridge QSAR with leakage-aware validation and applicability-domain output."""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from .chemistry import descriptors, morgan_fingerprint, parse_smiles

DESC=("molecular_weight","heavy_atoms","hetero_atoms","formal_charge","hbd_heuristic",
      "hba_heuristic","rotatable_bonds_heuristic","ring_rank","aromatic_fraction",
      "graph_diameter","fraction_csp3")

@dataclass
class QSARModel:
    coefficients: np.ndarray
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    alpha: float
    n_bits: int
    radius: int
    training_smiles: tuple[str,...]
    training_target_mean: float
    target_name: str


def _features(smiles, n_bits, radius):
    rows=[]
    for s in smiles:
        d=descriptors(s)
        rows.append(np.r_[[d[k] for k in DESC],morgan_fingerprint(s,radius,n_bits)])
    return np.asarray(rows,float)


def fit_qsar(smiles, y, *, alpha=1.0, n_bits=256, radius=2, target_name="pChEMBL") -> QSARModel:
    """Fit L2-regularised linear QSAR; intercept is not penalised."""
    if len(smiles)!=len(y) or len(smiles)<3: raise ValueError("need >=3 matched compounds and outcomes")
    y=np.asarray(y,float)
    if not np.all(np.isfinite(y)): raise ValueError("outcomes must be finite")
    if alpha<0: raise ValueError("alpha must be non-negative")
    X=_features(smiles,n_bits,radius); mean=X.mean(0); scale=X.std(0); scale[scale<1e-12]=1
    Z=(X-mean)/scale; A=np.c_[np.ones(len(Z)),Z]
    penalty=np.eye(A.shape[1])*alpha; penalty[0,0]=0
    coef=np.linalg.pinv(A.T@A+penalty)@A.T@y
    return QSARModel(coef,mean,scale,float(alpha),n_bits,radius,tuple(smiles),float(y.mean()),target_name)


def _tanimoto(a,b):
    inter=float(np.dot(a,b)); union=float(a.sum()+b.sum()-inter)
    return inter/union if union else 1.0


def predict(model: QSARModel, smiles):
    """Predict with nearest-training similarity and explicit AD flag."""
    X=_features(smiles,model.n_bits,model.radius); z=(X-model.feature_mean)/model.feature_scale
    values=np.c_[np.ones(len(z)),z]@model.coefficients
    train=[morgan_fingerprint(s,model.radius,model.n_bits) for s in model.training_smiles]
    out=[]
    for s,v in zip(smiles,values):
        fp=morgan_fingerprint(s,model.radius,model.n_bits); sim=max(_tanimoto(fp,t) for t in train)
        out.append({"smiles":s,"prediction":float(v),"target":model.target_name,
                    "max_training_tanimoto":round(sim,4),
                    "applicability_domain":"inside" if sim>=0.35 else "outside",
                    "ad_threshold":0.35})
    return out


def _murcko_like_scaffold(smiles):
    """Deterministic ring/branch graph signature for grouped split.

    This is explicitly a Murcko-like grouping surrogate, not RDKit's Bemis-
    Murcko implementation. Acyclic compounds are grouped by heteroatom profile.
    """
    m=parse_smiles(smiles); deg=[0]*len(m.atoms)
    for i,j,_ in m.bonds: deg[i]+=1; deg[j]+=1
    ring=max(0,len(m.bonds)-len(m.atoms)+m.components)
    atoms="".join(sorted(a.element.lower() if a.aromatic else a.element for i,a in enumerate(m.atoms) if a.aromatic or deg[i]>2))
    hetero="".join(sorted(a.element for a in m.atoms if a.element!="C"))
    return f"r{ring}:{atoms}:{hetero}"


def _split_indices(smiles, strategy, fraction, seed, years=None):
    n=len(smiles); k=max(1,min(n-2,int(round(n*fraction))))
    if strategy=="random":
        order=np.random.default_rng(seed).permutation(n); return order[k:],order[:k]
    if strategy=="time":
        if years is None or len(years)!=n: raise ValueError("time split requires one year per compound")
        order=np.argsort(np.asarray(years)); return order[:-k],order[-k:]
    if strategy=="scaffold":
        groups={}
        for i,s in enumerate(smiles): groups.setdefault(_murcko_like_scaffold(s),[]).append(i)
        ordered=sorted(groups.values(),key=lambda g:(-len(g),g[0])); test=[]
        for g in ordered:
            if len(test)<k: test.extend(g)
        test=np.array(test,dtype=int); train=np.array([i for i in range(n) if i not in set(test)],dtype=int)
        if len(train)<3: raise ValueError("scaffold split leaves fewer than 3 training compounds; add scaffold diversity")
        return train,test
    raise ValueError("strategy must be random, scaffold, or time")


def _metrics(y,p):
    e=y-p; ss=float(np.sum((y-y.mean())**2))
    return {"n":len(y),"rmse":float(np.sqrt(np.mean(e*e))),"mae":float(np.mean(abs(e))),
            "r2":float(1-np.sum(e*e)/ss) if ss>0 else None,
            "spearman":_spearman(y,p)}

def _spearman(a,b):
    def ranks(x):
        order=np.argsort(x); r=np.empty(len(x),float); r[order]=np.arange(len(x));
        for v in np.unique(x):
            ix=np.where(x==v)[0]; r[ix]=r[ix].mean()
        return r
    ra,rb=ranks(np.asarray(a)),ranks(np.asarray(b))
    if ra.std()==0 or rb.std()==0:return None
    return float(np.corrcoef(ra,rb)[0,1])


def validate_qsar(smiles,y,*,strategy="scaffold",test_fraction=.2,seed=17,years=None,alpha=1.0,n_bits=256):
    """Run one honest holdout split and return records sufficient to audit it."""
    if len(smiles)<8: raise ValueError("validation needs at least 8 compounds")
    if not 0.1<=test_fraction<=0.5: raise ValueError("test_fraction must be 0.1..0.5")
    tr,te=_split_indices(smiles,strategy,test_fraction,seed,years)
    model=fit_qsar([smiles[i] for i in tr],[y[i] for i in tr],alpha=alpha,n_bits=n_bits)
    pred=np.array([r["prediction"] for r in predict(model,[smiles[i] for i in te])])
    return {"strategy":strategy,"seed":seed,"train_indices":tr.tolist(),"test_indices":te.tolist(),
            "metrics":_metrics(np.asarray(y,float)[te],pred),
            "performance_status":"measured_on_supplied_holdout_not_external_validation",
            "limitations":["No stereochemistry or tautomer standardisation is performed.",
              "Scaffold grouping is a documented dependency-light surrogate, not Bemis-Murcko.",
              "Prospective and independent external validation: Missing."],"model":model}
