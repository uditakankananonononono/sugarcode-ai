"""SAM alignment toolkit (text SAM only - BAM is binary and out of scope).

SAM coordinates are 1-based (POS); CIGAR reference-consuming ops are
M D N = X. Conversion helpers do the coordinate math explicitly.
"""
from __future__ import annotations

FLAG_BITS = {
    "paired": 0x1, "proper_pair": 0x2, "unmapped": 0x4, "mate_unmapped": 0x8,
    "reverse": 0x10, "mate_reverse": 0x20, "read1": 0x40, "read2": 0x80,
    "secondary": 0x100, "qcfail": 0x200, "duplicate": 0x400,
    "supplementary": 0x800,
}
_CIGAR_OPS = set("MIDNSHP=X")
_REF_CONSUMING = set("MDN=X")
_QUERY_CONSUMING = set("MIS=X")
_TAG_TYPES = {"A", "i", "f", "Z", "H", "B"}


def decode_flags(flag: int) -> dict:
    if not 0 <= flag <= 0xFFFF:
        raise ValueError(f"flag {flag} outside 16 bits")
    return {name: bool(flag & bit) for name, bit in FLAG_BITS.items()}


def encode_flags(**flags) -> int:
    unknown = set(flags) - set(FLAG_BITS)
    if unknown:
        raise ValueError(f"unknown flag names {sorted(unknown)}")
    out = 0
    for name, on in flags.items():
        if on:
            out |= FLAG_BITS[name]
    return out


def parse_cigar(cigar: str) -> list[tuple[int, str]]:
    if cigar == "*":
        return []
    out, num = [], ""
    for ch in cigar:
        if ch.isdigit():
            num += ch
        elif ch in _CIGAR_OPS:
            if not num:
                raise ValueError(f"CIGAR op {ch!r} without a length in {cigar!r}")
            out.append((int(num), ch))
            num = ""
        else:
            raise ValueError(f"invalid CIGAR char {ch!r} in {cigar!r}")
    if num:
        raise ValueError(f"CIGAR {cigar!r} ends with a bare length")
    if not out:
        raise ValueError(f"CIGAR {cigar!r} has no operations")
    return out


def cigar_reference_length(ops: list[tuple[int, str]]) -> int:
    return sum(n for n, op in ops if op in _REF_CONSUMING)


def cigar_query_length(ops: list[tuple[int, str]]) -> int:
    return sum(n for n, op in ops if op in _QUERY_CONSUMING)


def _parse_tag(field: str, ln: int) -> tuple[str, str, object]:
    """Returns (name, sam_type, value). i/f are coerced to int/float;
    A/Z/H/B keep their raw text with the declared type preserved so the
    writer can re-emit the exact tag."""
    parts = field.split(":", 2)
    if len(parts) != 3 or parts[1] not in _TAG_TYPES:
        raise ValueError(f"line {ln}: malformed optional tag {field!r}")
    name, typ, raw = parts
    if typ == "i":
        try:
            return name, typ, int(raw)
        except ValueError:
            raise ValueError(f"line {ln}: tag {name} declares i but is {raw!r}")
    if typ == "f":
        try:
            return name, typ, float(raw)
        except ValueError:
            raise ValueError(f"line {ln}: tag {name} declares f but is {raw!r}")
    return name, typ, raw


def parse_sam(text: str) -> dict:
    header: dict[str, list] = {"HD": [], "SQ": [], "RG": [], "PG": [], "CO": []}
    records: list[dict] = []
    for ln, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith("@"):
            kind = line[1:3]
            if kind not in header:
                raise ValueError(f"line {ln}: unknown header record {kind!r}")
            if kind == "CO":
                header[kind].append({"text": line.split("\t", 1)[1]
                                     if "\t" in line else ""})
                continue
            fields = {}
            for item in line.split("\t")[1:]:
                if ":" in item:
                    k, v = item.split(":", 1)
                    fields[k] = v
            header[kind].append(fields)
            continue
        f = line.split("\t")
        if len(f) < 11:
            raise ValueError(f"line {ln}: alignment has {len(f)} fields, need >= 11")
        try:
            flag, pos, mapq = int(f[1]), int(f[3]), int(f[4])
        except ValueError:
            raise ValueError(f"line {ln}: FLAG/POS/MAPQ not integers")
        if f[2] != "*" and pos < 1:
            raise ValueError(f"line {ln}: mapped record with POS {pos}")
        ops = parse_cigar(f[5])
        tags: dict[str, object] = {}
        tag_types: dict[str, str] = {}
        for field in f[11:]:
            k, typ, v = _parse_tag(field, ln)
            tags[k] = v
            tag_types[k] = typ
        records.append({
            "qname": f[0], "flag": flag, "flags": decode_flags(flag),
            "rname": None if f[2] == "*" else f[2],
            "pos": pos, "mapq": mapq, "cigar": f[5], "cigar_ops": ops,
            "rnext": f[6], "pnext": int(f[7]), "tlen": int(f[8]),
            "seq": None if f[9] == "*" else f[9],
            "qual": None if f[10] == "*" else f[10],
            "tags": tags, "tag_types": tag_types,
        })
    if not records:
        raise ValueError("no SAM alignments found")
    return {"header": header, "records": records}


def alignment_end(record: dict) -> int | None:
    """1-based inclusive end on the reference (POS + ref-consuming - 1),
    None for unmapped reads."""
    if record["rname"] is None or not record["cigar_ops"]:
        return None
    return record["pos"] + cigar_reference_length(record["cigar_ops"]) - 1


def write_sam(sam: dict) -> str:
    out = []
    for kind in ("HD", "SQ", "RG", "PG", "CO"):
        for entry in sam["header"][kind]:
            if kind == "CO" and "text" in entry:
                out.append(f"@CO\t{entry['text']}")
            else:
                out.append("@" + kind + "\t" +
                           "\t".join(f"{k}:{v}" for k, v in entry.items()))
    for r in sam["records"]:
        fields = [r["qname"], str(r["flag"]), r["rname"] or "*",
                  str(r["pos"]), str(r["mapq"]), r["cigar"],
                  r["rnext"], str(r["pnext"]), str(r["tlen"]),
                  r["seq"] or "*", r["qual"] or "*"]
        for k, v in r["tags"].items():
            fields.append(f"{k}:{r['tag_types'].get(k, 'Z')}:{v}")
        out.append("\t".join(fields))
    return "\n".join(out) + "\n"


def stats(sam: dict) -> dict:
    mapped = [r for r in sam["records"] if not r["flags"]["unmapped"]]
    by_rname: dict[str, int] = {}
    for r in mapped:
        by_rname[r["rname"]] = by_rname.get(r["rname"], 0) + 1
    mapqs = [r["mapq"] for r in mapped]
    n = len(sam["records"])
    return {
        "reads": n,
        "mapped": len(mapped),
        "unmapped": n - len(mapped),
        "mapped_rate": round(len(mapped) / n, 4) if n else 0.0,
        "mapq": {"min": min(mapqs), "max": max(mapqs),
                 "mean": round(sum(mapqs) / len(mapqs), 2)} if mapqs else None,
        "by_rname": dict(sorted(by_rname.items())),
        "proper_pairs": sum(1 for r in sam["records"] if r["flags"]["proper_pair"]),
        "duplicates": sum(1 for r in sam["records"] if r["flags"]["duplicate"]),
        "secondary": sum(1 for r in sam["records"] if r["flags"]["secondary"]),
        "supplementary": sum(1 for r in sam["records"] if r["flags"]["supplementary"]),
    }


def filter_records(sam: dict, *, mapped_only: bool = False,
                   min_mapq: int | None = None,
                   rnames: list[str] | None = None,
                   primary_only: bool = False) -> dict:
    rname_set = set(rnames) if rnames else None
    keep = []
    for r in sam["records"]:
        if mapped_only and r["flags"]["unmapped"]:
            continue
        if primary_only and (r["flags"]["secondary"] or r["flags"]["supplementary"]):
            continue
        if min_mapq is not None and (r["flags"]["unmapped"] or r["mapq"] < min_mapq):
            continue
        if rname_set and r["rname"] not in rname_set:
            continue
        keep.append(r)
    return {**sam, "records": keep}


def to_bed(sam: dict) -> list[dict]:
    """Mapped reads -> BED6 intervals. SAM POS is 1-based: bed_start =
    POS - 1, bed_end = bed_start + CIGAR reference length."""
    out = []
    for r in sam["records"]:
        if r["flags"]["unmapped"] or r["rname"] is None:
            continue
        start = r["pos"] - 1
        out.append({"chrom": r["rname"], "start": start,
                    "end": start + cigar_reference_length(r["cigar_ops"]),
                    "name": r["qname"], "score": float(r["mapq"]),
                    "strand": "-" if r["flags"]["reverse"] else "+"})
    return out
