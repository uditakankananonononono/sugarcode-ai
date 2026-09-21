from __future__ import annotations
from ...bio.sequence import clean_dna, reverse_complement, tm_wallace, gc_content
from ..crispr_opt.core import pam_sites, score_off_targets

PBS_RANGE = (10, 17)   # primer binding site lengths (nt) per Anzalone et al.
RTT_RANGE = (10, 20)   # reverse-transcriptase template lengths (nt)


def design_pegrna(spacer: str, edit_seq: str, pbs_len: int | None = None,
                  rtt_len: int | None = None) -> dict:
    """Build a pegRNA from a 20 nt spacer and the desired edited strand context.

    edit_seq: the desired post-edit sequence 3' of the nick on the edited
    strand (RT template content). PBS is chosen by Wallace-Tm targeting
    ~30-34 C within 10-17 nt; RTT within 10-20 nt.
    """
    spacer = clean_dna(spacer)
    if len(spacer) != 20:
        raise ValueError("spacer must be 20 nt")
    edit_seq = clean_dna(edit_seq)
    rc_edit = reverse_complement(edit_seq)

    if pbs_len is None:
        best, best_d = PBS_RANGE[0], 1e9
        for L in range(PBS_RANGE[0], PBS_RANGE[1] + 1):
            cand = rc_edit[:L]
            d = abs(tm_wallace(cand) - 32.0)
            if d < best_d:
                best, best_d = L, d
        pbs_len = best
    if not PBS_RANGE[0] <= pbs_len <= PBS_RANGE[1]:
        raise ValueError(f"PBS length must be {PBS_RANGE[0]}-{PBS_RANGE[1]} nt")
    rtt_len = rtt_len or min(RTT_RANGE[1], max(RTT_RANGE[0], len(edit_seq)))
    if not RTT_RANGE[0] <= rtt_len <= RTT_RANGE[1]:
        raise ValueError(f"RTT length must be {RTT_RANGE[0]}-{RTT_RANGE[1]} nt")

    pbs = rc_edit[:pbs_len]
    rtt = rc_edit[:rtt_len]
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
    region = clean_dna(target_region)
    pos = edit["position"]
    if not 0 <= pos < len(region):
        raise ValueError("edit position outside target region")
    etype = edit["type"]
    ref, alt = clean_dna(edit.get("ref", "")), clean_dna(edit.get("alt", ""))
    if etype == "substitution" and region[pos:pos + len(ref)] != ref:
        raise ValueError("ref does not match target region at position")

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
            # RT template = edited strand 3' of nick (nick at PAM-3)
            nick = site["position"] - 3
            ctx = edited[nick + 1 - (pos - nick):] if False else None
            rtt_source = edited[pos:pos + 20] if etype != "deletion" else edited[max(0, nick - 0):nick + 20]
        else:
            g_start = site["position"] + 3
            if g_start + 20 > len(region):
                continue
            spacer = reverse_complement(region[g_start:g_start + 20])
            nick = site["position"] + 3
            rtt_source = reverse_complement(edited[max(0, nick - 20):nick])
        try:
            peg = design_pegrna(spacer, rtt_source[:20] if len(rtt_source) >= 10 else rtt_source)
        except ValueError:
            continue
        peg["pam_strand"] = site["strand"]
        peg["pam_position"] = site["position"]
        peg["distance_to_edit"] = dist
        if background:
            peg["off_targets"] = score_off_targets(spacer, background, max_mismatches=3)[:5]
        designs.append(peg)

    designs.sort(key=lambda d: d["distance_to_edit"])
    nicking = []
    for site in pam_sites(region, "NGG"):
        if designs and site["strand"] != designs[0]["pam_strand"]:
            d = abs(site["position"] - designs[0]["pam_position"])
            if 40 <= d <= 120:
                nicking.append({"strand": site["strand"], "position": site["position"],
                                "distance_from_primary": d})
    return {
        "edit": edit, "edited_region": edited,
        "pegrna_designs": designs[:5],
        "nicking_sgrna_candidates": nicking[:5],
        "pe_system": "PE3" if nicking else "PE2",
        "predicted_outcome_distribution": _outcome_distribution(designs[0]) if designs else None,
    }


def _outcome_distribution(peg: dict) -> dict:
    """Simplified efficiency/purity estimate from PBS Tm and RTT length."""
    tm_score = max(0.0, 1.0 - abs(peg["pbs_tm_c"] - 32.0) / 10.0)
    len_score = 1.0 - 0.02 * abs(peg["rtt_length"] - 14)
    eff = round(0.45 * tm_score * len_score, 3)
    return {"intended_edit": eff, "partial_rt_readthrough": round(0.2 * (1 - tm_score), 3),
            "indel_byproducts": round(0.1 + 0.15 * (1 - len_score), 3),
            "unedited": round(max(0.0, 1 - eff - 0.2 * (1 - tm_score) - (0.1 + 0.15 * (1 - len_score))), 3)}
