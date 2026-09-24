"""RNA-seq count toolkit: count table I/O, CPM/RPKM/TPM, DESeq
median-of-ratios size factors, expression filtering.

PROVENANCE
- RPKM: Mortazavi A, Williams BA, McCue K, Schaeffer L, Wold B (2008)
  "Mapping and quantifying mammalian transcriptomes by RNA-Seq",
  Nat Methods 5:621-628. RPKM = CPM / (gene length in kb).
- TPM: Wagner GP, Kin K, Lynch VJ (2012) "Measurement of mRNA abundance
  using RNA-seq data: RPKM measure is inconsistent among samples",
  Theory Biosci 131:281-285. TPM = RPK / sum(RPK per sample) x 1e6.
- Median-of-ratios size factors: Anders S, Huber W (2010) "Differential
  expression analysis for sequence count data", Genome Biology 11:R106
  (the DESeq method): per-gene geometric mean across samples, per-sample
  median of count/geomean ratios, normalized = count / size factor.

CONVENTIONS (stated here and next to every function)
- A count table is {genes: [...], samples: [...], counts: [[per sample]
  per gene]} - rows are genes, columns are samples. Counts are
  non-negative numbers; gene ids and sample names are unique.
- CPM/RPKM/TPM use library size = column sum of RAW counts (no
  pre-filtering; callers filter first if they want filtered library
  sizes).
- A sample whose library size is 0 cannot be normalized (ValueError,
  not a silent zero-fill).
- Median-of-ratios uses only genes with POSITIVE counts in EVERY sample
  (the DESeq default - a zero anywhere makes the geometric mean zero).
  If no such gene exists, or any size factor comes out 0, ValueError.
- filter_genes is the simple documented rule "count >= min_count in at
  least min_samples samples" - NOT edgeR's filterByExpr heuristic, and
  named as such.
"""
from __future__ import annotations

import math
from statistics import median


def parse_counts(text: str) -> dict:
    """Parse a CSV/TSV count table: header row of sample names (first cell
    a gene-id label), one row per gene. Delimiter auto-detects: a tab in
    the header line means TSV, otherwise CSV. Whitespace is stripped."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise ValueError("empty count table")
    delim = "\t" if "\t" in lines[0] else ","
    rows = [[c.strip() for c in ln.split(delim)] for ln in lines]
    header = rows[0]
    if len(header) < 2:
        raise ValueError("count table needs a gene column + >= 1 sample")
    samples = header[1:]
    if len(set(samples)) != len(samples):
        raise ValueError("duplicate sample names")
    genes, counts = [], []
    for ln_no, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError(f"line {ln_no}: expected {len(header)} fields, "
                             f"got {len(row)}")
        if not row[0]:
            raise ValueError(f"line {ln_no}: empty gene id")
        if row[0] in genes:
            raise ValueError(f"line {ln_no}: duplicate gene id {row[0]!r}")
        try:
            vals = [float(c) for c in row[1:]]
        except ValueError:
            raise ValueError(f"line {ln_no}: non-numeric count") from None
        if any(v < 0 for v in vals):
            raise ValueError(f"line {ln_no}: negative count")
        genes.append(row[0])
        counts.append(vals)
    return {"genes": genes, "samples": samples, "counts": counts}


def write_counts(table: dict, delimiter: str = "\t") -> str:
    """Serialize a count table (values formatted %g)."""
    lines = [delimiter.join(["gene"] + table["samples"])]
    for gene, row in zip(table["genes"], table["counts"]):
        lines.append(delimiter.join(
            [gene] + [f"{v:g}" for v in row]))
    return "\n".join(lines) + "\n"


def _check(table: dict) -> None:
    n = len(table["samples"])
    if len(table["genes"]) != len(table["counts"]):
        raise ValueError("genes/counts row mismatch")
    for row in table["counts"]:
        if len(row) != n:
            raise ValueError("counts/sample column mismatch")
        if any(v < 0 for v in row):
            raise ValueError("negative count")


def _library_sizes(table: dict) -> list:
    n = len(table["samples"])
    return [sum(row[j] for row in table["counts"]) for j in range(n)]


def cpm(table: dict) -> dict:
    """Counts per million on raw library sizes."""
    _check(table)
    libs = _library_sizes(table)
    if any(x == 0 for x in libs):
        raise ValueError("a sample has library size 0; cannot normalize")
    out = [[row[j] / libs[j] * 1e6 for j in range(len(libs))]
           for row in table["counts"]]
    return {**table, "counts": out, "method": "cpm",
            "library_sizes": libs}


def _check_lengths(table: dict, lengths: dict) -> list:
    lens = []
    for gene in table["genes"]:
        L = lengths.get(gene)
        if L is None:
            raise ValueError(f"no length for gene {gene!r}")
        if L <= 0:
            raise ValueError(f"gene {gene!r}: length must be > 0")
        lens.append(L)
    return lens


def rpkm(table: dict, lengths: dict) -> dict:
    """RPKM (Mortazavi 2008): CPM divided by gene length in kb."""
    _check(table)
    lens = _check_lengths(table, lengths)
    base = cpm(table)
    out = [[base["counts"][i][j] / (lens[i] / 1000.0)
            for j in range(len(base["samples"]))]
           for i in range(len(base["genes"]))]
    return {**table, "counts": out, "method": "rpkm",
            "library_sizes": base["library_sizes"]}


def tpm(table: dict, lengths: dict) -> dict:
    """TPM (Wagner 2012): per-sample RPK scaled to sum to 1e6."""
    _check(table)
    lens = _check_lengths(table, lengths)
    n = len(table["samples"])
    rpk = [[table["counts"][i][j] / (lens[i] / 1000.0)
            for j in range(n)] for i in range(len(table["genes"]))]
    totals = [sum(rpk[i][j] for i in range(len(rpk))) for j in range(n)]
    if any(x == 0 for x in totals):
        raise ValueError("a sample has all-zero RPK; cannot compute TPM")
    out = [[rpk[i][j] / totals[j] * 1e6 for j in range(n)]
           for i in range(len(rpk))]
    return {**table, "counts": out, "method": "tpm"}


def size_factors(counts: list) -> list:
    """DESeq median-of-ratios size factors (Anders & Huber 2010) for a
    counts matrix (rows = genes, columns = samples). Only rows positive
    in EVERY sample enter the geometric means (documented DESeq
    default)."""
    if not counts:
        raise ValueError("empty counts matrix")
    n = len(counts[0])
    for row in counts:
        if len(row) != n:
            raise ValueError("ragged counts matrix")
        if any(v < 0 for v in row):
            raise ValueError("negative count")
    positive = [row for row in counts if all(v > 0 for v in row)]
    if not positive:
        raise ValueError("no gene is positive in every sample; "
                         "median-of-ratios is undefined")
    geomeans = [math.exp(sum(math.log(v) for v in row) / n)
                for row in positive]
    factors = []
    for j in range(n):
        ratios = [row[j] / gm for row, gm in zip(positive, geomeans)]
        sf = median(ratios)
        if sf == 0:
            raise ValueError(f"sample {j}: size factor is 0")
        factors.append(sf)
    return factors


def normalize_deseq(table: dict) -> dict:
    """Median-of-ratios normalized counts (count / size factor)."""
    _check(table)
    sf = size_factors(table["counts"])
    out = [[row[j] / sf[j] for j in range(len(sf))]
           for row in table["counts"]]
    return {**table, "counts": out, "method": "deseq_median_of_ratios",
            "size_factors": sf}


def filter_genes(table: dict, min_count: float = 10,
                 min_samples: int = 1) -> dict:
    """Keep genes with count >= min_count in at least min_samples samples
    (simple documented threshold rule, not edgeR filterByExpr)."""
    _check(table)
    n = len(table["samples"])
    if not 1 <= min_samples <= n:
        raise ValueError(f"min_samples must be 1..{n}, got {min_samples}")
    keep = [i for i, row in enumerate(table["counts"])
            if sum(1 for v in row if v >= min_count) >= min_samples]
    return {"genes": [table["genes"][i] for i in keep],
            "samples": table["samples"],
            "counts": [table["counts"][i] for i in keep],
            "kept": len(keep), "dropped": len(table["genes"]) - len(keep)}
