"""GFF3/GTF annotation toolkit: reader, writer, hierarchy, interval queries.

Format detection per line: GFF3 attributes are key=value; GTF attributes are
key "value";. Attribute values are percent-unescaped on read and
percent-escaped on write (GFF3 spec sec 1.6), so parse -> write -> parse is
an exact roundtrip for well-formed input.
"""
from __future__ import annotations

_ENCODINGS = {"%": "%25", "\t": "%09", "\n": "%0A", "\r": "%0D",
              ";": "%3B", "=": "%3D", "&": "%26", ",": "%2C", " ": "%20"}
_DECODINGS = {v: k for k, v in _ENCODINGS.items()}


def escape_attr(s: str) -> str:
    out = s
    for k, v in _ENCODINGS.items():
        out = out.replace(k, v)
    return out


def unescape_attr(s: str) -> str:
    """Single-pass decode: %25 -> % and stops, so a literal '%2520' in the
    file correctly means the two characters '%20', not a space."""
    out, i = [], 0
    while i < len(s):
        if s[i] == "%" and s[i:i + 3] in _DECODINGS:
            out.append(_DECODINGS[s[i:i + 3]])
            i += 3
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _parse_attributes(field: str, ln: int) -> tuple[str, dict]:
    """Returns (format, attrs). GFF3: key=value;...  GTF: key "value"; ..."""
    field = field.strip()
    if field in ("", "."):
        return "gff3", {}
    attrs: dict[str, list[str]] = {}
    first = field.split(";", 1)[0]
    is_gff3 = "=" in first and ('"' not in first or first.index("=") < first.index('"'))
    if not is_gff3 and '"' not in first:
        raise ValueError(f"line {ln}: unrecognized attribute syntax {first!r}")
    if not is_gff3:
        fmt = "gtf"
        for item in field.split(";"):
            item = item.strip()
            if not item:
                continue
            parts = item.split(None, 1)
            if len(parts) != 2 or not parts[1].startswith('"') or not parts[1].endswith('"'):
                raise ValueError(f"line {ln}: malformed GTF attribute {item!r}")
            attrs.setdefault(parts[0], []).append(unescape_attr(parts[1][1:-1]))
    else:
        fmt = "gff3"
        for item in field.split(";"):
            if not item:
                continue
            if "=" not in item:
                raise ValueError(f"line {ln}: malformed GFF3 attribute {item!r}")
            k, v = item.split("=", 1)
            attrs.setdefault(k, []).extend(
                unescape_attr(x) for x in v.split(","))
    return fmt, attrs


def parse_gff(text: str) -> dict:
    directives: list[str] = []
    comments: list[str] = []
    records: list[dict] = []
    fmt_seen: set[str] = set()
    for ln, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith("##"):
            directives.append(line)
            continue
        if line.startswith("#"):
            comments.append(line)
            continue
        f = line.split("\t")
        if len(f) != 9:
            raise ValueError(f"line {ln}: GFF record has {len(f)} fields, need 9")
        try:
            start, end = int(f[3]), int(f[4])
        except ValueError:
            raise ValueError(f"line {ln}: start/end not integers")
        if start < 1 or end < start:
            raise ValueError(f"line {ln}: invalid coordinates {start}..{end}")
        if f[6] not in ("+", "-", ".", "?"):
            raise ValueError(f"line {ln}: invalid strand {f[6]!r}")
        if f[7] not in ("0", "1", "2", "."):
            raise ValueError(f"line {ln}: invalid phase {f[7]!r}")
        fmt, attrs = _parse_attributes(f[8], ln)
        fmt_seen.add(fmt)
        records.append({
            "seqid": f[0], "source": f[1], "type": f[2],
            "start": start, "end": end,
            "score": None if f[5] == "." else float(f[5]),
            "strand": f[6], "phase": None if f[7] == "." else int(f[7]),
            "attributes": attrs,
        })
    if not records:
        raise ValueError("no GFF records found")
    return {"directives": directives, "comments": comments,
            "format": fmt_seen.pop() if len(fmt_seen) == 1 else "mixed",
            "records": records}


def write_gff(gff: dict) -> str:
    out = list(gff["directives"]) + list(gff["comments"])
    fmt = gff["format"] if gff["format"] != "mixed" else "gff3"
    for r in gff["records"]:
        if fmt == "gtf":
            attr = "; ".join(f'{k} "{escape_attr(v)}"'
                             for k, vals in r["attributes"].items() for v in vals)
            if attr:
                attr += ";"
        else:
            attr = ";".join(f"{k}={','.join(escape_attr(v) for v in vals)}"
                            for k, vals in r["attributes"].items()) or "."
        fields = [r["seqid"], r["source"], r["type"], str(r["start"]),
                  str(r["end"]), "." if r["score"] is None else ("%g" % r["score"]),
                  r["strand"], "." if r["phase"] is None else str(r["phase"]), attr]
        out.append("\t".join(fields))
    return "\n".join(out) + "\n"


def children_of(gff: dict, feature_id: str) -> list[dict]:
    """Direct children: records whose Parent attribute names feature_id."""
    return [r for r in gff["records"]
            if feature_id in r["attributes"].get("Parent", [])]


def descendants_of(gff: dict, feature_id: str) -> list[dict]:
    """Full subtree below feature_id via Parent links (cycle-safe)."""
    out, frontier, seen = [], [feature_id], {feature_id}
    while frontier:
        nxt = []
        for pid in frontier:
            for c in children_of(gff, pid):
                cid = (c["attributes"].get("ID") or [None])[0]
                if cid is not None and cid in seen:
                    continue
                if cid is not None:
                    seen.add(cid)
                out.append(c)
                if cid is not None:
                    nxt.append(cid)
        frontier = nxt
    return out


def overlaps(r: dict, seqid: str, start: int, end: int) -> bool:
    """1-based closed-interval overlap, the GFF coordinate convention."""
    if start < 1 or end < start:
        raise ValueError(f"invalid query coordinates {start}..{end}")
    return r["seqid"] == seqid and r["start"] <= end and start <= r["end"]


def query_region(gff: dict, seqid: str, start: int, end: int,
                 types: list[str] | None = None) -> list[dict]:
    type_set = set(types) if types else None
    return [r for r in gff["records"] if overlaps(r, seqid, start, end)
            and (type_set is None or r["type"] in type_set)]


def stats(gff: dict) -> dict:
    by_type: dict[str, int] = {}
    by_seqid: dict[str, int] = {}
    strands = {"+": 0, "-": 0, ".": 0, "?": 0}
    for r in gff["records"]:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
        by_seqid[r["seqid"]] = by_seqid.get(r["seqid"], 0) + 1
        strands[r["strand"]] += 1
    return {
        "records": len(gff["records"]),
        "format": gff["format"],
        "by_type": dict(sorted(by_type.items())),
        "by_seqid": dict(sorted(by_seqid.items())),
        "strands": strands,
        "span": {s: {"min_start": min(r["start"] for r in gff["records"] if r["seqid"] == s),
                     "max_end": max(r["end"] for r in gff["records"] if r["seqid"] == s)}
                 for s in by_seqid},
    }


def filter_records(gff: dict, *, types: list[str] | None = None,
                   seqids: list[str] | None = None,
                   keep_children: bool = True) -> dict:
    """Filter by type/seqid. keep_children retains the Parent subtree of a
    kept feature so a filtered file stays navigable."""
    type_set = set(types) if types else None
    seq_set = set(seqids) if seqids else None
    keep_ids: set[str] = set()
    kept = []
    for r in gff["records"]:
        if type_set is not None and r["type"] not in type_set:
            continue
        if seq_set is not None and r["seqid"] not in seq_set:
            continue
        kept.append(r)
        rid = (r["attributes"].get("ID") or [None])[0]
        if rid:
            keep_ids.add(rid)
    if keep_children and keep_ids:
        have = {id(r) for r in kept}
        for rid in list(keep_ids):
            for d in descendants_of(gff, rid):
                if id(d) not in have:
                    kept.append(d)
                    have.add(id(d))
        order = {id(r): i for i, r in enumerate(gff["records"])}
        kept.sort(key=lambda r: order[id(r)])
    return {**gff, "records": kept}


def records_to_rows(gff: dict, *, attr_keys: list[str] | None = None) -> list[dict]:
    """Flatten for CSV: fixed columns plus attr_KEY columns (multi-values
    joined with '|')."""
    keys: list[str] = list(attr_keys or [])
    if not keys:
        for r in gff["records"]:
            keys.extend(k for k in r["attributes"] if k not in keys)
    rows = []
    for r in gff["records"]:
        row = {"seqid": r["seqid"], "source": r["source"], "type": r["type"],
               "start": r["start"], "end": r["end"],
               "score": "" if r["score"] is None else r["score"],
               "strand": r["strand"],
               "phase": "" if r["phase"] is None else r["phase"]}
        for k in keys:
            row[f"attr_{k}"] = "|".join(r["attributes"].get(k, []))
        rows.append(row)
    return rows
