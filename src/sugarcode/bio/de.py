"""Differential expression toolkit: log2 fold change + simple per-gene
tests on normalized counts with BH correction. Composes bio.rnaseq and
bio.gstats.

HONEST SCOPE (read first): simple per-gene tests on median-of-ratios
normalized counts - Welch's t-test or Wilcoxon rank-sum per gene,
Benjamini-Hochberg across genes. This is NOT a negative-binomial model:
DESeq2/edgeR estimate per-gene dispersion and shrink fold changes; this
toolkit does neither. With few replicates power is low and fold changes
are unshrunk. For publication-grade DE use an NB model; this is for
quick looks, teaching, and pipeline glue. Stated here and echoed in
every result's 'scope' field.

PROVENANCE
- Normalization: Anders & Huber 2010 median-of-ratios, via bio.rnaseq.
- Welch t-test: Welch BL (1947) "The generalization of Student's problem
  when several different population variances are involved", Biometrika
  34:28-35; Welch-Satterthwaite degrees of freedom. p from the t
  distribution (scipy); oracle-tested against scipy ttest_ind
  (equal_var=False).
- Wilcoxon rank-sum: Wilcoxon F (1945) Biometrics Bull 1:80-83; Mann &
  Whitney (1947) Ann Math Stat 18:50-60. Normal approximation with
  continuity correction and tie-corrected variance (midranks);
  oracle-tested against scipy mannwhitneyu (asymptotic).
- FDR: Benjamini & Hochberg 1995, via bio.gstats.
- Pseudocount: log2fc = log2(mean_B + pc) - log2(mean_A + pc) over
  normalized counts, pc default 1.0. A documented convention, NOT a
  shrinkage estimator.

CONVENTIONS
- Two groups only; group A is the first label in the groups list,
  group B the second. log2fc is B over A.
- Welch needs >= 2 replicates per group. Wilcoxon allows >= 1 but the
  normal approximation is crude below ~4 per group (warned in docs,
  not blocked).
- Degenerate variance: both group variances 0 -> statistic 0 and
  p = 1.0 when the means are equal; statistic = -inf and p = 0.0 when
  they differ (perfectly separated constant groups). Stated, not hidden.
- Wilcoxon with all values tied: p = 1.0.
- Volcano-ready output: gene, mean_a, mean_b, log2fc, statistic,
  pvalue, padj, neg_log10_p.
"""
from __future__ import annotations

import math

from . import gstats as _gs
from . import rnaseq as _rq

SCOPE = ("simple per-gene tests on median-of-ratios normalized counts - "
         "not a negative-binomial model (no dispersion estimation, "
         "no LFC shrinkage)")


def log2_fold_change(mean_a: float, mean_b: float,
                     pseudocount: float = 1.0) -> float:
    """log2((mean_b + pc) / (mean_a + pc)) - documented pseudocount."""
    if pseudocount <= 0:
        raise ValueError("pseudocount must be > 0")
    if mean_a < 0 or mean_b < 0:
        raise ValueError("means must be >= 0")
    return math.log2(mean_b + pseudocount) - math.log2(mean_a + pseudocount)


def _mean_var(x: list) -> tuple:
    n = len(x)
    m = sum(x) / n
    if n < 2:
        return m, 0.0
    return m, sum((v - m) ** 2 for v in x) / (n - 1)


def welch_ttest(x: list, y: list) -> dict:
    """Welch two-sample t-test (Welch 1947), two-sided. x = group A,
    y = group B."""
    if len(x) < 2 or len(y) < 2:
        raise ValueError("Welch t-test needs >= 2 replicates per group")
    from scipy.stats import t as _tdist
    mx, vx = _mean_var(x)
    my, vy = _mean_var(y)
    nx, ny = len(x), len(y)
    se2 = vx / nx + vy / ny
    if se2 == 0.0:
        if mx == my:
            return {"statistic": 0.0, "df": nx + ny - 2, "p": 1.0,
                    "degenerate": True}
        return {"statistic": -math.inf, "df": nx + ny - 2, "p": 0.0,
                "degenerate": True}
    t = (mx - my) / math.sqrt(se2)
    df = se2 ** 2 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
    return {"statistic": t, "df": df,
            "p": 2.0 * _tdist.sf(abs(t), df), "degenerate": False}


def wilcoxon_rank_sum(x: list, y: list) -> dict:
    """Wilcoxon rank-sum (1945) / Mann-Whitney (1947): midranks,
    tie-corrected variance, continuity correction, two-sided normal
    approximation. x = group A, y = group B. statistic is U for x."""
    from scipy.stats import norm as _norm
    x, y = list(x), list(y)
    if not x or not y:
        raise ValueError("both groups need >= 1 value")
    nx, ny = len(x), len(y)
    pooled = [(v, 0) for v in x] + [(v, 1) for v in y]
    pooled.sort(key=lambda t: t[0])
    ranks = [0.0] * len(pooled)
    tie_term = 0.0
    i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        mid = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = mid
        m = j - i + 1
        if m > 1:
            tie_term += m ** 3 - m
        i = j + 1
    r1 = sum(r for r, (_, g) in zip(ranks, pooled) if g == 0)
    u1 = r1 - nx * (nx + 1) / 2.0
    n = nx + ny
    mu = nx * ny / 2.0
    sigma2 = nx * ny / 12.0 * ((n + 1) - tie_term / (n * (n - 1)))
    if sigma2 <= 0.0:
        return {"statistic": u1, "z": 0.0, "p": 1.0, "degenerate": True}
    sigma = math.sqrt(sigma2)
    cc = 0.5 if u1 > mu else (-0.5 if u1 < mu else 0.0)
    z = (u1 - mu - cc) / sigma
    return {"statistic": u1, "z": z,
            "p": 2.0 * _norm.sf(abs(z)), "degenerate": False}


def de_analysis(table: dict, groups: list, method: str = "welch",
                pseudocount: float = 1.0) -> dict:
    """Per-gene DE between two groups of a count table. Normalizes with
    DESeq median-of-ratios (bio.rnaseq) - inheriting its requirement of
    at least one gene positive in every sample - then tests each gene.
    Returns volcano-ready rows in input gene order, BH padj attached."""
    if len(groups) != len(table["samples"]):
        raise ValueError(f"groups has {len(groups)} labels for "
                         f"{len(table['samples'])} samples")
    labels = []
    for g in groups:
        if g not in labels:
            labels.append(g)
    if len(labels) != 2:
        raise ValueError(f"need exactly 2 groups, got {len(labels)}")
    ga, gb = labels
    idx_a = [i for i, g in enumerate(groups) if g == ga]
    idx_b = [i for i, g in enumerate(groups) if g == gb]
    if method == "welch" and (len(idx_a) < 2 or len(idx_b) < 2):
        raise ValueError("Welch t-test needs >= 2 replicates per group")
    if method not in ("welch", "wilcoxon"):
        raise ValueError(f"method must be 'welch' or 'wilcoxon', "
                         f"got {method!r}")
    norm = _rq.normalize_deseq(table)
    test = welch_ttest if method == "welch" else wilcoxon_rank_sum
    rows = []
    for gene, counts in zip(norm["genes"], norm["counts"]):
        xa = [counts[j] for j in idx_a]
        xb = [counts[j] for j in idx_b]
        ma, mb = sum(xa) / len(xa), sum(xb) / len(xb)
        r = test(xa, xb)
        rows.append({"gene": gene, "mean_a": ma, "mean_b": mb,
                     "log2fc": log2_fold_change(ma, mb, pseudocount),
                     "statistic": r["statistic"], "pvalue": r["p"]})
    padj = _gs.benjamini_hochberg([r["pvalue"] for r in rows])
    for r, q in zip(rows, padj):
        r["padj"] = q
        r["neg_log10_p"] = -math.log10(r["pvalue"]) if r["pvalue"] > 0 \
            else math.inf
    return {"method": method, "pseudocount": pseudocount,
            "group_a": ga, "group_b": gb,
            "n_a": len(idx_a), "n_b": len(idx_b),
            "size_factors": norm["size_factors"],
            "scope": SCOPE, "results": rows}


def de_analysis_deseq2(table: dict, groups: list, blocks: list | None = None) -> dict:
    """Negative-binomial DE via PyDESeq2 (Muzellec et al. 2023; Love et al. 2014),
    with an optional blocking factor (e.g. donor / cell line) for paired designs.

    Why: on GEO GSE52778 (airway, dex vs untreated, 4 vs 4) the Welch path
    found 351 genes at padj<0.05 and Wilcoxon 0, versus 4,451 for PyDESeq2
    with ~cell + dex; all 7 canonical dex-response genes (FKBP5, TSC22D3,
    PER1, DUSP1, KLF15, ZBTB16, CRISPLD2) were missed by the simple tests
    (mega27-01 benchmarks/sweep_de_pydeseq2.json). Requires pydeseq2."""
    try:
        import pandas as pd
        from pydeseq2.dds import DeseqDataSet
        from pydeseq2.ds import DeseqStats
    except ImportError as e:  # pragma: no cover
        raise ImportError("de_analysis_deseq2 needs pydeseq2 (pip install sugarcode-ai[de])") from e
    samples = list(table["samples"])
    if len(groups) != len(samples):
        raise ValueError("groups length must match samples")
    labels = list(dict.fromkeys(groups))
    if len(labels) != 2:
        raise ValueError(f"need exactly 2 groups, got {len(labels)}")
    counts = pd.DataFrame(table["counts"], index=[str(g) for g in table["genes"]], columns=samples).T
    meta = pd.DataFrame({"group": [str(g) for g in groups]}, index=samples)
    design = "~group"
    if blocks is not None:
        if len(blocks) != len(samples):
            raise ValueError("blocks length must match samples")
        meta["block"] = [str(b) for b in blocks]
        design = "~block + group"
    dds = DeseqDataSet(counts=counts.round().astype(int), metadata=meta, design=design, quiet=True, n_cpus=1)
    dds.deseq2()
    st = DeseqStats(dds, contrast=["group", str(labels[1]), str(labels[0])], quiet=True, n_cpus=1)
    st.summary()
    R = st.results_df
    rows = [{"gene": g, "base_mean": float(R.loc[g, "baseMean"]), "log2fc": float(R.loc[g, "log2FoldChange"]),
             "pvalue": None if pd.isna(R.loc[g, "pvalue"]) else float(R.loc[g, "pvalue"]),
             "padj": None if pd.isna(R.loc[g, "padj"]) else float(R.loc[g, "padj"])} for g in R.index]
    return {"method": "pydeseq2_wald", "design": design, "group_a": labels[0], "group_b": labels[1],
            "results": rows}
