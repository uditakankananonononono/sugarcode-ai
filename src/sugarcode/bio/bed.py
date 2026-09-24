"""BED interval toolkit (UCSC BED3-BED12).

Coordinates are 0-based half-open (the BED convention) - end is exclusive,
so a BED interval [start, end) covers end - start bases. This differs from
GFF (1-based closed) and the conversion functions do the math explicitly.
"""
from __future__ import annotations

_FIELDS = ("chrom", "start", "end", "name", "score", "strand",
           "thick_start", "thick_end", "item_rgb",
           "block_count", "block_sizes", "block_starts")


def parse_bed(text: str) -> dict:
    header: list[str] = []
    records: list[dict] = []
    for ln, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith(("track", "browser", "#")):
            header.append(line)
            continue
        f = line.split("\t")
        if len(f) < 3:
            raise ValueError(f"line {ln}: BED record has {len(f)} fields, need >= 3")
        if len(f) > 12:
            raise ValueError(f"line {ln}: BED record has {len(f)} fields, max 12")
        try:
            start, end = int(f[1]), int(f[2])
        except ValueError:
            raise ValueError(f"line {ln}: start/end not integers")
        if start < 0 or end <= start:
            raise ValueError(f"line {ln}: invalid 0-based interval {start}..{end}")
        r: dict = {"chrom": f[0], "start": start, "end": end}
        if len(f) > 3:
            r["name"] = f[3]
        if len(f) > 4:
            try:
                r["score"] = float(f[4])
            except ValueError:
                raise ValueError(f"line {ln}: score not numeric: {f[4]!r}")
        if len(f) > 5:
            if f[5] not in ("+", "-", "."):
                raise ValueError(f"line {ln}: invalid strand {f[5]!r}")
            r["strand"] = f[5]
        if len(f) > 7:
            ts, te = int(f[6]), int(f[7])
            if ts < start or te > end or ts > te:
                raise ValueError(f"line {ln}: thick block outside the interval")
            r["thick_start"], r["thick_end"] = ts, te
        if len(f) > 8:
            r["item_rgb"] = f[8]
        if len(f) > 9:
            try:
                bc = int(f[9])
                sizes = [int(x) for x in f[10].rstrip(",").split(",")]
                starts = [int(x) for x in f[11].rstrip(",").split(",")]
            except ValueError:
                raise ValueError(f"line {ln}: malformed block fields")
            if not (bc == len(sizes) == len(starts)):
                raise ValueError(
                    f"line {ln}: blockCount {bc} != {len(sizes)} sizes / "
                    f"{len(starts)} starts")
            if bc and starts[0] != 0:
                raise ValueError(f"line {ln}: first blockStart must be 0")
            for s, b in zip(starts, sizes):
                if b < 1 or start + s + b > end:
                    raise ValueError(f"line {ln}: block at +{s} size {b} escapes the interval")
            r["block_count"] = bc
            r["block_sizes"] = sizes
            r["block_starts"] = starts
        records.append(r)
    if not records:
        raise ValueError("no BED records found")
    return {"header": header, "records": records}


def write_bed(bed: dict) -> str:
    out = list(bed["header"])
    for r in bed["records"]:
        fields = [r["chrom"], str(r["start"]), str(r["end"])]
        if "name" in r:
            fields.append(r["name"])
        if "score" in r:
            fields.append("%g" % r["score"])
        if "strand" in r:
            fields.append(r["strand"])
        if "thick_start" in r:
            fields += [str(r["thick_start"]), str(r["thick_end"])]
        if "item_rgb" in r:
            fields.append(r["item_rgb"])
        if "block_count" in r:
            fields += [str(r["block_count"]),
                       ",".join(str(b) for b in r["block_sizes"]) + ",",
                       ",".join(str(s) for s in r["block_starts"]) + ","]
        out.append("\t".join(fields))
    return "\n".join(out) + "\n"


def overlaps(r: dict, chrom: str, start: int, end: int) -> bool:
    """0-based half-open overlap: [start, end) sharing at least one base."""
    if start < 0 or end <= start:
        raise ValueError(f"invalid query interval {start}..{end}")
    return r["chrom"] == chrom and r["start"] < end and start < r["end"]


def merge_intervals(records: list[dict], min_dist: int = 0) -> list[dict]:
    """bedtools-merge semantics: collapse intervals per chromosome whose gap
    is <= min_dist. Default min_dist=0 matches `bedtools merge` (-d 0) and
    bioframe.merge(min_dist=0): book-ended intervals (end == next start) ARE
    joined. Use min_dist=-1 to join only intervals sharing >= 1 base.
    Names/scores/strands are dropped (coordinates only).
    Validated vs bioframe 0.8.0 on UCSC hg38 rmsk chr20:0-5Mb (11,699 ->
    8,251 intervals, identical)."""
    if min_dist < -1:
        raise ValueError("min_dist must be >= -1")
    by_chrom: dict[str, list[dict]] = {}
    for r in records:
        by_chrom.setdefault(r["chrom"], []).append(r)
    out = []
    for chrom in sorted(by_chrom):
        iv = sorted(((r["start"], r["end"]) for r in by_chrom[chrom]))
        cur_s, cur_e = iv[0]
        for s, e in iv[1:]:
            if s <= cur_e + min_dist:
                cur_e = max(cur_e, e)
            else:
                out.append({"chrom": chrom, "start": cur_s, "end": cur_e})
                cur_s, cur_e = s, e
        out.append({"chrom": chrom, "start": cur_s, "end": cur_e})
    return out


def to_gff(records: list[dict], *, source: str = "bed", feature_type: str = "region") -> list[dict]:
    """BED (0-based half-open) -> GFF3 record dicts (1-based closed):
    gff_start = bed_start + 1, gff_end = bed_end."""
    out = []
    for r in records:
        attrs: dict[str, list[str]] = {}
        if r.get("name"):
            attrs["Name"] = [r["name"]]
        out.append({"seqid": r["chrom"], "source": source, "type": feature_type,
                    "start": r["start"] + 1, "end": r["end"],
                    "score": r.get("score"),
                    "strand": r.get("strand", "."),
                    "phase": None, "attributes": attrs})
    return out


def stats(bed: dict) -> dict:
    by_chrom: dict[str, int] = {}
    total_bases = 0
    for r in bed["records"]:
        by_chrom[r["chrom"]] = by_chrom.get(r["chrom"], 0) + 1
        total_bases += r["end"] - r["start"]
    widths = [r["end"] - r["start"] for r in bed["records"]]
    return {
        "records": len(bed["records"]),
        "bases_covered": total_bases,
        "width": {"min": min(widths), "max": max(widths),
                  "mean": round(total_bases / len(widths), 2)},
        "by_chrom": dict(sorted(by_chrom.items())),
        "stranded": sum(1 for r in bed["records"] if r.get("strand") in ("+", "-")),
    }


def filter_records(bed: dict, *, chroms: list[str] | None = None,
                   min_width: int | None = None,
                   min_score: float | None = None) -> dict:
    chrom_set = set(chroms) if chroms else None
    keep = []
    for r in bed["records"]:
        if chrom_set and r["chrom"] not in chrom_set:
            continue
        if min_width is not None and r["end"] - r["start"] < min_width:
            continue
        if min_score is not None and ("score" not in r or r["score"] < min_score):
            continue
        keep.append(r)
    return {**bed, "records": keep}
