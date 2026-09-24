"""Stockholm 1.0 and A3M multiple-sequence-alignment toolkit.

Two sibling alignment formats:

- Stockholm 1.0 (Pfam/Rfam): ``# STOCKHOLM 1.0`` header, named sequences that
  may wrap across blank-line-separated blocks, markup lines (``#=GF`` per
  file, ``#=GS`` per sequence, ``#=GC`` per column, ``#=GR`` per sequence per
  column), and a ``//`` terminator.
- A3M (HH-suite): FASTA-like, one sequence per record; lowercase letters mark
  insertions relative to the master sequence (record 1), ``-`` is a gap and
  ``.`` is an alignment-padding gap. Deleting lowercase letters and ``.``
  characters yields the aligned match-state view (A2M/AFA).

Both parsers preserve case and validate widths with line-numbered errors.
Writers are semantically roundtrip-faithful: parse -> write -> parse yields an
equal structure (byte-exactness of wrapping/order is not promised, because
Stockholm permits arbitrary block layouts).
"""
from __future__ import annotations

_GAP_CHARS = set("-.")


def parse_stockholm(text: str) -> dict:
    """Parse Stockholm 1.0 text into an alignment dict:
    {seqs: [(name, seq)], gf: {tag: value}, gs: {tag: {name: value}},
     gc: {tag: colstring}, gr: {tag: {name: colstring}}}."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# STOCKHOLM 1.0"):
        raise ValueError("Stockholm text must start with '# STOCKHOLM 1.0'")
    seqs: dict[str, list[str]] = {}
    order: list[str] = []
    gf: dict[str, str] = {}
    gs: dict[str, dict[str, str]] = {}
    gc: dict[str, list[str]] = {}
    gr: dict[str, dict[str, list[str]]] = {}
    terminated = False
    for i, line in enumerate(lines[1:], start=2):
        s = line.strip()
        if not s:
            continue
        if s == "//":
            terminated = True
            if any(x.strip() for x in lines[i:]):
                raise ValueError(f"line {i}: content after '//' terminator")
            break
        if s.startswith("#="):
            parts = s.split(None, 2)
            kind = parts[0]
            if kind == "#=GF" and len(parts) == 3:
                gf[parts[1]] = parts[2]
            elif kind == "#=GC" and len(parts) == 3:
                gc.setdefault(parts[1], []).append(parts[2])
            elif kind in ("#=GS", "#=GR") and len(parts) == 3:
                sub = parts[2].split(None, 1)
                if len(sub) != 2:
                    raise ValueError(f"line {i}: malformed {kind} line")
                name, (tag, val) = parts[1], sub
                if kind == "#=GS":
                    gs.setdefault(tag, {})[name] = val
                else:
                    gr.setdefault(tag, {}).setdefault(name, []).append(val)
            else:
                raise ValueError(f"line {i}: malformed markup line {s!r}")
        else:
            parts = s.split(None, 1)
            if len(parts) != 2:
                raise ValueError(f"line {i}: expected 'name sequence-chunk'")
            name, chunk = parts
            if name not in seqs:
                seqs[name] = [chunk.replace(" ", "")]
                order.append(name)
            else:
                seqs[name].append(chunk.replace(" ", ""))
    if not terminated:
        raise ValueError("missing '//' terminator")
    if not order:
        raise ValueError("no sequences found")
    out = {"seqs": [(n, "".join(seqs[n])) for n in order], "gf": gf,
           "gs": gs,
           "gc": {t: "".join(ch) for t, ch in gc.items()},
           "gr": {t: {n: "".join(ch) for n, ch in m.items()}
                  for t, m in gr.items()}}
    _validate_widths(out["seqs"], out["gc"], out["gr"])
    return out


def _validate_widths(seqs, gc, gr) -> None:
    widths = {len(s) for _, s in seqs}
    if len(widths) != 1:
        raise ValueError(f"sequences have inconsistent widths {sorted(widths)}")
    w = widths.pop()
    names = {n for n, _ in seqs}
    for tag, cols in gc.items():
        if len(cols) != w:
            raise ValueError(f"#=GC {tag} width {len(cols)} != alignment {w}")
    for tag, m in gr.items():
        for name, cols in m.items():
            if name not in names:
                raise ValueError(f"#=GR {tag} references unknown sequence "
                                 f"{name!r}")
            if len(cols) != w:
                raise ValueError(f"#=GR {tag} for {name!r} width {len(cols)} "
                                 f"!= alignment {w}")


def write_stockholm(aln: dict) -> str:
    """Write an alignment dict as single-block Stockholm 1.0."""
    seqs = aln["seqs"]
    if not seqs:
        raise ValueError("alignment has no sequences")
    pad = max(len(n) for n, _ in seqs)
    out = ["# STOCKHOLM 1.0"]
    for tag, val in aln.get("gf", {}).items():
        out.append(f"#=GF {tag} {val}")
    for name, seq in seqs:
        out.append(f"{name.ljust(pad)} {seq}")
    for tag, m in aln.get("gs", {}).items():
        for name, val in m.items():
            out.append(f"#=GS {name} {tag} {val}")
    for tag, m in aln.get("gr", {}).items():
        for name, cols in m.items():
            out.append(f"#=GR {name} {tag} {cols}")
    for tag, cols in aln.get("gc", {}).items():
        out.append(f"#=GC {tag} {cols}")
    out.append("//")
    return "\n".join(out) + "\n"


def parse_a3m(text: str) -> list[dict]:
    """Parse A3M/FASTA-like alignment records preserving case (lowercase =
    insertion). Returns [{id, description, sequence}]."""
    records, header, buf = [], None, []
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append({"id": header.split()[0],
                                "description": header,
                                "sequence": "".join(buf)})
            header, buf = line[1:], []
        else:
            if header is None:
                raise ValueError(f"line {i}: sequence before any header")
            buf.append(line)
    if header is not None:
        records.append({"id": header.split()[0], "description": header,
                        "sequence": "".join(buf)})
    if not records:
        raise ValueError("no records found")
    return records


def write_a3m(records: list[dict], line_width: int = 60) -> str:
    out = []
    for r in records:
        out.append(f">{r.get('description') or r['id']}")
        seq = r["sequence"]
        out.extend(seq[i:i + line_width] for i in range(0, len(seq), line_width))
    return "\n".join(out) + "\n"


def a3m_match_states(records: list[dict]) -> list[dict]:
    """A3M -> aligned match-state view: delete lowercase letters and '.'.
    Every resulting sequence must have identical width."""
    out = [{"id": r["id"], "description": r["description"],
            "sequence": "".join(c for c in r["sequence"]
                                if not (c.islower() or c == "."))}
           for r in records]
    widths = {len(r["sequence"]) for r in out}
    if len(widths) != 1:
        raise ValueError(f"match-state widths disagree {sorted(widths)} - "
                         f"input is not a valid A3M alignment")
    return out


def pairwise_identity(a: str, b: str) -> float:
    """Identical residues / non-gap column pairs (HH-suite convention):
    columns where both sequences have a residue; gaps on either side are
    excluded from numerator and denominator."""
    if len(a) != len(b):
        raise ValueError("sequences must have equal width")
    pairs = [(x, y) for x, y in zip(a, b)
             if x not in _GAP_CHARS and y not in _GAP_CHARS]
    if not pairs:
        return 0.0
    return sum(1 for x, y in pairs if x == y) / len(pairs)


def stats(records: list[dict]) -> dict:
    """Alignment summary for a list of {id, sequence} records with equal
    widths (use a3m_match_states first for A3M input)."""
    if not records:
        raise ValueError("no records")
    widths = {len(r["sequence"]) for r in records}
    if len(widths) != 1:
        raise ValueError(f"widths disagree {sorted(widths)}")
    w = widths.pop()
    n = len(records)
    gap = sum(sum(1 for c in r["sequence"] if c in _GAP_CHARS)
              for r in records)
    pids = [pairwise_identity(records[i]["sequence"], records[j]["sequence"])
            for i in range(n) for j in range(i + 1, n)]
    return {"nseq": n, "width": w,
            "gap_fraction": round(gap / (n * w), 6),
            "mean_pairwise_identity": (round(sum(pids) / len(pids), 6)
                                       if pids else 1.0)}


def consensus(records: list[dict], threshold: float = 0.5) -> str:
    """Majority-residue consensus. A column contributes the most frequent
    residue when its frequency among NON-GAP characters reaches `threshold`
    AND residues are the majority of the column; otherwise '-'."""
    if not records:
        raise ValueError("no records")
    w = len(records[0]["sequence"])
    out = []
    for col in range(w):
        chars = [r["sequence"][col] for r in records]
        res = [c for c in chars if c not in _GAP_CHARS]
        if len(res) < len(chars) * threshold or not res:
            out.append("-")
            continue
        top = max(set(res), key=res.count)
        if res.count(top) / len(chars) >= threshold:
            out.append(top)
        else:
            out.append("-")
    return "".join(out)


def filter_columns(records: list[dict], min_occupancy: float) -> list[dict]:
    """Drop columns whose residue occupancy (non-gap fraction) is below
    `min_occupancy`."""
    if not 0.0 <= min_occupancy <= 1.0:
        raise ValueError("min_occupancy must be in [0, 1]")
    n = len(records)
    if not n:
        raise ValueError("no records")
    w = len(records[0]["sequence"])
    keep = [c for c in range(w)
            if sum(1 for r in records if r["sequence"][c] not in _GAP_CHARS)
            / n >= min_occupancy]
    return [{**r, "sequence": "".join(r["sequence"][c] for c in keep)}
            for r in records]


def filter_sequences(records: list[dict], min_coverage: float) -> list[dict]:
    """Drop sequences whose non-gap fraction is below `min_coverage`."""
    if not 0.0 <= min_coverage <= 1.0:
        raise ValueError("min_coverage must be in [0, 1]")
    out = []
    for r in records:
        s = r["sequence"]
        cov = sum(1 for c in s if c not in _GAP_CHARS) / max(1, len(s))
        if cov >= min_coverage:
            out.append(r)
    return out
