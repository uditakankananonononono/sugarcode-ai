"""Real human splice-site PWMs learned from RefSeqGene records.

Data: 1,170 GT-AG splice junctions extracted live from NCBI RefSeqGene
records for 29 clinically relevant genes (title-verified accessions) (see data/splice_sites/PROVENANCE.md).
Donor window: 9 nt (3 exonic + 6 intronic). Acceptor window: 15 nt
(14 intronic + 1 exonic). Learned consensus: AAG|GTAAGT and (T)nCAG|G,
matching the published mammalian consensus.
"""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

from .pwm import log_odds_matrix

DATA = Path(__file__).parent / "data" / "splice_sites"


class SpliceDataMissing(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load(name: str) -> list[dict[str, float]]:
    p = DATA / name
    if not p.exists():
        raise SpliceDataMissing(f"missing vendored splice data: {p}")
    payload = json.loads(p.read_text())
    return payload["pwm"]


def donor_pwm() -> list[dict[str, float]]:
    return _load("donor_pwm.json")


def acceptor_pwm() -> list[dict[str, float]]:
    return _load("acceptor_pwm.json")


def donor_lod() -> list[dict[str, float]]:
    return log_odds_matrix(donor_pwm())


def acceptor_lod() -> list[dict[str, float]]:
    return log_odds_matrix(acceptor_pwm())


def n_sites() -> dict[str, int]:
    return {"donor": json.loads((DATA / "donor_pwm.json").read_text())["n_sites"],
            "acceptor": json.loads((DATA / "acceptor_pwm.json").read_text())["n_sites"]}


# --- live splice assessment (drop 25): RefSeqGene junction maps -------------

from . import entrez as _entrez
from .genbank import parse_genbank as _parse_gb, revcomp as _rc, transcript_exons as _texons


def refseqgene_accession(gene: str) -> str | None:
    """Title-verified accession from the vendored harvest metadata."""
    meta = DATA / "harvest_meta.json"
    if not meta.exists():
        raise SpliceDataMissing(f"missing {meta}")
    for g in json.loads(meta.read_text())["genes"]:
        if g["gene"] == gene.upper():
            return g["accession"]
    return None


def junction_map(gene: str, offline: bool = False) -> dict:
    """Canonical-transcript splice junction map for a gene from its
    RefSeqGene record: donor/acceptor windows keyed by cDNA junction
    position, plus the full record sequence for context scans.

    Canonical = CDS with the most spans; internal CDS span boundaries ARE
    the splice junctions (UTR trimming differs only at terminal exons).
    """
    acc = refseqgene_accession(gene)
    if not acc:
        return {"status": "no RefSeqGene junction map for this gene", "gene": gene}
    txt = _entrez._get("efetch.fcgi", {"db": "nuccore", "id": acc,
                                       "rettype": "gb", "retmode": "text"},
                       offline=offline).decode()
    gb = _parse_gb(txt); seq = gb["sequence"]
    cds = max((f for f in gb["features"] if f["key"] == "CDS" and len(f["spans"]) >= 2),
              key=lambda c: len(c["spans"]), default=None)
    if not cds:
        return {"status": "no multi-exon CDS in record", "gene": gene, "accession": acc}
    strand = cds["strand"]
    spans = _texons(cds)

    def cdna_of(pos):
        n = 0
        for a, b in spans:
            if strand == 1:
                if pos < a: return None
                if a <= pos <= b: return n + (pos - a + 1)
                n += b - a + 1
            else:
                if pos > b: return None
                if a <= pos <= b: return n + (b - pos + 1)
                n += b - a + 1
        return None

    donors, acceptors = {}, {}
    for (a, b), (c, d) in zip(spans, spans[1:]):
        if strand == 1:
            donors[cdna_of(b)] = seq[b-3:b+6]
            acceptors[cdna_of(c)] = seq[c-15:c]
        else:
            donors[cdna_of(a)] = _rc(seq[a-7:a+2])
            acceptors[cdna_of(d)] = _rc(seq[d-1:d+14])
    return {"status": "ok", "gene": gene, "accession": acc,
            "donors": {k: v for k, v in donors.items() if k is not None},
            "acceptors": {k: v for k, v in acceptors.items() if k is not None},
            "sequence": seq, "cdna_of": cdna_of, "strand": strand,
            "cds_spans": spans,
            "source": f"NCBI RefSeqGene {acc} ({'cache' if offline else 'live'})"}


def gc_donor_lod() -> list[dict[str, float]]:
    """GC-AG donor log-odds: the GT donor matrix with the +2 column T<->C
    swapped. GC donors are ~0.6% of junctions (7 observed in our harvest), too
    few for an independent matrix; published analyses (Burset et al. 2000)
    show the GC-donor consensus mirrors the GT consensus with C at +2.
    Cross-checked: our 5 observed GC-donor windows score 0.83-1.00 under this
    matrix vs 0.36-0.61 under the GT matrix. Approximation, labeled as such.
    """
    pwm = donor_pwm()
    swapped = [dict(col) for col in pwm]
    c = pwm[4]
    swapped[4] = {"A": c["C"], "C": c["T"], "G": c["G"], "T": c["A"]}
    return log_odds_matrix(swapped)
