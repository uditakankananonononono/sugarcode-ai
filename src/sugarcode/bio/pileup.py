"""Mpileup-style per-position pileup from parsed SAM records.

Walks each mapped read's CIGAR and stacks bases over reference positions:

- M/= /X consume reference + query and contribute a base (with its quality).
- I is an insertion: the inserted query string is attached as a "+lenSEQ"
  event to the reference position it FOLLOWS (samtools convention).
- D is a deletion: the event is attached as "-lenN*" to the preceding
  position (the deleted reference sequence is not knowable from SAM alone,
  so N placeholders are used - documented, not fabricated) and each deleted
  reference position records a "*" base for that read, counted in depth as
  samtools does.
- N (skipped) consumes the reference with no bases; S/H consume no
  reference.

Without a reference FASTA the reference base is unknowable, so text output
uses the ACGTN letters (uppercase = forward strand, lowercase = reverse)
rather than mpileup's '.',',' notation; the structured form reports counts
per base letter plus per-position quality and MAPQ means.
"""
from __future__ import annotations

from .sam import parse_cigar

def pileup(sam: dict, *, min_mapq: int = 0, min_baseq: int = 0,
           rname: str | None = None) -> list[dict]:
    """Per-reference-position pileup over a parse_sam() result.

    Returns rows sorted in record order of first appearance then position:
    {rname, pos (1-based), depth, counts {A,C,G,T,N + lowercase}, qual_mean,
    mapq_mean, insertions {event: n}, deletions {event: n}, del_depth}."""
    if min_mapq < 0 or min_baseq < 0:
        raise ValueError("min_mapq/min_baseq must be >= 0")
    cols: dict[tuple[str, int], dict] = {}

    def col(rn: str, p: int) -> dict:
        key = (rn, p)
        if key not in cols:
            cols[key] = {"rname": rn, "pos": p, "depth": 0, "counts": {},
                         "_quals": [], "_mapqs": [], "insertions": {},
                         "deletions": {}, "del_depth": 0}
        return cols[key]

    for rec in sam["records"]:
        rn = rec["rname"]
        if rn is None or (rname is not None and rn != rname):
            continue
        if rec["flags"].get("unmapped") or rec["mapq"] < min_mapq:
            continue
        if rec["seq"] is None:
            continue
        reverse = bool(rec["flags"].get("reverse"))
        ref_pos, qpos = rec["pos"], 0
        for length, op in rec["cigar_ops"]:
            if op in ("M", "=", "X"):
                for k in range(length):
                    base = rec["seq"][qpos + k].upper()
                    q = (ord(rec["qual"][qpos + k]) - 33
                         if rec["qual"] is not None else None)
                    if q is not None and q < min_baseq:
                        continue
                    c = col(rn, ref_pos + k)
                    letter = base.lower() if reverse else base
                    c["counts"][letter] = c["counts"].get(letter, 0) + 1
                    c["depth"] += 1
                    if q is not None:
                        c["_quals"].append(q)
                    c["_mapqs"].append(rec["mapq"])
                ref_pos += length
                qpos += length
            elif op == "I":
                ins = rec["seq"][qpos:qpos + length].upper()
                event = f"+{length}{ins}"
                anchor = col(rn, ref_pos - 1) if ref_pos > rec["pos"] \
                    else col(rn, rec["pos"])
                anchor["insertions"][event] = \
                    anchor["insertions"].get(event, 0) + 1
                qpos += length
            elif op == "D":
                event = f"-{length}{'N' * length}"
                anchor = col(rn, ref_pos - 1) if ref_pos > rec["pos"] \
                    else col(rn, rec["pos"])
                anchor["deletions"][event] = \
                    anchor["deletions"].get(event, 0) + 1
                for k in range(length):
                    c = col(rn, ref_pos + k)
                    c["counts"]["*"] = c["counts"].get("*", 0) + 1
                    c["depth"] += 1
                    c["del_depth"] += 1
                    c["_mapqs"].append(rec["mapq"])
                ref_pos += length
            elif op == "N":
                ref_pos += length
            elif op in ("S", "H", "P"):
                qpos += length if op == "S" else 0

    rows = sorted(cols.values(), key=lambda c: (c["rname"], c["pos"]))
    for c in rows:
        quals, mapqs = c.pop("_quals"), c.pop("_mapqs")
        c["qual_mean"] = (round(sum(quals) / len(quals), 3)
                          if quals else None)
        c["mapq_mean"] = round(sum(mapqs) / len(mapqs), 3) if mapqs else None
    return rows


def to_mpileup(rows: list[dict]) -> str:
    """Render rows in mpileup-like text: rname, pos, refbase ('N' - no
    reference available, documented), depth, base string (ACGTN/* with
    lowercase = reverse strand, +lenSEQ / -lenN* events inline), qualities."""
    out = []
    for c in rows:
        parts = []
        for letter, n in sorted(c["counts"].items(),
                                key=lambda kv: -kv[1]):
            parts.append(letter * n)
        bases = "".join(parts)
        for ev, n in c["insertions"].items():
            bases += ev * n
        for ev, n in c["deletions"].items():
            bases += ev * n
        out.append(f"{c['rname']}\t{c['pos']}\tN\t{c['depth']}\t"
                   f"{bases}\t.")
    return "\n".join(out) + ("\n" if out else "")


def variant_sites(rows: list[dict], *, min_depth: int = 1,
                  min_alt_fraction: float = 0.2) -> list[dict]:
    """Positions where a minority base reaches `min_alt_fraction` of depth.
    Reference-free: the majority base is the putative reference, the runner-
    up the putative alt - stated as such, not a substitute for a real
    caller with a reference."""
    out = []
    for c in rows:
        acgt = {b: n for b, n in c["counts"].items() if b.upper() in "ACGT"}
        if c["depth"] < min_depth or len(acgt) < 2:
            continue
        merged: dict[str, int] = {}
        for b, n in acgt.items():
            merged[b.upper()] = merged.get(b.upper(), 0) + n
        ranked = sorted(merged.items(), key=lambda kv: -kv[1])
        major, alt = ranked[0], ranked[1]
        frac = alt[1] / sum(merged.values())
        if frac >= min_alt_fraction:
            out.append({"rname": c["rname"], "pos": c["pos"],
                        "ref_base": major[0], "alt_base": alt[0],
                        "depth": c["depth"], "alt_count": alt[1],
                        "alt_fraction": round(frac, 6)})
    return out
