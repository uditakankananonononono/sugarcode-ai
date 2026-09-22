from __future__ import annotations
import random
from ...bio.sequence import clean_dna, gc_content

# E. coli sigma70 consensus elements
CONS_35 = "TTGACA"
CONS_10 = "TATAAT"
UP_ELEMENT = "AAAATATTT"  # A/T-rich UP element boosts rrn-type strength


def _mutate(base: str, rng: random.Random) -> str:
    return rng.choice([b for b in "ACGT" if b != base])


def score_promoter(seq: str) -> dict:
    """Score a promoter against sigma70 consensus.

    Strength 0..1 from -35/-10 identity, spacer length optimality (17 +/- 1),
    and UP-element A/T richness.
    """
    s = clean_dna(seq)
    best = None
    # scan for the -10 box, then check -35 upstream with spacer 15-19
    for i in range(len(s) - 6):
        box10 = s[i:i + 6]
        id10 = sum(a == b for a, b in zip(box10, CONS_10)) / 6
        for spacer in (15, 16, 17, 18, 19):
            j = i - spacer - 6
            if j < 0:
                continue
            box35 = s[j:j + 6]
            id35 = sum(a == b for a, b in zip(box35, CONS_35)) / 6
            spacer_score = 1.0 - abs(spacer - 17) / 4.0
            up = s[max(0, j - 9):j]
            up_score = (up.count("A") + up.count("T")) / max(1, len(up)) if up else 0.5
            total = 0.40 * id35 + 0.40 * id10 + 0.12 * spacer_score + 0.08 * up_score
            if best is None or total > best["strength"]:
                best = {"strength": round(total, 4), "minus10": box10,
                        "minus10_pos": i, "minus35": box35, "minus35_pos": j,
                        "spacer": spacer, "identity_35": round(id35, 3),
                        "identity_10": round(id10, 3), "up_element_at": round(up_score, 3)}
    if best is None:
        return {"strength": 0.0, "error": "sequence too short for promoter elements"}
    return best


def design_promoter(target_strength: float = 0.7, tfbs: list[str] | None = None,
                    seed: int = 42, length: int = 80) -> dict:
    """Generate a synthetic promoter tuned near target_strength (0..1).

    Starts from consensus and mutates away until within tolerance; optional
    TF binding sites are embedded upstream for compatibility.
    """
    rng = random.Random(seed)
    core = CONS_35 + "".join(rng.choice("ACGT") for _ in range(17)) + CONS_10
    flank5 = UP_ELEMENT + "".join(rng.choice("ACGT") for _ in range(6))
    flank3 = "".join(rng.choice("ACGT") for _ in range(12))
    seq = flank5 + core + flank3
    # degrade toward target by mutating consensus positions
    n_mut35 = round((1 - target_strength) * 6)
    n_mut10 = round((1 - target_strength) * 6)
    s = list(seq)
    base35 = len(flank5)
    base10 = base35 + 6 + 17
    for k in range(n_mut35):
        p = base35 + rng.randrange(6)
        s[p] = _mutate(s[p], rng)
    for k in range(n_mut10):
        p = base10 + rng.randrange(6)
        s[p] = _mutate(s[p], rng)
    seq = "".join(s)
    if tfbs:
        seq = "".join(tfbs) + seq
    sc = score_promoter(seq)
    return {
        "sequence": seq,
        "target_strength": target_strength,
        "achieved": sc,
        "gc": round(gc_content(seq), 3),
        "tfbs_embedded": tfbs or [],
        "host_prediction": _host_activity(sc["strength"]),
    }


def _host_activity(strength: float) -> dict:
    return {
        "e_coli": round(strength, 3),
        "b_subtilis": round(max(0.0, strength - 0.1), 3),
        "yeast_estimated": round(strength * 0.4, 3),
    }


def generate_library(n: int = 12, tfbs: list[str] | None = None,
                     strength_min: float = 0.2, strength_max: float = 0.95,
                     seed: int = 7) -> dict:
    """A promoter library spanning a predictable strength range."""
    rng = random.Random(seed)
    members = []
    for i in range(n):
        t = strength_min + (strength_max - strength_min) * (i / max(1, n - 1))
        d = design_promoter(target_strength=t, tfbs=tfbs, seed=rng.randrange(10**6))
        members.append({"id": f"pSC-{i + 1:03d}", "sequence": d["sequence"],
                        "predicted_strength": d["achieved"]["strength"]})
    members.sort(key=lambda m: m["predicted_strength"])
    heatmap = _motif_heatmap(members)
    return {"size": len(members), "members": members, "motif_heatmap": heatmap,
            "strength_range": [members[0]["predicted_strength"], members[-1]["predicted_strength"]]}


def _motif_heatmap(members: list[dict]) -> list[list[int]]:
    """Per-position A/C/G/T counts across aligned member cores (last 80 nt)."""
    rows = [[] for _ in range(4)]
    for b_i, base in enumerate("ACGT"):
        rows[b_i] = []
    cores = [m["sequence"][-80:] for m in members]
    for pos in range(80):
        col = [c[pos] for c in cores if len(c) > pos]
        for b_i, base in enumerate("ACGT"):
            rows[b_i].append(col.count(base))
    return rows

import math
import numpy as np
RBP={'lacI':'AATTGTGAGCGGATAACAATT','tetR':'TCCCTATCAGTGATAGAGA'}
def thermodynamic_occupancy(tf_conc,kd,cooperativity=1): return tf_conc**cooperativity/(kd**cooperativity+tf_conc**cooperativity)
def promoter_response(seq,tf_conc=0,tf_kd=1,repressor=True):
 base=score_promoter(seq)['strength']; occ=thermodynamic_occupancy(tf_conc,tf_kd); return {'basal':base,'occupancy':occ,'expression':base*((1-occ) if repressor else (1+occ))}
def sequence_features(seq):
 s=clean_dna(seq); hairpin=sum(s[i:i+4]==s[i:i+4][::-1] for i in range(len(s)-3)); return {'gc':gc_content(s),'hairpin_proxy':hairpin,'length':len(s),'homopolymer_max':max(len(x) for b in 'ACGT' for x in s.split(b) if x) if s else 0}
def host_context(seq,host='e_coli',copy_number=1,growth_rate=1):
 strength=score_promoter(seq)['strength']; factors={'e_coli':1,'b_subtilis':.85,'yeast':.35}; burden=min(1,strength*copy_number/(10*growth_rate)); return {'host':host,'activity':strength*factors.get(host,.5)*(1-burden*.3),'burden':burden,'copy_number':copy_number}
def motif_compatibility(seq,tf_motifs):
 s=clean_dna(seq); return {name:{'count':s.count(clean_dna(motif)),'positions':[i for i in range(len(s)) if s.startswith(clean_dna(motif),i)]} for name,motif in tf_motifs.items()}
def expression_noise(mean_expression,burst_size=5,degradation=.2): return {'mean':mean_expression,'variance':mean_expression*(1+burst_size),'cv':math.sqrt(mean_expression*(1+burst_size))/max(mean_expression,1e-9),'fano':1+burst_size,'degradation':degradation}
def library_calibration(predicted,observed):
 x=np.asarray(predicted,float); y=np.asarray(observed,float); A=np.vstack([x,np.ones(len(x))]).T; slope,intercept=np.linalg.lstsq(A,y,rcond=None)[0]; pred=slope*x+intercept; return {'slope':float(slope),'intercept':float(intercept),'rmse':float(np.sqrt(np.mean((pred-y)**2))),'calibrated':pred.tolist()}
def promoter_report(target=.7,tfbs=None,host='e_coli'):
 d=design_promoter(target,tfbs); s=d['sequence']; return {**d,'features':sequence_features(s),'host_context':host_context(s,host),'motif_compatibility':motif_compatibility(s,{f'tf{i}':x for i,x in enumerate(tfbs or [])}),'noise':expression_noise(d['achieved']['strength']),'model_status':'Sigma70 motif/thermodynamic heuristics; no trained sequence model and host predictions are not experimentally calibrated.'}
def promoter_diagnostics(r):
 a=r['achieved']; f=r['features']; h=r['host_context']; n=r['noise']; return {'target':r['target_strength'],'strength':a['strength'],'identity_35':a['identity_35'],'identity_10':a['identity_10'],'spacer':float(a['spacer']),'up_at':a['up_element_at'],'gc':f['gc'],'hairpin_proxy':float(f['hairpin_proxy']),'host_activity':h['activity'],'burden':h['burden'],'noise_cv':n['cv'],'noise_fano':n['fano']}
