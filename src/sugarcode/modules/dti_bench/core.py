"""Proteochemometric ridge baseline with cold-start validation.

The model is target-conditioned: ligand fingerprints are combined with protein
composition, grouped dipeptides and explicit ligand-protein outer interactions.
It is an auditable baseline, not a docking or clinical efficacy model.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import numpy as np
from sugarcode.modules.qsar_bench.chemistry import descriptors,morgan_fingerprint

AA="ACDEFGHIKLMNPQRSTVWY"
GROUPS={"hydrophobic":set("AVILMFWY"),"polar":set("STNQCH"),"positive":set("KRH"),"negative":set("DE"),"special":set("GP")}
GN=tuple(GROUPS)


def protein_features(sequence: str) -> np.ndarray:
    """Composition and grouped-dipeptide protein representation (50 values)."""
    seq="".join(sequence.upper().split())
    if len(seq)<10: raise ValueError("protein sequence must contain at least 10 residues")
    bad=set(seq)-set(AA)
    if bad: raise ValueError(f"non-canonical amino acids: {''.join(sorted(bad))}")
    comp=[seq.count(a)/len(seq) for a in AA]
    assignment={a:i for i,g in enumerate(GN) for a in GROUPS[g]}
    di=np.zeros((5,5),float)
    for a,b in zip(seq,seq[1:]): di[assignment[a],assignment[b]]+=1
    di/=max(1,len(seq)-1)
    phys=[len(seq)/1000.0,sum(a in GROUPS["hydrophobic"] for a in seq)/len(seq),
          sum(a in GROUPS["positive"] for a in seq)/len(seq),sum(a in GROUPS["negative"] for a in seq)/len(seq),
          (sum(a in GROUPS["positive"] for a in seq)-sum(a in GROUPS["negative"] for a in seq))/len(seq)]
    return np.r_[comp,di.ravel(),phys]


def pair_features(smiles: str, sequence: str, *, ligand_bits=128, interaction_dims=16) -> np.ndarray:
    """Concatenate ligand, target and explicit low-dimensional interaction terms."""
    if interaction_dims<1 or interaction_dims>min(ligand_bits,50): raise ValueError("invalid interaction_dims")
    lig=morgan_fingerprint(smiles,n_bits=ligand_bits,radius=2); prot=protein_features(sequence)
    d=descriptors(smiles); continuous=np.array([d[k] for k in ("molecular_weight","hetero_atoms","hbd_heuristic","hba_heuristic","ring_rank","aromatic_fraction")])
    interactions=np.outer(lig[:interaction_dims],prot[:interaction_dims]).ravel()
    return np.r_[continuous,lig,prot,interactions]

@dataclass
class DTIModel:
    coefficients: np.ndarray
    mean: np.ndarray
    scale: np.ndarray
    alpha: float
    ligand_bits: int
    interaction_dims: int
    training_smiles: tuple[str,...]
    training_sequences: tuple[str,...]
    target_name: str


def fit_dti(smiles,sequences,outcomes,*,alpha=10.0,ligand_bits=128,interaction_dims=16,target_name="pChEMBL") -> DTIModel:
    if not (len(smiles)==len(sequences)==len(outcomes)) or len(smiles)<4: raise ValueError("need >=4 matched interaction records")
    y=np.asarray(outcomes,float)
    if not np.all(np.isfinite(y)): raise ValueError("outcomes must be finite")
    X=np.asarray([pair_features(s,q,ligand_bits=ligand_bits,interaction_dims=interaction_dims) for s,q in zip(smiles,sequences)])
    mean=X.mean(0); scale=X.std(0); scale[scale<1e-12]=1; Z=(X-mean)/scale; A=np.c_[np.ones(len(Z)),Z]
    pen=np.eye(A.shape[1])*alpha; pen[0,0]=0
    coef=np.linalg.pinv(A.T@A+pen)@A.T@y
    return DTIModel(coef,mean,scale,float(alpha),ligand_bits,interaction_dims,tuple(smiles),tuple(sequences),target_name)


def _tan(a,b):
    x=float(a@b); u=float(a.sum()+b.sum()-x); return x/u if u else 1.0

def _seq_identity(a,b):
    # Length-normalized positional identity is transparent and deliberately
    # conservative; this is not an alignment algorithm.
    n=max(len(a),len(b)); return sum(x==y for x,y in zip(a,b))/n

def predict_dti(model: DTIModel,smiles,sequences):
    if len(smiles)!=len(sequences): raise ValueError("smiles and sequences lengths differ")
    X=np.asarray([pair_features(s,q,ligand_bits=model.ligand_bits,interaction_dims=model.interaction_dims) for s,q in zip(smiles,sequences)])
    values=np.c_[np.ones(len(X)),(X-model.mean)/model.scale]@model.coefficients
    fps=[morgan_fingerprint(s,n_bits=model.ligand_bits) for s in model.training_smiles]
    out=[]
    for s,q,v in zip(smiles,sequences,values):
        lf=morgan_fingerprint(s,n_bits=model.ligand_bits); ls=max(_tan(lf,x) for x in fps); ps=max(_seq_identity(q,x) for x in model.training_sequences)
        # Require support in both modalities. Thresholds are declared operating heuristics.
        inside=ls>=.35 and ps>=.3
        out.append({"smiles":s,"prediction":float(v),"target":model.target_name,"max_ligand_tanimoto":round(ls,4),
          "max_target_positional_identity":round(ps,4),"applicability_domain":"inside" if inside else "outside",
          "ad_thresholds":{"ligand_tanimoto":.35,"target_positional_identity":.3}})
    return out


def _metrics(y,p):
    e=y-p; ss=float(np.sum((y-y.mean())**2))
    return {"n":len(y),"rmse":float(np.sqrt(np.mean(e*e))),"mae":float(np.mean(abs(e))),
      "r2":float(1-np.sum(e*e)/ss) if ss>0 else None}


def _split(smiles,target_ids,strategy,fraction,seed,years):
    n=len(smiles); k=max(1,min(n-4,int(round(n*fraction))))
    if strategy=="warm_random":
        order=np.random.default_rng(seed).permutation(n); return order[k:],order[:k]
    labels=target_ids if strategy=="cold_target" else smiles if strategy=="cold_drug" else None
    if labels is not None:
        groups={}
        for i,x in enumerate(labels): groups.setdefault(x,[]).append(i)
        if len(groups)<2: raise ValueError(f"{strategy} needs at least 2 unique groups")
        ordered=sorted(groups.values(),key=lambda x:(len(x),str(x)))
        te=[]
        for g in ordered:
            if len(te)<k: te.extend(g)
        te=np.array(sorted(te),int); tr=np.array([i for i in range(n) if i not in set(te)],int)
        if len(tr)<4: raise ValueError("group split leaves fewer than 4 training records")
        return tr,te
    if strategy=="time":
        if years is None or len(years)!=n or any(y is None for y in years): raise ValueError("time split requires every record year")
        order=np.argsort(years); return order[:-k],order[-k:]
    raise ValueError("strategy must be warm_random, cold_target, cold_drug, or time")


def validate_dti(smiles,sequences,outcomes,target_ids,*,strategy="cold_target",test_fraction=.2,seed=23,years=None,alpha=10.0,ligand_bits=128,interaction_dims=16):
    """Validate with warm, cold-target, cold-drug or chronological holdout."""
    n=len(smiles)
    if n<10 or len(sequences)!=n or len(outcomes)!=n or len(target_ids)!=n: raise ValueError("validation needs >=10 complete records")
    if not .1<=test_fraction<=.5: raise ValueError("test_fraction must be 0.1..0.5")
    tr,te=_split(smiles,target_ids,strategy,test_fraction,seed,years)
    model=fit_dti([smiles[i] for i in tr],[sequences[i] for i in tr],[outcomes[i] for i in tr],alpha=alpha,ligand_bits=ligand_bits,interaction_dims=interaction_dims)
    pred=predict_dti(model,[smiles[i] for i in te],[sequences[i] for i in te]); vals=np.array([p["prediction"] for p in pred])
    return {"strategy":strategy,"seed":seed,"train_indices":tr.tolist(),"test_indices":te.tolist(),"metrics":_metrics(np.asarray(outcomes,float)[te],vals),
      "support":{"inside_ad":sum(p["applicability_domain"]=="inside" for p in pred),"outside_ad":sum(p["applicability_domain"]=="outside" for p in pred)},
      "performance_status":"measured_on_supplied_holdout_not_external_validation","model":model,
      "limitations":["Positional identity is not a sequence alignment.","No 3D target or ligand geometry is used.","Independent prospective validation: Missing."]}
