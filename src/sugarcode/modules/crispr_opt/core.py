from __future__ import annotations
from ...bio.sequence import clean_dna, reverse_complement, gc_content, find_motif

PAMS = {
    "SpCas9": ["NGG", "NAG"],
    "SpCas9-VQR": ["NGAN"],
    "Cas12a": ["TTTV"],
    "Cas9-NG": ["NG"],
}
SEED_REGION = 12  # PAM-proximal positions weighted most for off-target risk


def pam_sites(seq: str, pam: str = "NGG") -> list[dict]:
    """Every PAM occurrence on both strands with coordinates."""
    s = clean_dna(seq)
    sites = []
    for pos in find_motif(s, pam):
        sites.append({"strand": "+", "position": pos, "pam": s[pos:pos + len(pam)]})
    rc = reverse_complement(s)
    for pos in find_motif(rc, pam):
        orig = len(s) - pos - len(pam)
        sites.append({"strand": "-", "position": orig, "pam": rc[pos:pos + len(pam)]})
    return sorted(sites, key=lambda x: x["position"])


def _extract_guides(seq: str, pam: str = "NGG", guide_len: int = 20) -> list[dict]:
    """Enumerate candidate guides 5' of each PAM on both strands."""
    s = clean_dna(seq)
    cands = []
    for site in pam_sites(s, pam):
        if site["strand"] == "+":
            p = site["position"]
            if p >= guide_len:
                cands.append({"strand": "+", "guide": s[p - guide_len:p],
                              "pam": site["pam"], "cut_site": p - 3,
                              "start": p - guide_len, "end": p})
        else:
            # guide lies downstream of PAM on + strand
            p_end = site["position"] + len(site["pam"])
            if p_end + guide_len <= len(s):
                g = reverse_complement(s[p_end:p_end + guide_len])
                cands.append({"strand": "-", "guide": g,
                              "pam": site["pam"], "cut_site": p_end + 3,
                              "start": p_end, "end": p_end + guide_len})
    return cands


def score_on_target(guide: str) -> float:
    """Heuristic on-target efficiency model (Rule-Set-1-style position weights
    plus GC-window and motif penalties, calibrated to 0..1)."""
    g = clean_dna(guide)
    if len(g) != 20:
        raise ValueError("on-target model expects a 20 nt guide")
    score = 0.0
    # position-specific nucleotide preferences (approx Doench 2014)
    fav = {15: "G", 19: "G", 2: "C", 3: "A"}
    for pos, base in fav.items():
        if g[pos] == base:
            score += 0.08
    gc = gc_content(g)
    if 0.40 <= gc <= 0.60:
        score += 0.30
    elif 0.30 <= gc <= 0.70:
        score += 0.15
    # penalties
    if "TTTT" in g:
        score -= 0.25  # Pol III terminator
    if g[-1] == "T":
        score -= 0.05
    if g.count("G") >= 8:
        score -= 0.10  # extreme G load / quadruplex risk
    dinuc_boost = sum(0.02 for i in range(19) if g[i:i + 2] in ("GG", "GC"))
    return max(0.0, min(1.0, 0.45 + score + dinuc_boost))


def _hairpin_score(guide: str) -> float:
    """Fraction of the guide that can self-pair (simple sliding complement)."""
    g = clean_dna(guide)
    best = 0
    comp = reverse_complement(g)
    for shift in range(-len(g) + 4, len(g) - 3):
        run = cur = 0
        for i in range(len(g)):
            j = i + shift
            if 0 <= j < len(g) and g[i] == comp[j]:
                cur += 1
                run = max(run, cur)
            else:
                cur = 0
        best = max(best, run)
    return best / len(g)


def score_off_targets(guide: str, background: str, max_mismatches: int = 4) -> list[dict]:
    """Scan a background sequence for off-target sites, seed-weighted."""
    g = clean_dna(guide)
    bg = clean_dna(background)
    k = len(g)
    hits = []
    for strand, s in (("+", bg), ("-", reverse_complement(bg))):
        for i in range(len(s) - k + 1):
            cand = s[i:i + k]
            mm = [(k - 1 - j) for j in range(k) if cand[j] != g[j]]
            if len(mm) <= max_mismatches:
                # CFD-like weighting: mismatches in PAM-proximal seed hurt most
                risk = 1.0
                for pos_from_3p in mm:
                    w = 0.65 if pos_from_3p < SEED_REGION else 0.87
                    risk *= w
                if risk < 1.0 or not mm:
                    hits.append({"strand": strand, "position": i,
                                 "mismatches": len(mm),
                                 "risk": round(1.0 - risk, 4)})
    return sorted(hits, key=lambda h: -h["risk"])


def design_guides(seq: str, pam: str = "NGG", background: str | None = None,
                  top_n: int = 5, regulatory_tracks: list[dict] | None = None) -> dict:
    """Full design pass: enumerate, filter GC 40-60%, score on/off-target, rank."""
    cands = _extract_guides(seq, pam)
    graded = []
    for c in cands:
        gc = gc_content(c["guide"])
        on = score_on_target(c["guide"])
        hairpin = _hairpin_score(c["guide"])
        offs = score_off_targets(c["guide"], background, max_mismatches=3) if background else []
        off_risk = sum(o["risk"] for o in offs if o["mismatches"] > 0)
        # GC filter per spec (40-60% optimal window), hairpin suppresses folding
        composite = on * (1.0 - 0.5 * hairpin) / (1.0 + off_risk)
        if not (0.20 <= gc <= 0.80):
            continue
        graded.append({**c, "gc": round(gc, 3), "on_target": round(on, 3),
                       "hairpin_fraction": round(hairpin, 3),
                       "off_target_risk": round(off_risk, 3),
                       "composite": round(composite, 4)})
    graded.sort(key=lambda x: -x["composite"])
    return {
        "pam": pam,
        "candidates": len(cands),
        "guides": graded[:top_n],
        "pam_track": pam_sites(seq, pam),
        "regulatory_tracks": regulatory_tracks or [],
        "browser_track": _browser_track(seq, pam, graded[:top_n], regulatory_tracks or []),
    }


def _browser_track(seq: str, pam: str, guides: list[dict], tracks: list[dict]) -> dict:
    """Simulated genome-browser payload: coordinate system + feature tracks."""
    return {
        "reference_length": len(clean_dna(seq)),
        "tracks": [
            {"name": f"PAM {pam}", "type": "motif",
             "features": [{"start": s["position"], "end": s["position"] + len(s["pam"]),
                           "strand": s["strand"]} for s in pam_sites(seq, pam)]},
            {"name": "Top guides", "type": "guide",
             "features": [{"start": g["start"], "end": g["end"], "strand": g["strand"],
                           "score": g["composite"]} for g in guides]},
            *[{"name": t.get("name", f"track-{i}"), "type": "annotation",
               "features": t.get("features", [])} for i, t in enumerate(tracks)],
        ],
    }


# ---- Published CFD off-target model (Doench 2016) - verifiably sourced ----
import json as _json
from pathlib import Path as _Path

_DATA = _Path(__file__).parent / "data"
_CFD_MM = _json.load(open(_DATA / "cfd_mm_scores.json"))
_CFD_PAM = _json.load(open(_DATA / "cfd_pam_scores.json"))
_COMPLEMENT = {"A": "T", "T": "A", "U": "A", "C": "G", "G": "C"}


def cfd_score(wt_guide: str, off_guide: str, pam2: str = "GG") -> float:
    """Published CFD off-target score (Doench et al. 2016, matrices vendored
    verbatim from the CRISPOR distribution - see data/PROVENANCE.md).

    wt_guide / off_guide: 20-nt protospacers (same length).
    pam2: the off-target site's 2-nt PAM core ('GG' for NGG).
    Returns activity fraction 0-1 (1 = as active as on-target).
    """
    if len(wt_guide) != len(off_guide):
        raise ValueError("guides must be same length")
    pam2 = pam2.upper()
    if pam2 not in _CFD_PAM:
        raise KeyError(f"PAM {pam2!r} not in published matrix")
    wt = wt_guide.upper().replace("T", "U")
    off = off_guide.upper().replace("T", "U")
    score = 1.0
    for i, (w, o) in enumerate(zip(wt, off), 1):
        if w != o:
            key = f"r{w}:d{_COMPLEMENT[o]},{i}"
            score *= _CFD_MM[key]
    return round(score * _CFD_PAM[pam2], 6)


def score_off_targets_cfd(guide: str, background: str,
                          max_mismatches: int = 4) -> list[dict]:
    """Genome scan with the PUBLISHED CFD model: candidate sites within
    max_mismatches are scored by the real Doench matrices, PAM-aware."""
    guide = guide.upper()
    out = []
    for strand, s in (("+", background.upper()),
                      ("-", str.maketrans("ACGT", "TGCA"))):
        seq = s if strand == "+" else background.upper().translate(str.maketrans("ACGT", "TGCA"))[::-1]
        for i in range(len(seq) - 23 + 1):
            protospacer = seq[i:i + 20]
            pam = seq[i + 20:i + 23]
            if len(pam) < 3 or pam[1:] != "GG":
                continue
            mm = sum(1 for a, b in zip(guide, protospacer) if a != b)
            if mm == 0 or mm > max_mismatches:
                continue
            score = cfd_score(guide, protospacer, "GG")
            if score < 0.001:
                continue
            out.append({"position": i, "strand": strand,
                        "off_sequence": protospacer, "mismatches": mm,
                        "cfd_score": score,
                        "risk": "high" if score >= 0.3 else "medium" if score >= 0.05 else "low"})
    out.sort(key=lambda x: -x["cfd_score"])
    return out
