"""Codon usage tables and CAI (Codon Adaptation Index) computation.

Built-in usage frequencies (per-thousand) from the Kazusa-style E. coli K12
and H. sapiens tables; users may supply any custom table.
"""
from __future__ import annotations
import math
from pathlib import Path
from .sequence import STANDARD_CODE, clean_dna

# per-thousand codon frequencies
ECOLI_K12 = {
    "TTT": 22.0, "TTC": 16.0, "TTA": 13.9, "TTG": 13.7, "CTT": 10.9, "CTC": 10.9,
    "CTA": 3.8, "CTG": 52.7, "ATT": 29.8, "ATC": 24.2, "ATA": 4.8, "ATG": 27.8,
    "GTT": 18.1, "GTC": 15.3, "GTA": 11.2, "GTG": 26.4, "TCT": 8.6, "TCC": 8.9,
    "TCA": 7.6, "TCG": 8.8, "CCT": 7.2, "CCC": 5.5, "CCA": 8.4, "CCG": 23.2,
    "ACT": 9.0, "ACC": 23.3, "ACA": 7.5, "ACG": 14.4, "GCT": 18.6, "GCC": 25.5,
    "GCA": 21.2, "GCG": 32.7, "TAT": 16.0, "TAC": 12.2, "TAA": 2.0, "TAG": 0.3,
    "CAT": 12.8, "CAC": 9.7, "CAA": 15.3, "CAG": 29.5, "AAT": 18.3, "AAC": 21.7,
    "AAA": 33.2, "AAG": 12.1, "GAT": 32.1, "GAC": 19.1, "GAA": 39.6, "GAG": 17.9,
    "TGT": 5.2, "TGC": 6.5, "TGA": 1.0, "TGG": 15.2, "CGT": 20.8, "CGC": 21.6,
    "CGA": 3.7, "CGG": 5.6, "AGT": 8.7, "AGC": 15.9, "AGA": 4.4, "AGG": 2.4,
    "GGT": 24.7, "GGC": 28.0, "GGA": 8.2, "GGG": 11.4,
}

H_SAPIENS = {
    "TTT": 17.6, "TTC": 20.3, "TTA": 7.7, "TTG": 12.9, "CTT": 13.2, "CTC": 19.6,
    "CTA": 7.2, "CTG": 39.6, "ATT": 16.0, "ATC": 20.8, "ATA": 7.5, "ATG": 22.0,
    "GTT": 11.0, "GTC": 14.5, "GTA": 7.1, "GTG": 28.1, "TCT": 15.2, "TCC": 17.7,
    "TCA": 12.2, "TCG": 4.4, "CCT": 17.5, "CCC": 19.8, "CCA": 16.9, "CCG": 6.9,
    "ACT": 13.1, "ACC": 18.9, "ACA": 15.1, "ACG": 6.1, "GCT": 18.4, "GCC": 27.7,
    "GCA": 15.8, "GCG": 7.4, "TAT": 12.2, "TAC": 15.3, "TAA": 1.0, "TAG": 0.8,
    "CAT": 10.9, "CAC": 15.1, "CAA": 12.3, "CAG": 34.2, "AAT": 17.0, "AAC": 19.1,
    "AAA": 24.4, "AAG": 31.9, "GAT": 21.8, "GAC": 25.1, "GAA": 29.0, "GAG": 39.6,
    "TGT": 10.6, "TGC": 12.6, "TGA": 1.6, "TGG": 13.2, "CGT": 4.5, "CGC": 10.4,
    "CGA": 6.2, "CGG": 11.4, "AGT": 12.1, "AGC": 19.5, "AGA": 12.2, "AGG": 12.0,
    "GGT": 10.8, "GGC": 22.2, "GGA": 16.5, "GGG": 16.5,
}

HOST_TABLES = {"ecoli_k12": ECOLI_K12, "h_sapiens": H_SAPIENS}


def synonymous_codons(aa: str) -> list[str]:
    return [c for c, a in STANDARD_CODE.items() if a == aa]


def relative_adaptiveness(table: dict[str, float]) -> dict[str, float]:
    """w_i = f_i / f_max within each synonymous family (Sharp & Li 1987)."""
    by_aa: dict[str, list[str]] = {}
    for codon, aa in STANDARD_CODE.items():
        by_aa.setdefault(aa, []).append(codon)
    w = {}
    for aa, codons in by_aa.items():
        fmax = max(table.get(c, 0.0) for c in codons)
        for c in codons:
            f = table.get(c, 0.0)
            w[c] = (f / fmax) if fmax > 0 else 0.0
    return w


def cai(seq: str, table: dict[str, float] | None = None) -> float:
    """Codon Adaptation Index of a coding sequence against a usage table."""
    table = table or ECOLI_K12
    w = relative_adaptiveness(table)
    s = clean_dna(seq.replace("U", "T"))
    vals = []
    for i in range(0, len(s) - 2, 3):
        cod = s[i:i + 3]
        aa = STANDARD_CODE.get(cod)
        if aa in (None, "*", "M", "W"):
            continue  # excluded by convention (Met/Trp have w=1 always)
        wi = w.get(cod, 0.0)
        if wi > 0:
            vals.append(math.log(wi))
    if not vals:
        return 0.0
    return math.exp(sum(vals) / len(vals))


def optimize_sequence(protein: str, table: dict[str, float] | None = None,
                      gc_min: float = 0.40, gc_max: float = 0.60,
                      avoid_motifs: list[str] | None = None) -> str:
    """Greedy per-codon optimization toward max relative adaptiveness,
    with GC-window repair and forbidden-motif avoidance."""
    from .sequence import find_motif, gc_content
    table = table or ECOLI_K12
    w = relative_adaptiveness(table)
    avoid = [m.upper() for m in (avoid_motifs or [])]

    def best_codons(aa: str) -> list[str]:
        cods = synonymous_codons(aa)
        return sorted(cods, key=lambda c: -w.get(c, 0.0))

    codon_list = [best_codons(a)[0] for a in protein if a in "ACDEFGHIKLMNPQRSTVWY*"]

    def local_gc(cl: list[str], idx: int, span: int = 10) -> float:
        lo, hi = max(0, idx - span), min(len(cl), idx + span)
        return gc_content("".join(cl[lo:hi]))

    # GC window repair: swap codons in out-of-band windows for second-best synonyms
    for i in range(len(codon_list)):
        g = local_gc(codon_list, i)
        aa = STANDARD_CODE.get(codon_list[i], "")
        if g < gc_min or g > gc_max:
            for alt in best_codons(aa)[1:]:
                trial = codon_list[:i] + [alt] + codon_list[i + 1:]
                g2 = local_gc(trial, i)
                if gc_min <= g2 <= gc_max or abs(g2 - 0.5) < abs(g - 0.5):
                    codon_list = trial
                    break

    seq = "".join(codon_list)
    # forbidden motif removal: mutate wobble position inside the motif
    for motif in avoid:
        hits = find_motif(seq, motif)
        for h in reversed(hits):
            ci = (h + len(motif) - 1) // 3
            if 0 <= ci < len(codon_list):
                aa = STANDARD_CODE.get(codon_list[ci], "")
                for alt in best_codons(aa)[1:]:
                    trial = codon_list[:ci] + [alt] + codon_list[ci + 1:]
                    tseq = "".join(trial)
                    if h not in find_motif(tseq, motif):
                        codon_list = trial
                        seq = tseq
                        break
    return "".join(codon_list)


# --- published tables (Edinburgh Genome Foundry codon-usage-tables, see
# bio/data/codon_tables/PROVENANCE.md) -----------------------------------------
_DATA_DIR = Path(__file__).parent / "data" / "codon_tables"


def load_published_table(species: str) -> dict[str, float]:
    """Load a vendored published codon table (relative frequency per AA).

    species: 'e_coli', 'h_sapiens' or 's_cerevisiae'. RNA codons are converted
    to DNA. Values are relative frequencies within each amino acid - directly
    usable for CAI/relative-adaptiveness (which normalizes per AA anyway)."""
    import csv
    f = _DATA_DIR / f"{species}.csv"
    if not f.exists():
        raise ValueError(f"no published table for {species!r}; have e_coli, h_sapiens, s_cerevisiae")
    out = {}
    for row in csv.DictReader(open(f)):
        out[row["codon"].replace("U", "T")] = float(row["relative_frequency"])
    return out


ECOLI_PUBLISHED = load_published_table("e_coli_316407")
HUMAN_PUBLISHED = load_published_table("h_sapiens_9606")
YEAST_PUBLISHED = load_published_table("s_cerevisiae_4932")
# Sharp & Li-style highly-expressed reference: codon usage of 36 ribosomal-protein
# CDS (rpl/rps/rpm) from NCBI GCF_000005845.2. On PaxDb integrated E. coli protein
# abundance (n=3453 non-ribosomal genes) CAI Spearman rises 0.496 -> 0.580 vs the
# genome-wide table (mega27-01 benchmarks/sweep_codon_cai.json).
ECOLI_HIGHEXPR = load_published_table("e_coli_highexpr_ribo")

# published tables become the canonical defaults; memory-built tables kept as
# named legacy fallbacks
ECOLI_LEGACY = ECOLI_K12
H_SAPIENS_LEGACY = H_SAPIENS
HOST_TABLES.update({
    "ecoli_highexpr": ECOLI_HIGHEXPR,
    "ecoli": ECOLI_PUBLISHED, "ecoli_published": ECOLI_PUBLISHED,
    "h_sapiens_published": HUMAN_PUBLISHED, "human": HUMAN_PUBLISHED,
    "s_cerevisiae": YEAST_PUBLISHED, "yeast": YEAST_PUBLISHED,
    "ecoli_legacy": ECOLI_LEGACY, "h_sapiens_legacy": H_SAPIENS_LEGACY,
})
