"""Minimal GenBank flat-file parser: sequence, feature joins, qualifiers."""
from __future__ import annotations
import re


def parse_genbank(text: str) -> dict:
    seq_lines, in_origin = [], False
    features = []
    cur = None
    in_features = False
    for line in text.splitlines():
        if line.startswith("FEATURES"):
            in_features = True
            continue
        if line.startswith("ORIGIN"):
            in_features = False
            if cur: features.append(cur); cur = None
            in_origin = True
            continue
        if line.startswith("//"):
            break
        if in_origin:
            seq_lines.append(re.sub(r"[^acgtACGTnN]", "", line))
            continue
        if in_features:
            if line[:5].strip() == "" and line[5:6].strip():
                if cur: features.append(cur)
                cur = {"key": line[5:21].strip(), "loc": line[21:].strip(), "qualifiers": {}}
            elif cur is not None:
                s = line[21:].strip() if len(line) > 21 else line.strip()
                if s.startswith("/"):
                    m = re.match(r"/([^=]+)=?(.*)", s)
                    if m:
                        cur["qualifiers"][m.group(1)] = m.group(2).strip().strip('"')
                else:
                    cur["loc"] += s
    if cur: features.append(cur)
    out = {"sequence": "".join(seq_lines).upper(), "features": []}
    for f in features:
        loc = f["loc"]
        strand = -1 if loc.startswith("complement") else 1
        spans = [(int(a), int(b)) for a, b in re.findall(r"(\d+)\.\.(\d+)", loc)]
        if not spans and re.fullmatch(r"(?:complement\()?\d+\)?", loc):
            n = int(re.search(r"(\d+)", loc).group(1)); spans = [(n, n)]
        f["strand"] = strand; f["spans"] = spans
        out["features"].append(f)
    return out


RC = str.maketrans("ACGTN", "TGCAN")


def revcomp(s: str) -> str:
    return s.translate(RC)[::-1]


def transcript_exons(feat: dict) -> list[tuple[int, int]]:
    """Exon spans in transcription order (5'->3')."""
    spans = feat["spans"]
    return list(reversed(spans)) if feat["strand"] == -1 else spans
