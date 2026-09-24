"""ORF and translation toolkit: NCBI genetic codes, six-frame ORF finding.

PROVENANCE
- Genetic code tables vendored in bio/data/genetic_codes/tables.json (NCBI
  transl_table ids 1, 2, 4, 11), extracted PROGRAMMATICALLY from Biopython
  1.88 Bio.Data.CodonTable - see PROVENANCE.md in that directory. NCBI
  source page: https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi
- Translation is oracle-tested against Biopython 1.88 Seq.translate over
  all 64 codons for every vendored table.

CONVENTIONS (stated here, next to every function, and in CLI output)
- Coordinates are 0-based half-open on the INPUT sequence, on both strands.
  An ORF with a stop codon INCLUDES that stop codon in [start, end).
- frame: +1/+2/+3 = forward offsets 0/1/2; -1/-2/-3 = reverse-complement
  offsets 0/1/2.
- starts='atg': ATG is the only start. starts='table': every codon in the
  table's NCBI Starts row (table 11 adds GTG/TTG/ATT/ATC/ATA/CTG). Either
  way the first residue is reported as M (initiator methionine) - the
  standard annotation practice for alternative starts, documented.
- nested='longest' (default): one ORF per stop codon, the longest (the
  first in-frame start upstream of that stop). nested='all': every in-frame
  start upstream of a stop yields its own ORF, sharing the stop.
- allow_truncated=False (default): an ORF must end at a stop codon.
  allow_truncated=True: a start whose frame runs off the end without a
  stop is reported with stop_codon=None and truncated=True, ending at the
  last complete codon (contig-edge partial ORFs).
- min_aa counts amino acids EXCLUDING the stop; the initiator M counts.
- Input is uppercased and U is treated as T. A codon containing any
  non-ACGT base translates to 'X' and is never a start or a stop; the
  frame scan continues through it. A trailing incomplete codon (< 3 nt)
  is dropped by translate().
"""
from __future__ import annotations

import json
from importlib import resources

from .sequence import reverse_complement

_CACHE: dict | None = None


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        with resources.files("sugarcode.bio.data.genetic_codes").joinpath(
                "tables.json").open() as fh:
            _CACHE = json.load(fh)
    return _CACHE


def tables() -> list:
    """Available NCBI transl_table ids."""
    return sorted(int(t) for t in _load())


def genetic_code(table: int = 1) -> dict:
    """One vendored genetic code: {id, name, forward, stops, starts}."""
    t = _load().get(str(table))
    if t is None:
        raise ValueError(f"genetic code table {table} not vendored; "
                         f"available: {tables()}")
    return {"id": table, **t}


def _clean(seq: str) -> str:
    return seq.upper().replace("U", "T")


def translate(seq: str, table: int = 1, cds: bool = False) -> str:
    """Translate DNA/RNA with a vendored NCBI table. Trailing incomplete
    codons are dropped; non-ACGT codons become 'X'. cds=True validates a
    complete CDS: multiple of 3, begins with a start codon of the table,
    ends with a stop, and has no internal stop (ValueError otherwise)."""
    code = genetic_code(table)
    s = _clean(seq)
    if cds:
        if len(s) % 3:
            raise ValueError("CDS length is not a multiple of 3")
        if not s:
            raise ValueError("empty CDS")
        if s[:3] not in code["starts"]:
            raise ValueError(f"CDS does not begin with a start codon of "
                             f"table {table}")
    protein = []
    for i in range(0, len(s) - 2, 3):
        codon = s[i:i + 3]
        if any(c not in "ACGT" for c in codon):
            protein.append("X")
        elif codon in code["stops"]:
            protein.append("*")
        else:
            protein.append(code["forward"][codon])
    aa = "".join(protein)
    if cds:
        if not aa.endswith("*"):
            raise ValueError("CDS does not end with a stop codon")
        if "*" in aa[:-1]:
            raise ValueError("CDS contains an internal stop codon")
    return aa


def _gc(region: str) -> float:
    acgt = [c for c in region if c in "ACGT"]
    if not acgt:
        return 0.0
    return sum(1 for c in acgt if c in "GC") / len(acgt)


def find_orfs(seq: str, table: int = 1, min_aa: int = 1,
              starts: str = "atg", both_strands: bool = True,
              nested: str = "longest",
              allow_truncated: bool = False) -> list:
    """Six-frame ORF finding under the module-docstring conventions.
    Returns a list of ORF dicts sorted by (start, end, strand, frame):
    strand, frame, start, end (0-based half-open input coordinates, stop
    included when present), length_nt, length_aa (stop excluded), gc
    (ACGT bases of the ORF region), start_codon, stop_codon (None when
    truncated), truncated, protein (initiator forced to M)."""
    code = genetic_code(table)
    if starts == "atg":
        start_set = {"ATG"}
    elif starts == "table":
        start_set = set(code["starts"])
    else:
        raise ValueError(f"starts must be 'atg' or 'table', got {starts!r}")
    if nested not in ("longest", "all"):
        raise ValueError(f"nested must be 'longest' or 'all', got {nested!r}")
    if min_aa < 1:
        raise ValueError(f"min_aa must be >= 1, got {min_aa}")
    stop_set = set(code["stops"])
    n = len(seq)
    strands = [("+", _clean(seq))]
    if both_strands:
        strands.append(("-", reverse_complement(_clean(seq))))
    out = []
    for strand, s in strands:
        for offset in range(3):
            codons = [(i, s[i:i + 3]) for i in range(offset, n - 2, 3)]
            open_starts: list[int] = []

            def emit(ci: int, stop_idx: int | None) -> None:
                spos, scodon = codons[ci]
                if stop_idx is not None:
                    epos, ecodon = codons[stop_idx]
                    end_rc = epos + 3
                    stop_codon, truncated = ecodon, False
                else:
                    end_rc = codons[-1][0] + 3
                    stop_codon, truncated = None, True
                len_nt = end_rc - spos
                len_aa = len_nt // 3 - (0 if truncated else 1)
                if len_aa < min_aa:
                    return
                protein = list(translate(
                    s[spos:end_rc - (0 if truncated else 3)], table))
                protein[0] = "M"  # initiator methionine (documented)
                if strand == "+":
                    start, end = spos, end_rc
                    region = _clean(seq)[start:end]
                else:
                    start, end = n - end_rc, n - spos
                    region = _clean(seq)[start:end]
                out.append({
                    "strand": strand,
                    "frame": (offset + 1) if strand == "+" else -(offset + 1),
                    "start": start, "end": end,
                    "length_nt": len_nt, "length_aa": len_aa,
                    "gc": round(_gc(region), 6),
                    "start_codon": scodon,
                    "stop_codon": stop_codon,
                    "truncated": truncated,
                    "protein": "".join(protein),
                })

            for idx, (pos, codon) in enumerate(codons):
                if codon in start_set:
                    open_starts.append(idx)
                if codon in stop_set:
                    chosen = open_starts if nested == "all" else open_starts[:1]
                    for ci in chosen:
                        emit(ci, idx)
                    open_starts = []
            if allow_truncated and open_starts and codons:
                chosen = open_starts if nested == "all" else open_starts[:1]
                for ci in chosen:
                    emit(ci, None)
    out.sort(key=lambda o: (o["start"], o["end"], o["strand"], o["frame"]))
    return out
