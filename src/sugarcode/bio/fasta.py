"""FASTA parsing and serialization."""
from __future__ import annotations


def parse_fasta(text: str) -> list[dict]:
    records = []
    header, buf = None, []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append({"id": header.split()[0], "description": header, "sequence": "".join(buf).upper()})
            header, buf = line[1:], []
        else:
            if header is None:
                raise ValueError("FASTA sequence data encountered before any header")
            buf.append(line)
    if header is not None:
        records.append({"id": header.split()[0], "description": header, "sequence": "".join(buf).upper()})
    if not records:
        raise ValueError("no FASTA records found")
    return records


def write_fasta(records: list[dict], line_width: int = 60) -> str:
    out = []
    for r in records:
        desc = r.get("description") or r["id"]
        out.append(f">{desc}")
        seq = r["sequence"]
        out.extend(seq[i:i + line_width] for i in range(0, len(seq), line_width))
    return "\n".join(out) + "\n"


def stream_fasta(path: str):
    """Streaming FASTA reader: yields {id, description, sequence} one record at
    a time without loading the file - the honest way to scan large backgrounds
    (chromosomes, genomes) that do not fit comfortably in memory."""
    with open(path) as fh:
        header, chunks = None, []
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if header is not None:
                    yield {"id": header.split()[0],
                           "description": header,
                           "sequence": "".join(chunks)}
                header, chunks = line[1:], []
            elif line:
                chunks.append(line.strip())
        if header is not None:
            yield {"id": header.split()[0], "description": header,
                   "sequence": "".join(chunks)}
