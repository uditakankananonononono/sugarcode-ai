"""VCF 4.x toolkit: reader, roundtrip-faithful writer, stats and filters.

Parse keeps INFO/FORMAT values as text except where the header meta declares
a Number=1 Integer/Float (those are coerced). String values are
percent-unescaped on read and percent-escaped on write (VCF 4.3 sec 1.4.3),
so parse -> write -> parse is an exact roundtrip.
"""
from __future__ import annotations

_ENCODINGS = {"%": "%25", ";": "%3B", "=": "%3D", ",": "%2C",
              " ": "%20", "\t": "%09", "\n": "%0A", "\r": "%0D"}
_DECODINGS = {v: k for k, v in _ENCODINGS.items()}


def escape_value(s: str) -> str:
    out = s
    for k, v in _ENCODINGS.items():
        out = out.replace(k, v)
    return out


def unescape_value(s: str) -> str:
    out = s
    for v, k in sorted(_DECODINGS.items(), key=lambda kv: -len(kv[0])):
        out = out.replace(v, k)
    return out


def _parse_meta_angle(body: str) -> dict:
    """Parse the inside of a <...> meta body, honoring quoted strings."""
    out, key, buf, in_q, parts = {}, None, [], False, []
    for ch in body:
        if ch == '"':
            in_q = not in_q
        if ch == "," and not in_q:
            parts.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def parse_vcf(text: str) -> dict:
    meta_lines: list[str] = []
    meta: dict[str, dict] = {"INFO": {}, "FORMAT": {}, "FILTER": {},
                             "ALT": {}, "contig": {}}
    fileformat = None
    columns = samples = None
    records = []
    for ln, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith("##"):
            meta_lines.append(line)
            body = line[2:]
            if body.startswith("fileformat="):
                fileformat = body.split("=", 1)[1]
            elif "=" in body:
                kind, rest = body.split("=", 1)
                if kind in meta and rest.startswith("<") and rest.endswith(">"):
                    entry = _parse_meta_angle(rest[1:-1])
                    if "ID" in entry:
                        meta[kind][entry["ID"]] = entry
            continue
        if line.startswith("#CHROM"):
            columns = line.lstrip("#").split("\t")
            if len(columns) < 8:
                raise ValueError(f"line {ln}: header has {len(columns)} columns, need >= 8")
            samples = columns[9:] if len(columns) > 9 else []
            continue
        if columns is None:
            raise ValueError(f"line {ln}: record before the #CHROM header line")
        f = line.split("\t")
        if len(f) < 8:
            raise ValueError(f"line {ln}: record has {len(f)} fields, need >= 8")
        try:
            pos = int(f[1])
        except ValueError:
            raise ValueError(f"line {ln}: POS is not an integer: {f[1]!r}")
        info: dict = {}
        if f[7] != ".":
            for item in f[7].split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    decl = meta["INFO"].get(k, {})
                    if decl.get("Number") == "1" and decl.get("Type") in ("Integer", "Float"):
                        try:
                            v2 = int(v) if decl["Type"] == "Integer" else float(v)
                        except ValueError:
                            v2 = unescape_value(v)
                        info[k] = v2
                    else:
                        info[k] = unescape_value(v)
                else:
                    info[item] = True
        fmt_keys = f[8].split(":") if len(f) > 8 and f[8] != "." else None
        sample_data = {}
        if fmt_keys:
            for name, cell in zip(samples, f[9:]):
                vals = cell.split(":")
                if len(vals) != len(fmt_keys):
                    raise ValueError(
                        f"line {ln}: sample {name} has {len(vals)} values for "
                        f"{len(fmt_keys)} FORMAT keys")
                sample_data[name] = {k: unescape_value(v) for k, v in zip(fmt_keys, vals)}
        records.append({
            "chrom": f[0], "pos": pos,
            "id": None if f[2] == "." else f[2],
            "ref": f[3],
            "alts": [] if f[4] in (".", "") else f[4].split(","),
            "qual": None if f[5] == "." else float(f[5]),
            "filters": [] if f[6] in (".", "") else f[6].split(";"),
            "info": info,
            "format": fmt_keys,
            "samples": sample_data,
        })
    if columns is None:
        raise ValueError("no #CHROM header line found")
    return {"fileformat": fileformat, "meta": meta, "meta_lines": meta_lines,
            "columns": columns, "samples": samples, "records": records}


def write_vcf(vcf: dict) -> str:
    out = list(vcf["meta_lines"])
    out.append("#" + "\t".join(vcf["columns"]))
    for r in vcf["records"]:
        info = "." if not r["info"] else ";".join(
            k if v is True else f"{k}={escape_value(str(v))}"
            for k, v in r["info"].items())
        fields = [r["chrom"], str(r["pos"]), r["id"] or ".", r["ref"],
                  ",".join(r["alts"]) or ".",
                  "." if r["qual"] is None else ("%g" % r["qual"]),
                  ";".join(r["filters"]) or ".", info]
        if r["format"]:
            fields.append(":".join(r["format"]))
            for name in vcf["samples"]:
                cell = r["samples"][name]
                fields.append(":".join(escape_value(str(cell.get(k) or "."))
                                       if cell.get(k) is not None else "."
                                       for k in r["format"]))
        out.append("\t".join(fields))
    return "\n".join(out) + "\n"


def variant_type(ref: str, alt: str) -> str:
    """snp | mnp | insertion | deletion | indel | symbolic | breakend."""
    if alt.startswith("<") or alt.endswith(">"):
        return "symbolic"
    if "[" in alt or "]" in alt:
        return "breakend"
    if len(ref) == len(alt):
        return "snp" if len(ref) == 1 else "mnp"
    if alt.startswith(ref):
        return "insertion"
    if ref.startswith(alt):
        return "deletion"
    return "indel"


_TRANSITIONS = {("A", "G"), ("G", "A"), ("C", "T"), ("T", "C")}


def is_transition(ref: str, alt: str) -> bool:
    return (ref, alt) in _TRANSITIONS


def stats(vcf: dict) -> dict:
    by_type: dict[str, int] = {}
    ti = tv = 0
    filter_hist: dict[str, int] = {}
    gt_counts: dict[str, dict[str, int]] = {s: {} for s in vcf["samples"]}
    for r in vcf["records"]:
        for alt in r["alts"] or [""]:
            t = variant_type(r["ref"], alt) if alt else "no_call"
            by_type[t] = by_type.get(t, 0) + 1
            if t == "snp":
                if is_transition(r["ref"], alt):
                    ti += 1
                else:
                    tv += 1
        key = ";".join(r["filters"]) or "."
        filter_hist[key] = filter_hist.get(key, 0) + 1
        for s in vcf["samples"]:
            gt = r["samples"].get(s, {}).get("GT")
            if gt is not None:
                gt_counts[s][gt] = gt_counts[s].get(gt, 0) + 1
    return {
        "records": len(vcf["records"]),
        "chroms": sorted({r["chrom"] for r in vcf["records"]}),
        "by_type": dict(sorted(by_type.items())),
        "snps": {"transitions": ti, "transversions": tv,
                 "ti_tv": round(ti / tv, 4) if tv else None},
        "filters": dict(sorted(filter_hist.items())),
        "samples": {s: dict(sorted(c.items())) for s, c in gt_counts.items()},
    }


def filter_records(vcf: dict, *, pass_only: bool = False,
                   min_qual: float | None = None,
                   chroms: list[str] | None = None,
                   types: list[str] | None = None) -> dict:
    """Return a filtered copy; meta/columns are preserved verbatim.
    pass_only keeps records with explicit PASS or missing (".") FILTER -
    the usual convention that unfiltered calls pass."""
    chrom_set = set(chroms) if chroms else None
    type_set = set(types) if types else None
    keep = []
    for r in vcf["records"]:
        if pass_only and r["filters"] not in (["PASS"], []):
            continue
        if min_qual is not None and (r["qual"] is None or r["qual"] < min_qual):
            continue
        if chrom_set and r["chrom"] not in chrom_set:
            continue
        if type_set and not any(variant_type(r["ref"], a) in type_set
                                for a in r["alts"]):
            continue
        keep.append(r)
    return {**vcf, "records": keep}


def records_to_rows(vcf: dict, *, sample: str | None = None) -> list[dict]:
    """Flatten records for CSV/TSV export: fixed columns plus one info_KEY
    column per INFO key present (union, sorted), and fmt_KEY columns when a
    sample is named."""
    if sample is not None and sample not in vcf["samples"]:
        raise ValueError(f"unknown sample {sample!r}; have {vcf['samples']}")
    info_keys: list[str] = []
    fmt_keys: list[str] = []
    for r in vcf["records"]:
        info_keys.extend(k for k in r["info"] if k not in info_keys)
        if sample:
            fmt_keys.extend(k for k in r["samples"].get(sample, {})
                            if k not in fmt_keys)
    rows = []
    for r in vcf["records"]:
        row = {"chrom": r["chrom"], "pos": r["pos"], "id": r["id"] or "",
               "ref": r["ref"], "alt": ",".join(r["alts"]),
               "qual": "" if r["qual"] is None else r["qual"],
               "filter": ";".join(r["filters"])}
        for k in info_keys:
            if k not in r["info"]:
                row[f"info_{k}"] = ""
            else:
                v = r["info"][k]
                row[f"info_{k}"] = "true" if v is True else v
        if sample:
            for k in fmt_keys:
                row[f"fmt_{k}"] = r["samples"].get(sample, {}).get(k, "")
        rows.append(row)
    return rows
