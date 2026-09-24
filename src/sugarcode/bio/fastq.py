"""FASTQ toolkit: parse/stream, Phred quality math, stats, filter, trim.

Quality offsets: auto-detection uses the standard heuristic - any quality
char below ASCII 64 means Phred+33 (a +64 file would never produce those);
a file of only high-quality +64 reads is indistinguishable from +33 and
detects as 33, which is documented, not hidden. Callers can force the
offset explicitly.
"""
from __future__ import annotations

from .sequence import gc_content

_DNA = set("ACGTURYSWKMBDHVNacgturyswkmbdhvn.-")


def parse_fastq(text: str) -> list[dict]:
    records = []
    lines = [ln for ln in text.splitlines()]
    i, n = 0, len(lines)
    while i < n:
        if not lines[i].strip():
            i += 1
            continue
        if not lines[i].startswith("@"):
            raise ValueError(f"line {i + 1}: FASTQ record must start with '@'")
        header = lines[i][1:]
        if i + 3 >= n:
            raise ValueError(f"line {i + 1}: truncated FASTQ record")
        seq, plus, qual = lines[i + 1], lines[i + 2], lines[i + 3]
        if not plus.startswith("+"):
            raise ValueError(f"line {i + 3}: expected '+' separator, got {plus[:20]!r}")
        if len(seq) != len(qual):
            raise ValueError(
                f"line {i + 2}: sequence ({len(seq)} bp) and quality "
                f"({len(qual)} chars) lengths differ")
        bad = set(seq) - _DNA
        if bad:
            raise ValueError(f"line {i + 2}: non-IUPAC sequence chars {sorted(bad)}")
        records.append({"id": header.split()[0] if header else "",
                        "description": header,
                        "sequence": seq.upper(), "quality": qual})
        i += 4
    if not records:
        raise ValueError("no FASTQ records found")
    return records


def stream_fastq(path: str):
    """Streaming FASTQ reader: yields one record at a time (4-line blocks)."""
    with open(path) as fh:
        buf = []
        for line in fh:
            buf.append(line.rstrip("\n"))
            if len(buf) == 4:
                yield from parse_fastq("\n".join(buf) + "\n")
                buf = []
        if buf:
            yield from parse_fastq("\n".join(buf) + "\n")


def write_fastq(records: list[dict]) -> str:
    out = []
    for r in records:
        desc = r.get("description") or r["id"]
        out.append(f"@{desc}")
        out.append(r["sequence"])
        out.append("+")
        out.append(r["quality"])
    return "\n".join(out) + "\n"


def detect_offset(qualities: list[str]) -> int | None:
    """Return 33 when the data proves Phred+33 (any char below ASCII 64),
    else None: an all-high-quality file is compatible with both encodings,
    and the +64 case must be forced by the caller. Honest ambiguity, not a
    guess."""
    for q in qualities:
        if any(ord(c) < 64 for c in q):
            return 33
    return None


def phred_scores(quality: str, offset: int = 33) -> list[int]:
    if offset not in (33, 64):
        raise ValueError("offset must be 33 or 64")
    scores = [ord(c) - offset for c in quality]
    if any(s < 0 for s in scores):
        raise ValueError(f"quality char below the Phred+{offset} baseline")
    return scores


def mean_phred(record: dict, offset: int = 33) -> float:
    s = phred_scores(record["quality"], offset)
    return sum(s) / len(s) if s else 0.0


def stats(records: list[dict], offset: int | None = None) -> dict:
    """FastQC-style summary over parsed records."""
    note = None
    if offset is None:
        detected = detect_offset([r["quality"] for r in records])
        if detected is None:
            offset = 33
            note = ("offset ambiguous (all quality chars >= ASCII 64); "
                    "assumed Phred+33 - pass offset=64 explicitly if this is "
                    "a legacy +64 file")
        else:
            offset = detected
    lengths = [len(r["sequence"]) for r in records]
    seqs = "".join(r["sequence"] for r in records)
    all_scores: list[int] = []
    per_pos: list[list[int]] = []
    for r in records:
        s = phred_scores(r["quality"], offset)
        all_scores.extend(s)
        for i, v in enumerate(s):
            while len(per_pos) <= i:
                per_pos.append([])
            per_pos[i].append(v)
    n_bases = seqs.count("N")
    return {
        "reads": len(records),
        "bases": sum(lengths),
        "offset": offset,
        "length": {"min": min(lengths), "max": max(lengths),
                   "mean": round(sum(lengths) / len(lengths), 2)},
        "gc": round(gc_content(seqs), 4),
        "n_fraction": round(n_bases / len(seqs), 6) if seqs else 0.0,
        "mean_phred": round(sum(all_scores) / len(all_scores), 2),
        "per_position_mean_phred": [round(sum(p) / len(p), 2) for p in per_pos],
        "offset_note": note,
    }


def filter_reads(records: list[dict], *, min_mean_phred: float | None = None,
                 min_len: int | None = None, max_len: int | None = None,
                 max_n_frac: float | None = None,
                 offset: int = 33) -> list[dict]:
    keep = []
    for r in records:
        L = len(r["sequence"])
        if min_len is not None and L < min_len:
            continue
        if max_len is not None and L > max_len:
            continue
        if max_n_frac is not None and L and r["sequence"].count("N") / L > max_n_frac:
            continue
        if min_mean_phred is not None and mean_phred(r, offset) < min_mean_phred:
            continue
        keep.append(r)
    return keep


def trim_reads(records: list[dict], *, window: int = 4, min_phred: float = 15.0,
               min_len: int = 36, offset: int = 33) -> list[dict]:
    """Trimmomatic-style sliding-window 3' trim: cut at the first window
    (scanning 5'->3') whose mean Phred drops below min_phred; drop reads
    shorter than min_len after trimming."""
    if window < 1:
        raise ValueError("window must be >= 1")
    out = []
    for r in records:
        s = phred_scores(r["quality"], offset)
        cut = len(s)
        if len(s) <= window:
            if sum(s) / len(s) < min_phred:
                cut = 0
        else:
            for i in range(len(s) - window + 1):
                if sum(s[i:i + window]) / window < min_phred:
                    cut = i
                    break
        if cut < min_len:
            continue
        out.append({**r, "sequence": r["sequence"][:cut],
                    "quality": r["quality"][:cut]})
    return out


def to_fasta(records: list[dict]) -> str:
    from .fasta import write_fasta
    return write_fasta([{"id": r["id"], "description": r.get("description") or r["id"],
                         "sequence": r["sequence"]} for r in records])
