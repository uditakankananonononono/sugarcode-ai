from __future__ import annotations
from ...bio.sequence import clean_dna, reverse_complement, tm_wallace, gc_content
from ..crispr_opt.core import pam_sites, score_off_targets

def _oligo(sequence):
    if not isinstance(sequence, str):
        raise ValueError('sequence must be text')
    sequence = ''.join(sequence.split()).upper()
    if not sequence or set(sequence) - set('ACGT'):
        raise ValueError('nonempty unambiguous DNA (ACGT) required')
    return sequence


PBS_RANGE = (10, 16)   # PBS lengths (nt) per Anzalone et al.; the published PBS/RTT boundary leaves a 16 nt flap on the spacer, so longer PBS needs genomic context this function does not receive
RTT_RANGE = (10, 20)   # reverse-transcriptase template lengths (nt)


def design_pegrna(spacer: str, edit_seq: str, pbs_len: int | None = None,
                  rtt_len: int | None = None) -> dict:
    """Build a pegRNA from a 20 nt spacer and the desired edited strand context.

    edit_seq: the desired post-edit sequence 3' of the nick on the edited
    strand (RT template content). The PBS anneals to the 3' flap of the
    nicked strand, i.e. the genomic sequence immediately 5' of the nick;
    with an NGG PAM the PBS/RTT boundary follows the convention of the
    published, experimentally validated pegRNAs (Anzalone et al. 2019 HEK3
    +1 CTT and RNF2 +5 G>T; Chow et al. 2021): the PBS is the reverse
    complement of spacer[16-pbs_len:16] and the RTT templates from spacer
    position 17 (1-based). PBS length is chosen by Wallace-Tm targeting
    ~30-34 C within 10-16 nt; RTT within 10-20 nt.
    """
    spacer = _oligo(spacer)
    if len(spacer) != 20:
        raise ValueError("spacer must be 20 nt")
    edit_seq = _oligo(edit_seq)
    rc_edit = reverse_complement(edit_seq)

    if pbs_len is None:
        best, best_d = PBS_RANGE[0], 1e9
        for L in range(PBS_RANGE[0], PBS_RANGE[1] + 1):
            cand = reverse_complement(spacer[16 - L:16])
            d = abs(tm_wallace(cand) - 32.0)
            if d < best_d:
                best, best_d = L, d
        pbs_len = best
    if isinstance(pbs_len, bool) or not isinstance(pbs_len, int) or not PBS_RANGE[0] <= pbs_len <= PBS_RANGE[1]:
        raise ValueError(f"PBS length must be {PBS_RANGE[0]}-{PBS_RANGE[1]} nt")
    rtt_len = min(RTT_RANGE[1], len(edit_seq)) if rtt_len is None else rtt_len
    if isinstance(rtt_len, bool) or not isinstance(rtt_len, int) or not RTT_RANGE[0] <= rtt_len <= RTT_RANGE[1]:
        raise ValueError(f"RTT length must be {RTT_RANGE[0]}-{RTT_RANGE[1]} nt")

    if rtt_len > len(edit_seq):
        raise ValueError('edited context is shorter than requested RTT; supply more verified context')
    pbs = reverse_complement(spacer[16 - pbs_len:16])
    # the RTT templates from the nick: its 3' end pairs with the nick-proximal
    # base, so truncation must keep the LAST rtt_len bases of the reverse
    # complement, not the first (bug found against the published HEK3 pegRNA)
    rtt = rc_edit[-rtt_len:] if rtt_len <= len(rc_edit) else rc_edit
    ext = rtt + pbs  # 3' extension, 5'->3'
    # first base of RTT should not be C (pairs with scaffold G -> mispriming)
    warns = []
    if rtt and rtt[0] == "C":
        warns.append("RTT 5' base is C: risk of scaffold-templated misincorporation; prefer alternate RTT length")
    if gc_content(pbs) < 0.3 or gc_content(pbs) > 0.7:
        warns.append("PBS GC outside 30-70%: annealing may be weak or non-specific")
    return {
        "spacer": spacer,
        "pbs": pbs, "pbs_length": pbs_len, "pbs_tm_c": round(tm_wallace(pbs), 1),
        "rt_template": rtt, "rtt_length": rtt_len,
        "pegrna_3p_extension": ext,
        "full_pegrna": spacer + "GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC" + ext,
        "warnings": warns,
    }


def design_edit(target_region: str, edit: dict, background: str | None = None) -> dict:
    """Design a full prime edit for a point mutation / small indel.

    edit: {"type": "substitution"|"insertion"|"deletion", "position": int,
           "ref": str, "alt": str}
    Finds PAMs near the edit, designs pegRNAs on each strand, finds PE3
    nicking sgRNAs 40-120 nt on the opposite strand, runs off-target scans.
    """
    region = _oligo(target_region)
    if not isinstance(edit, dict):
        raise ValueError('edit must be a mapping')
    pos = edit.get('position')
    etype = edit.get('type')
    if etype not in ('substitution', 'insertion', 'deletion'):
        raise ValueError('unknown edit type')
    if isinstance(pos, bool) or not isinstance(pos, int) or not 0 <= pos <= len(region):
        raise ValueError('edit position must be an integer within target boundaries')
    ref = _oligo(edit['ref']) if edit.get('ref') else ''
    alt = _oligo(edit['alt']) if edit.get('alt') else ''
    if etype == 'insertion':
        if ref or not alt:
            raise ValueError('insertion requires empty ref and nonempty alt')
    else:
        if not ref or pos+len(ref) > len(region) or region[pos:pos+len(ref)] != ref:
            raise ValueError('nonempty ref must exactly match target span')
        if etype == 'deletion' and alt:
            raise ValueError('deletion requires empty alt')
        if etype == 'substitution' and (not alt or len(alt) != len(ref) or alt == ref):
            raise ValueError('substitution requires changed alt of equal length')

    if etype == "substitution":
        edited = region[:pos] + alt + region[pos + len(ref):]
    elif etype == "insertion":
        edited = region[:pos] + alt + region[pos:]
    elif etype == "deletion":
        edited = region[:pos] + region[pos + len(ref):]
    else:
        raise ValueError(f"unknown edit type {etype!r}")

    designs = []
    for site in pam_sites(region, "NGG"):
        dist = abs(site["position"] - pos)
        if dist > 35:
            continue  # PAM too far from edit for efficient PE
        if site["strand"] == "+":
            g_start = site["position"] - 20
            if g_start < 0:
                continue
            spacer = region[g_start:site["position"]]
            # RT template = edited strand 3' of the nick; the PBS/RTT
            # boundary is 4 nt upstream of the PAM per the published convention
            nick = site["position"] - 4
            if nick < 0 or pos < nick or edited[nick:nick + 20] == region[nick:nick + 20]:
                continue  # RT template would not encode the edit
            rtt_source = edited[nick:nick + 20]
        else:
            g_start = site["position"] + 3
            if g_start + 20 > len(region):
                continue
            spacer = reverse_complement(region[g_start:g_start + 20])
            nick = site["position"] + 7
            if nick > len(region) or pos >= nick:
                continue  # reverse-strand template extends left of the nick
            # Indels left of the nick shift its coordinate in the edited allele.
            # A deletion spanning the nick removes the PBS boundary: skip it.
            if pos+len(ref) > nick:
                continue
            edited_nick = nick + len(alt)-len(ref)
            rtt_source = reverse_complement(edited[max(0, edited_nick-20):edited_nick])
            if rtt_source == reverse_complement(region[max(0,nick-20):nick]):
                continue
        try:
            peg = design_pegrna(spacer, rtt_source[:20] if len(rtt_source) >= 10 else rtt_source)
        except ValueError:
            continue
        # Require complete edit plus 3 nt distal context. This explicit design
        # constraint is not a validated efficiency threshold.
        required = (pos-nick+len(alt)+3 if site['strand']=='+' else
                    nick-(pos+len(ref))+len(alt)+3)
        if required < 3 or len(peg['rt_template']) < required:
            continue
        peg['distal_homology_min_nt'] = 3
        peg["nick_position"] = nick
        peg["pam_strand"] = site["strand"]
        peg["pam_position"] = site["position"]
        peg["distance_to_edit"] = dist
        if background:
            peg["off_targets"] = score_off_targets(spacer, background, max_mismatches=3)[:5]
        designs.append(peg)

    designs.sort(key=lambda d: d["distance_to_edit"])
    nicking = []
    # PE3 nick is the canonical Cas9 nick site, not the PAM coordinate.
    # Retain the primary association so candidates are not mixed across designs.
    if designs:
        primary = designs[0]
        for site in pam_sites(region, 'NGG'):
            if site['strand'] == primary['pam_strand']:
                continue
            if site['strand'] == '+':
                p = site['position']; start = p-20
                if start < 0:
                    continue
                spacer = region[start:p]; nick = p-3
            else:
                start = site['position']+3
                if start+20 > len(region):
                    continue
                spacer = reverse_complement(region[start:start+20]); nick = start+3
            distance = abs(nick-primary['nick_position'])
            if 40 <= distance <= 120:
                candidate = {'strand':site['strand'],'position':site['position'],
                             'pam':site['pam'],'spacer':spacer,'nick_position':nick,
                             'distance_from_primary':distance,
                             'primary_pam_position':primary['pam_position']}
                if background:
                    candidate['off_targets'] = score_off_targets(spacer, background, max_mismatches=3)[:5]
                nicking.append(candidate)

    return {
        "edit": edit, "edited_region": edited,
        "pegrna_designs": designs[:5],
        "nicking_sgrna_candidates": nicking[:5],
        "pe_system": "PE3" if nicking else "PE2",
        "predicted_outcome_distribution": _outcome_distribution(designs[0]) if designs else None,
    }


def _outcome_distribution(peg: dict) -> dict:
    """Legacy unfitted four-class heuristic; not assay-calibrated outcomes.

    Only the designed RTT range is supported. Input/domain checks are numerical
    safeguards, not a repair mechanism or validation of these hand-set weights.
    """
    from collections.abc import Mapping
    if not isinstance(peg, Mapping) or 'pbs_tm_c' not in peg or 'rtt_length' not in peg:
        raise ValueError('peg must include pbs_tm_c and rtt_length')
    tm = _finite_real(peg['pbs_tm_c'], 'pbs_tm_c')
    length = peg['rtt_length']
    if type(length) is not int or not RTT_RANGE[0] <= length <= RTT_RANGE[1]:
        raise ValueError('rtt_length must be an integer in designed RTT range')
    tm_score = max(0.0, 1.0 - abs(tm - 32.0) / 10.0)
    len_score = 1.0 - 0.02 * abs(length - 14)
    eff = round(0.45 * tm_score * len_score, 3)
    return {'intended_edit': eff,
            'partial_rt_readthrough': round(0.2 * (1 - tm_score), 3),
            'indel_byproducts': round(0.1 + 0.15 * (1 - len_score), 3),
            'unedited': round(max(0.0, 1 - eff - 0.2 * (1 - tm_score) -
                                   (0.1 + 0.15 * (1 - len_score))), 3)}

# Explicit biophysical and repair models. There is no trained sequence model
# and this module is not clinically validated.
import math
import json
import numpy as np

# Sugimoto et al. (1995) RNA/DNA hybrid nearest neighbors. Keys denote the
# 5'->3' RNA strand, with T used as the serialized representation of U.
# H: kcal/mol; S: cal/(mol K). Source table R_DNA_NN1:
# https://biopython.org/docs/latest/api/Bio.SeqUtils.MeltingTemp.html
_PBS_RNA_DNA_NN = {
    'AA': (-7.8, -21.9), 'AC': (-5.9, -12.3),
    'AG': (-9.1, -23.5), 'AT': (-8.3, -23.9),
    'CA': (-9.0, -26.1), 'CC': (-9.3, -23.2),
    'CG': (-16.3, -47.1), 'CT': (-7.0, -19.7),
    'GA': (-5.5, -13.5), 'GC': (-8.0, -17.1),
    'GG': (-12.8, -31.9), 'GT': (-7.8, -21.6),
    'TA': (-7.8, -23.2), 'TC': (-8.6, -22.9),
    'TG': (-10.4, -28.4), 'TT': (-11.5, -36.4),
}


def pbs_thermodynamics(pbs, target_temperature_c=37, salt_mM=50,
                       strand_concentration_nM=25):
    """Perfect RNA PBS / complementary DNA duplex, not editing efficiency.

    PBS is encoded as ACGT in RNA 5'->3' orientation. Equal free strand
    totals are assumed, each strand_concentration_nM. Sugimoto 1995 hybrid
    H/S parameters plus the SantaLucia entropy salt correction (a DNA-derived
    approximation, NOT a fitted hybrid/intracellular salt model). No mismatches,
    dangling ends, magnesium, competing fold or effective tether concentration.
    """
    from numbers import Real
    s = _oligo(pbs)
    if not 8 <= len(s) <= 25:
        raise ValueError('PBS must be 8-25 nt')
    for value, name in ((target_temperature_c, 'temperature'),
                        (salt_mM, 'salt_mM'),
                        (strand_concentration_nM, 'strand_concentration_nM')):
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ValueError(f'{name} must be a finite number')
    if target_temperature_c <= -273.15 or salt_mM <= 0 or strand_concentration_nM <= 0:
        raise ValueError('positive absolute temperature, salt and concentration required')
    # General initiation only; this hybrid table has no symmetry or terminal
    # correction. RNA/DNA strands are distinct even for palindromic sequence.
    dh, ds = 1.9, -3.9
    for i in range(len(s)-1):
        h, entropy = _PBS_RNA_DNA_NN[s[i:i+2]]
        dh += h
        ds += entropy
    salt_entropy = .368 * (len(s)-1) * (math.log(salt_mM)-math.log(1000))
    ds += salt_entropy
    temperature_k = target_temperature_c + 273.15
    gas_constant = 1.987
    log_concentration = math.log(strand_concentration_nM)-math.log(1e9)
    denominator = ds + gas_constant*(log_concentration-math.log(2))
    if denominator >= 0:
        raise ValueError('conditions outside positive melting-temperature model domain')
    tm = 1000*dh/denominator-273.15
    dg = dh-temperature_k*ds/1000
    # Equal strand totals C: f = K*C*(1-f)^2. Stable quadratic form
    # avoids exp overflow/catastrophic cancellation at strong association.
    log_q = -1000*dg/(gas_constant*temperature_k) + log_concentration
    if log_q >= 0:
        inverse_q = math.exp(-log_q)
        anneal = 2/(2+inverse_q+math.sqrt(inverse_q*inverse_q+4*inverse_q))
    else:
        q = math.exp(log_q)
        anneal = 2*q/(1+2*q+math.sqrt(1+4*q))
    return {'length': len(s), 'gc_fraction': gc_content(s), 'tm_c': tm,
            'delta_h_kcal_mol': dh, 'delta_s_cal_mol_k': ds,
            'salt_entropy_correction_cal_mol_k': salt_entropy,
            'delta_g_kcal_mol': dg, 'annealing_probability': anneal,
            'temperature_c': target_temperature_c, 'salt_mM': salt_mM,
            'strand_concentration_nM': strand_concentration_nM,
            'model': 'Sugimoto1995_RNA_DNA_perfect_duplex',
            'salt_model': 'SantaLucia1998_DNA_entropy_approximation',
            'status': 'OPEN/unfitted PBS context: equal-strand equilibrium, not editing efficiency'}

def secondary_structure(sequence,min_stem=4):
    """RNA fold of supplied pegRNA sequence; no self-overlap stem shortcut."""
    from ..rna_nussinov import fold_energy
    seq=_oligo(sequence)
    if isinstance(min_stem,bool) or not isinstance(min_stem,int) or min_stem<1:
        raise ValueError('min_stem must be positive integer')
    if len(seq)>2000:
        raise ValueError('RNA fold exceeds 2000-base resource limit')
    fold=fold_energy(seq)
    pairs={tuple(pair) for pair in fold['pairs']}
    longest=0
    for i,j in pairs:
        if (i-1,j+1) in pairs:
            continue
        length=1
        while (i+length,j-length) in pairs:
            length+=1
        longest=max(longest,length)
    return {'longest_stem':longest,'paired_fraction':2*len(pairs)/len(seq),
            'structure_penalty':min(1,longest/10),'min_stem':min_stem,
            'stems_meeting_min':sum((i-1,j+1) not in pairs and all((i+k,j-k) in pairs for k in range(min_stem)) for i,j in pairs),
            'pairs':fold['pairs'],'dot_bracket':fold['dot_bracket'],
            'mfe_kcal_mol':fold['mfe_kcal_mol'],'method':fold['model'],
            'status':'RNA secondary-structure model; penalty is uncalibrated, not editing efficiency'}


def _finite_real(value, name, minimum=None, maximum=None):
    from numbers import Real
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValueError(f'{name} outside supported range')
    return float(value)


def rt_processivity(rt_template, base_processivity=.96):
    """Unfitted processivity/pause heuristic, not measured RT completion."""
    s = _oligo(rt_template)
    probability = _finite_real(base_processivity, 'base_processivity', 0, 1)
    if probability == 0:
        raise ValueError('base_processivity must be in (0,1]')
    # Linear run scan replaces cubic repeated substring/set construction.
    longest = run = 1
    for i in range(1, len(s)):
        run = run+1 if s[i] == s[i-1] else 1
        longest = max(longest, run)
    gc = gc_content(s)
    pause = .03*max(0, longest-3)+.2*abs(gc-.5)
    completion = probability**len(s)*math.exp(-pause)
    return {'length': len(s), 'gc_fraction': gc, 'homopolymer_max': longest,
            'pause_penalty': pause, 'completion_probability': completion,
            'model_status': 'OPEN/unfitted RT processivity heuristic'}


def flap_resolution(rt_template, homology_length=10, fen1_activity=.8):
    """Unfitted flap score with sequence and probability domain checks."""
    s = _oligo(rt_template)
    if isinstance(homology_length, bool) or not isinstance(homology_length, int) or homology_length < 1:
        raise ValueError('homology_length must be a positive integer')
    activity = _finite_real(fen1_activity, 'fen1_activity', 0, 1)
    equilibration = -math.expm1(-homology_length/8)
    structure = secondary_structure(s)['structure_penalty']
    resolution = activity*equilibration*(1-.5*structure)
    return {'equilibration': equilibration, 'structure_penalty': structure,
            'resolution_probability': resolution,
            'model_status': 'OPEN/unfitted flap-resolution heuristic'}


def repair_competition(rt_template, mmr_activity=.7, ber_activity=.2,
                       fen1_activity=.8, nick_bias=.5):
    """Normalize hand-set pathway scores; NOT assay-fitted repair frequencies.

    The residual indel score is arbitrary, including with all activities zero.
    Such output is a surrogate assumption, not a biological zero-activity result.
    """
    for value, name in ((mmr_activity, 'mmr'), (ber_activity, 'ber'),
                        (fen1_activity, 'fen1'), (nick_bias, 'nick_bias')):
        _finite_real(value, name, 0, 1)
    completion = rt_processivity(rt_template)['completion_probability']
    flap = flap_resolution(rt_template, fen1_activity=fen1_activity)['resolution_probability']
    raw = np.array([completion*flap*(.4+.6*nick_bias),
                    mmr_activity*(1-nick_bias)*.35, ber_activity*.15,
                    (1-completion)*.5+.05])
    raw /= raw.sum()
    return {'intended': float(raw[0]), 'reverted': float(raw[1]),
            'partial_edit': float(raw[2]), 'indel': float(raw[3]),
            'pathway_inputs': {'mmr': mmr_activity, 'ber': ber_activity,
                               'fen1': fen1_activity, 'nick_bias': nick_bias},
            'model_status': 'OPEN/unfitted normalized pathway scores; residual indel channel is arbitrary'}

def nicking_strategy(primary_position,candidates,edited_strand='+'):
    ranked=[]
    for c in candidates:
        distance=abs(int(c['position'])-primary_position); orientation=1 if c.get('strand')!=edited_strand else .3; distance_score=math.exp(-((distance-70)/35)**2); dsb_risk=math.exp(-distance/15) if c.get('strand')!=edited_strand else .05; timing=1-math.exp(-distance/30); score=.5*distance_score+.3*orientation+.2*timing-.4*dsb_risk; ranked.append({**c,"distance":distance,"orientation_score":orientation,"timing_score":timing,"dsb_like_risk":dsb_risk,"score":score,"strategy":"PE3b" if c.get('requires_edit_match') else "PE3"})
    return sorted(ranked,key=lambda x:(-x['score'],x['distance']))

def spacer_binding_risk(spacer, background, max_mismatches=3, intended_position=None):
    """Scan spacer homologs with binding hazard highest for exact matches.

    ``score_off_targets`` exposes mismatch *dissimilarity* as ``risk``. Prime
    Design converts it back to similarity (1-dissimilarity). An exact hit is
    excluded only when its observed position equals ``intended_position``;
    other perfect copies remain maximum-hazard off-targets.
    """
    spacer = clean_dna(spacer)
    hits = score_off_targets(spacer, background, max_mismatches)
    ranked = []
    for hit in hits:
        if intended_position is not None and hit["position"] == intended_position and hit["mismatches"] == 0:
            continue
        binding_risk = max(0.0, min(1.0, 1.0 - float(hit["risk"])))
        ranked.append({**hit, "binding_risk": binding_risk})
    ranked.sort(key=lambda item: (-item["binding_risk"], item["mismatches"], item["position"]))
    return {"hit_count": len(ranked),
            "aggregate_binding_risk": float(sum(h["binding_risk"] for h in ranked)),
            "top_hits": ranked[:10],
            "intended_position_excluded": intended_position}

def rt_template_offtarget_risk(rt_template,background,min_identity=.7):
    r=clean_dna(rt_template); bg=clean_dna(background); hits=[]
    for i in range(len(bg)-len(r)+1):
        window=bg[i:i+len(r)]; identity=sum(a==b for a,b in zip(r,window))/len(r)
        if identity>=min_identity: hits.append({"position":i,"identity":identity,"annealing_probability":identity*pbs_thermodynamics(r[:min(17,len(r))])['annealing_probability']})
    hits.sort(key=lambda x:-x['annealing_probability']); return {"hit_count":len(hits),"aggregate_rewrite_risk":sum(h['annealing_probability'] for h in hits),"hits":hits[:10]}

def edit_window_score(edit_distance,rtt_length,optimal=(4,15)):
    if rtt_length<1 or edit_distance<0: raise ValueError("distance non-negative and RTT length positive")
    inside=optimal[0]<=edit_distance<=min(optimal[1],rtt_length); center=sum(optimal)/2; return {"inside_optimal_window":inside,"distance_score":math.exp(-((edit_distance-center)/5)**2),"partial_edit_risk":min(1,max(0,edit_distance-rtt_length+3)/5)}

def outcome_distribution(peg, repair=None, nick=None):
    """Unfitted outcome score blend; validated domains are not biological fit.

    Supplied repair must be a normalized nonnegative distribution. Negative
    nick scores from the ranking heuristic are allowed in [-1,1]; the intended
    score is clamped before blending so it cannot become a negative weight.
    """
    from collections.abc import Mapping
    if not isinstance(peg, Mapping) or 'pbs_tm_c' not in peg or 'rt_template' not in peg:
        raise ValueError('peg must include pbs_tm_c and rt_template')
    tm_c = _finite_real(peg['pbs_tm_c'], 'pbs_tm_c')
    process = rt_processivity(peg['rt_template'])['completion_probability']
    if repair is None:
        repair = repair_competition(peg['rt_template'])
    keys = ('intended', 'partial_edit', 'indel', 'reverted')
    if not isinstance(repair, Mapping) or any(key not in repair for key in keys):
        raise ValueError('repair must include all four pathway probabilities')
    values = {key: _finite_real(repair[key], key, 0, 1) for key in keys}
    if not math.isclose(sum(values.values()), 1, rel_tol=0, abs_tol=1e-8):
        raise ValueError('repair probabilities must sum to one')
    if nick is None:
        nick = {}
    if not isinstance(nick, Mapping):
        raise ValueError('nick must be a mapping')
    score = _finite_real(nick.get('score', 0), 'nick score', -1, 1)
    risk = _finite_real(nick.get('dsb_like_risk', 0), 'dsb_like_risk', 0, 1)
    tm = max(0, 1-abs(tm_c-32)/15)
    intended = max(0, min(1, values['intended']*.5+.3*tm+.2*process+.15*score))
    partial = values['partial_edit']*(1-intended)
    indel = min(.5, values['indel']+.2*risk)
    reverted = values['reverted']
    raw = np.array([intended, partial, indel, reverted,
                    max(0, 1-intended-partial-indel-reverted)])
    raw /= raw.sum()
    return dict(zip(('intended_edit', 'partial_edit', 'indel', 'reverted', 'unedited'),
                    map(float, raw)))

def architecture_variants(spacer,edit_seq,pbs_lengths=range(10,17),rtt_lengths=range(10,21)):
    designs=[]
    for pbs in pbs_lengths:
        for rtt in rtt_lengths:
            if len(edit_seq)<max(pbs,rtt): continue
            peg=design_pegrna(spacer,edit_seq,pbs,rtt); thermo=pbs_thermodynamics(peg['pbs']); process=rt_processivity(peg['rt_template']); structure=secondary_structure(peg['pegrna_3p_extension']); repair=repair_competition(peg['rt_template']); efficiency=thermo['annealing_probability']*process['completion_probability']*(1-structure['structure_penalty']*.5); precision=outcome_distribution(peg,repair)['intended_edit']; designs.append({**peg,"predicted_efficiency":efficiency,"predicted_precision":precision,"thermodynamics":thermo,"processivity":process,"secondary_structure":structure,"repair":repair,"score":.55*efficiency+.45*precision})
    return sorted(designs,key=lambda x:(-x['score'],x['pbs_length'],x['rtt_length']))

def pegrna_diagnostics(peg,background=None):
    thermo=pbs_thermodynamics(peg['pbs']); rt=rt_processivity(peg['rt_template']); struct=secondary_structure(peg['pegrna_3p_extension']); flap=flap_resolution(peg['rt_template']); repair=repair_competition(peg['rt_template']); out=outcome_distribution(peg,repair)
    d={"spacer_gc":gc_content(peg['spacer']),"pbs_gc":gc_content(peg['pbs']),"rtt_gc":gc_content(peg['rt_template']),"pbs_length":float(peg['pbs_length']),"rtt_length":float(peg['rtt_length']),"extension_length":float(len(peg['pegrna_3p_extension'])),"pbs_tm_c":float(peg['pbs_tm_c']),"pbs_delta_g":thermo['delta_g_kcal_mol'],"pbs_annealing_probability":thermo['annealing_probability'],"rt_completion_probability":rt['completion_probability'],"rt_pause_penalty":rt['pause_penalty'],"rt_homopolymer_max":float(rt['homopolymer_max']),"structure_longest_stem":float(struct['longest_stem']),"structure_paired_fraction":struct['paired_fraction'],"structure_penalty":struct['structure_penalty'],"flap_equilibration":flap['equilibration'],"flap_resolution_probability":flap['resolution_probability'],"repair_intended":repair['intended'],"repair_reverted":repair['reverted'],"repair_partial":repair['partial_edit'],"repair_indel":repair['indel'],"outcome_intended":out['intended_edit'],"outcome_partial":out['partial_edit'],"outcome_indel":out['indel'],"outcome_reverted":out['reverted'],"outcome_unedited":out['unedited'],"warning_count":float(len(peg['warnings']))}
    if background is not None:
        spacing=spacer_binding_risk(peg['spacer'],background); rewrite=rt_template_offtarget_risk(peg['rt_template'],background); d.update({"background_spacer_hit_count":float(spacing['hit_count']),"background_spacer_binding_risk":float(spacing['aggregate_binding_risk']),"background_rt_hit_count":float(rewrite['hit_count']),"background_rt_rewrite_risk":float(rewrite['aggregate_rewrite_risk'])})
    return d

def export_design(design,format='json'):
    if format!='json': raise ValueError("only JSON export is supported")
    return json.dumps(design,sort_keys=True,separators=(',',':'))

def validation_strategy(edit_length,outcome=None):
    outcome=outcome or {}; expected=max(1e-4,float(outcome.get('intended_edit',.1))); depth=math.ceil(100/max(expected,.001)); return {"assay":"amplicon sequencing","minimum_read_depth":depth,"amplicon_span_bp":max(250,edit_length+200),"report":["intended allele fraction","partial RT alleles","indel spectrum","unedited fraction"],"orthogonal_confirmation":"independent sequencing chemistry for selected clones","model_status":"Planning guidance only; validate under institutional procedures."}

def compile_prime_edit(spacer,edit_seq,background=None,nicking_candidates=None):
    variants=architecture_variants(spacer,edit_seq)
    if not variants: raise ValueError("edit sequence must support requested PBS/RTT design ranges")
    top=variants[0]; nick=nicking_strategy(0,nicking_candidates or [])[:5]; selected_nick=nick[0] if nick else None; outcomes=outcome_distribution(top,top['repair'],selected_nick); diagnostics=pegrna_diagnostics(top,background)
    return {"recommended":top,"alternatives":variants[1:10],"nicking_strategies":nick,"outcome_distribution":outcomes,"diagnostics":diagnostics,"validation":validation_strategy(len(edit_seq),outcomes),"export":export_design({"spacer":top['spacer'],"pbs":top['pbs'],"rt_template":top['rt_template'],"outcomes":outcomes}),"model_status":"Explicit thermodynamic/repair surrogates; no trained sequence model and not clinically validated."}
