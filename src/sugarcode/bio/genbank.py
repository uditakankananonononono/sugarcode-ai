"""Minimal GenBank flat-file parser: sequence, feature joins, qualifiers."""
from __future__ import annotations
import re


_PART = re.compile(r"(?<![A-Za-z0-9_.:])(complement\()?[<>]?(\d+)(?:(?:\.\.|\^)[<>]?(\d+))?")


def parse_location(loc: str) -> tuple[list[tuple[int, int]], int]:
    """INSDC location -> (1-based closed spans in file order, strand).

    Handles join/order, complement() around the whole location or around
    every part, partial ends (<1..>200), single bases (123), between-base
    sites (123^124) and skips parts on other records (J00194.1:100..202)."""
    loc = re.sub(r"\s+", "", loc)
    body = loc
    outer = body.startswith("complement(") and body.endswith(")")
    if outer:
        body = body[len("complement("):-1]
    spans, inner = [], []
    for m in _PART.finditer(body):
        a = int(m.group(2)); b = int(m.group(3)) if m.group(3) else a
        if "^" in m.group(0):
            b = a  # between-base site: anchor on the left base
        spans.append((a, b)); inner.append(bool(m.group(1)))
    strand = -1 if outer or (inner and all(inner)) else 1
    return spans, strand


def parse_genbank(text: str) -> dict:
    """Parse the first record of a GenBank flat file.

    Multi-line qualifier values are joined the INSDC way: /translation
    lines are concatenated without spaces, other values with one space.
    The ORIGIN sequence keeps every IUPAC letter so coordinates never shift."""
    seq_lines, in_origin = [], False
    features = []
    cur = None
    qkey = None      # qualifier currently being continued
    in_features = False
    def _close_q():
        if cur is not None and qkey is not None:
            v = cur["qualifiers"][qkey]
            if v.startswith('"'):
                v = v[1:-1] if v.endswith('"') and len(v) > 1 else v[1:]
                v = v.replace('""', '"')
            cur["qualifiers"][qkey] = v
    for line in text.splitlines():
        if line.startswith("FEATURES"):
            in_features = True
            continue
        if line.startswith("ORIGIN"):
            in_features = False
            _close_q(); qkey = None
            if cur: features.append(cur); cur = None
            in_origin = True
            continue
        if line.startswith("//"):
            break
        if in_origin:
            seq_lines.append(re.sub(r"[^A-Za-z]", "", line))
            continue
        if in_features:
            if line[:5].strip() == "" and line[5:6].strip():
                _close_q(); qkey = None
                if cur: features.append(cur)
                cur = {"key": line[5:21].strip(), "loc": line[21:].strip(), "qualifiers": {}}
            elif cur is not None:
                s = line[21:].strip() if len(line) > 21 else line.strip()
                open_quote = (qkey is not None and cur["qualifiers"][qkey].startswith('"')
                              and (cur["qualifiers"][qkey].count('"') % 2 == 1))
                if s.startswith("/") and not open_quote:
                    _close_q()
                    m = re.match(r"/([^=]+)=?(.*)", s)
                    qkey = m.group(1)
                    cur["qualifiers"][qkey] = m.group(2).strip()
                elif qkey is not None:
                    sep = "" if qkey == "translation" else " "
                    cur["qualifiers"][qkey] += sep + s
                else:
                    cur["loc"] += s
            elif line[:1].strip():
                in_features = False
    _close_q()
    if cur: features.append(cur)
    out = {"sequence": "".join(seq_lines).upper(), "features": []}
    for f in features:
        f["spans"], f["strand"] = parse_location(f["loc"])
        out["features"].append(f)
    return out


RC = str.maketrans("ACGTN", "TGCAN")


def revcomp(s: str) -> str:
    return s.translate(RC)[::-1]


def transcript_exons(feat: dict) -> list[tuple[int, int]]:
    """Exon spans in transcription order (5'->3')."""
    spans = feat["spans"]
    return list(reversed(spans)) if feat["strand"] == -1 else spans
