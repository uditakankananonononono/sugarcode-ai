"""Core nucleic-acid / protein sequence operations. Pure stdlib + numpy."""
from __future__ import annotations

DNA_COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")
RNA_COMPLEMENT = str.maketrans("ACGUNacgun", "UGCANugcan")

STANDARD_CODE: dict[str, str] = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}

AA_NAMES = {
    "A": "Alanine", "R": "Arginine", "N": "Asparagine", "D": "Aspartate",
    "C": "Cysteine", "Q": "Glutamine", "E": "Glutamate", "G": "Glycine",
    "H": "Histidine", "I": "Isoleucine", "L": "Leucine", "K": "Lysine",
    "M": "Methionine", "F": "Phenylalanine", "P": "Proline", "S": "Serine",
    "T": "Threonine", "W": "Tryptophan", "Y": "Tyrosine", "V": "Valine",
    "*": "Stop",
}

# Kyte-Doolittle hydrophobicity
AA_HYDROPHOBICITY = {
    "I": 4.5, "V": 4.2, "L": 3.8, "F": 2.8, "C": 2.5, "M": 1.9, "A": 1.8,
    "G": -0.4, "T": -0.7, "S": -0.8, "W": -0.9, "Y": -1.3, "P": -1.6,
    "H": -3.2, "E": -3.5, "Q": -3.5, "D": -3.5, "N": -3.5, "K": -3.9, "R": -4.5,
}

AA_MASS = {
    "A": 89.09, "R": 174.20, "N": 132.12, "D": 133.10, "C": 121.16,
    "Q": 146.15, "E": 147.13, "G": 75.07, "H": 155.16, "I": 131.17,
    "L": 131.17, "K": 146.19, "M": 149.21, "F": 165.19, "P": 115.13,
    "S": 105.09, "T": 119.12, "W": 204.23, "Y": 181.19, "V": 117.15,
}


def clean_dna(seq: str) -> str:
    s = "".join(c for c in seq.upper() if c in "ACGTN")
    if not s:
        raise ValueError("sequence contains no valid DNA bases")
    return s


def reverse_complement(seq: str) -> str:
    return seq.translate(DNA_COMPLEMENT)[::-1]


def transcribe(dna: str) -> str:
    """DNA coding strand -> mRNA (5'->3')."""
    return clean_dna(dna).replace("T", "U")


def translate(dna_or_rna: str, reading_frame: int = 0, to_stop: bool = False) -> str:
    """Translate nucleotides -> amino acids using the standard genetic code."""
    s = clean_dna(dna_or_rna.replace("U", "T"))
    if reading_frame not in (0, 1, 2):
        raise ValueError("reading_frame must be 0, 1 or 2")
    s = s[reading_frame:]
    aas = []
    for i in range(0, len(s) - 2, 3):
        codon = s[i:i + 3]
        aa = STANDARD_CODE.get(codon, "X")
        if aa == "*" and to_stop:
            break
        aas.append(aa)
    return "".join(aas)


def gc_content(seq: str) -> float:
    s = clean_dna(seq.replace("U", "T"))
    gc = s.count("G") + s.count("C")
    atgc = sum(s.count(b) for b in "ACGT")
    return gc / atgc if atgc else 0.0


def gc_windows(seq: str, window: int = 50, step: int | None = None) -> list[tuple[int, float]]:
    """GC fraction over sliding windows: list of (start, gc)."""
    s = clean_dna(seq)
    step = step or max(1, window // 2)
    out = []
    for i in range(0, max(1, len(s) - window + 1), step):
        w = s[i:i + window]
        if w:
            out.append((i, gc_content(w)))
    return out


def tm_wallace(seq: str) -> float:
    """Wallace rule melting temperature for short oligos (2*(A+T)+4*(G+C))."""
    s = clean_dna(seq)
    if len(s) > 13:
        # Marmur/Schildkraut long-oligo approximation
        return 64.9 + 41.0 * ((s.count("G") + s.count("C")) - 16.4) / len(s)
    return 2.0 * (s.count("A") + s.count("T")) + 4.0 * (s.count("G") + s.count("C"))


def find_motif(seq: str, motif: str, iupac: bool = True) -> list[int]:
    """All start positions of a (possibly IUPAC-degenerate) motif."""
    table = {
        "A": "A", "C": "C", "G": "G", "T": "T", "U": "T",
        "R": "AG", "Y": "CT", "S": "GC", "W": "AT", "K": "GT", "M": "AC",
        "B": "CGT", "D": "AGT", "H": "ACT", "V": "ACG", "N": "ACGT",
    }
    s = clean_dna(seq.replace("U", "T"))
    motif = motif.upper().replace("U", "T")
    hits = []
    for i in range(len(s) - len(motif) + 1):
        window = s[i:i + len(motif)]
        ok = True
        for mc, bc in zip(motif, window):
            allowed = table.get(mc, mc) if iupac else mc
            if bc not in allowed:
                ok = False
                break
        if ok:
            hits.append(i)
    return hits


def orfs(seq: str, min_aa: int = 30, both_strands: bool = True) -> list[dict]:
    """Open reading frames (ATG..stop) >= min_aa. Returns strand/position/length/protein."""
    found = []
    strands = [("+", clean_dna(seq))]
    if both_strands:
        strands.append(("-", reverse_complement(clean_dna(seq))))
    for strand, s in strands:
        for frame in range(3):
            i = frame
            while i < len(s) - 2:
                if s[i:i + 3] == "ATG":
                    j = i
                    while j < len(s) - 2 and STANDARD_CODE.get(s[j:j + 3]) != "*":
                        j += 3
                    aa_len = (j - i) // 3
                    if aa_len >= min_aa and j < len(s) - 2:
                        found.append({
                            "strand": strand, "frame": frame, "start": i, "end": j + 3,
                            "aa_length": aa_len,
                            "protein": translate(s[i:j]),
                        })
                    i = j + 3
                else:
                    i += 3
    return found


def molecular_weight(protein: str) -> float:
    return sum(AA_MASS.get(a, 0.0) for a in protein) - 18.02 * max(0, len(protein) - 1)


def hydrophobicity_profile(protein: str, window: int = 9) -> list[float]:
    vals = [AA_HYDROPHOBICITY.get(a, 0.0) for a in protein]
    if len(vals) < window:
        return [sum(vals) / len(vals)] if vals else []
    return [sum(vals[i:i + window]) / window for i in range(len(vals) - window + 1)]
