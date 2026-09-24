"""Genetics statistics toolkit: Hardy-Weinberg exact test, association
chi-square, odds ratios, multiple-testing correction.

PROVENANCE
- HWE exact test: Wigginton JE, Cutler DJ, Abecasis GR (2005) "A note on
  exact tests of Hardy-Weinberg equilibrium", Am J Hum Genet 76:887-893.
  This is their SNP-HWE algorithm: walk the heterozygote-count
  distribution outward from the mode with the recurrence ratios, then sum
  the probabilities of all configurations at most as probable as the
  observed one. Oracle-tested against an INDEPENDENT brute-force
  hypergeometric enumeration in the tests (not the same code twice).
- Chi-square association: Pearson's statistic on the 2x2 allelic table
  (df = 1) and the 2x3 genotypic table (df = 2); Yates continuity
  correction (Yates 1934) optional on the 2x2 only. p-values use the
  closed forms chi2_sf(x, df=1) = erfc(sqrt(x/2)) and
  chi2_sf(x, df=2) = exp(-x/2).
- Odds ratio with Woolf log CI: Woolf B (1955) "On estimating the
  relation between blood group and disease", Ann Hum Genet 19:251-253.
  Zero cells get the Haldane-Anscombe +0.5 correction to ALL four cells -
  reported via the 'corrected' flag, never silent.
- Multiple testing: Bonferroni (Dunn OJ 1961, JASA 56:52-64) and
  Benjamini-Hochberg step-up FDR (Benjamini Y, Hochberg Y 1995, JRSS B
  57:289-300). The BH implementation is tested against the 15 p-values
  from the paper's own worked example.

CONVENTIONS
- Genotype counts are (AA, AB, BB) integers; which allele is 'rare' is
  derived from the counts, not from the caller's labeling.
- hwe_exact returns the two-sided exact p-value of Wigginton 2005.
- An association table with a zero row/column total is degenerate
  (chi-square undefined) -> ValueError.
"""
from __future__ import annotations

import math
from statistics import NormalDist


def hwe_exact(n_aa: int, n_ab: int, n_bb: int) -> float:
    """Two-sided exact HWE p-value (Wigginton et al. 2005 SNP-HWE
    algorithm) for genotype counts (AA, AB, BB)."""
    if min(n_aa, n_ab, n_bb) < 0:
        raise ValueError("genotype counts must be >= 0")
    obs_homr = min(n_aa, n_bb)
    obs_homc = max(n_aa, n_bb)
    rare_copies = 2 * obs_homr + n_ab
    genotypes = obs_homr + obs_homc + n_ab
    if genotypes == 0:
        raise ValueError("no genotypes")
    probs = [0.0] * (rare_copies + 1)
    mid = int(rare_copies * (2.0 * genotypes - rare_copies)
              / (2.0 * genotypes))
    if (rare_copies & 1) ^ (mid & 1):
        mid += 1
    probs[mid] = 1.0
    total = 1.0
    # walk down from the mode; state tracks current homozygote counts
    curr = mid
    homr = (rare_copies - mid) // 2
    homc = genotypes - mid - homr
    while curr >= 2:
        probs[curr - 2] = probs[curr] * curr * (curr - 1.0) / (
            4.0 * (homr + 1.0) * (homc + 1.0))
        total += probs[curr - 2]
        curr -= 2
        homr += 1
        homc += 1
    # walk up from the mode
    curr = mid
    homr = (rare_copies - mid) // 2
    homc = genotypes - mid - homr
    while curr <= rare_copies - 2:
        probs[curr + 2] = probs[curr] * 4.0 * homr * homc / (
            (curr + 2.0) * (curr + 1.0))
        total += probs[curr + 2]
        curr += 2
        homr -= 1
        homc -= 1
    p_obs = probs[n_ab]
    p = sum(p for p in probs if p <= p_obs) / total
    return min(1.0, p)


def chi2_sf(x: float, df: int) -> float:
    """Chi-square survival function, closed forms for df 1 and 2."""
    if x < 0:
        raise ValueError("chi-square statistic must be >= 0")
    if df == 1:
        return math.erfc(math.sqrt(x / 2.0))
    if df == 2:
        return math.exp(-x / 2.0)
    raise ValueError(f"df must be 1 or 2, got {df}")


def chi_square_2x2(a: float, b: float, c: float, d: float,
                   yates: bool = False) -> dict:
    """Pearson chi-square on [[a, b], [c, d]] (df = 1); optional Yates
    continuity correction (|ad - bc| - N/2)."""
    cells = (a, b, c, d)
    if min(cells) < 0:
        raise ValueError("cell counts must be >= 0")
    n = a + b + c + d
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    if n == 0 or r1 == 0 or r2 == 0 or c1 == 0 or c2 == 0:
        raise ValueError("degenerate table (zero margin)")
    diff = a * d - b * c
    if yates:
        diff = max(0.0, abs(diff) - n / 2.0)
        stat = n * diff * diff / (r1 * r2 * c1 * c2)
    else:
        stat = n * diff * diff / (r1 * r2 * c1 * c2)
    return {"statistic": stat, "df": 1, "p": chi2_sf(stat, 1),
            "yates": yates}


def odds_ratio(a: float, b: float, c: float, d: float,
               ci: float = 0.95) -> dict:
    """Odds ratio (a*d)/(b*c) for [[a, b], [c, d]] with the Woolf (1955)
    log CI. Zero cells trigger the Haldane-Anscombe +0.5 correction of all
    four cells (flagged 'corrected')."""
    if min(a, b, c, d) < 0:
        raise ValueError("cell counts must be >= 0")
    corrected = min(a, b, c, d) == 0
    if corrected:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    log_or = math.log((a * d) / (b * c))
    se = math.sqrt(1.0 / a + 1.0 / b + 1.0 / c + 1.0 / d)
    z = NormalDist().inv_cdf(1.0 - (1.0 - ci) / 2.0)
    return {"odds_ratio": math.exp(log_or), "log_or": log_or,
            "ci": ci, "ci_low": math.exp(log_or - z * se),
            "ci_high": math.exp(log_or + z * se), "corrected": corrected}


def allelic_test(cases: tuple, controls: tuple,
                 yates: bool = False) -> dict:
    """Allelic association: cases/controls as (AA, AB, BB) genotype counts
    collapsed to the 2x2 allele table (A vs a), chi-square df = 1 with
    optional Yates, plus odds ratio + Woolf CI on the allele table."""
    ca = 2 * cases[0] + cases[1]
    cb = cases[1] + 2 * cases[2]
    cc = 2 * controls[0] + controls[1]
    cd = controls[1] + 2 * controls[2]
    chi = chi_square_2x2(ca, cb, cc, cd, yates)
    or_ = odds_ratio(ca, cb, cc, cd)
    return {"table": [[ca, cb], [cc, cd]], **chi,
            "odds_ratio": or_["odds_ratio"],
            "ci_low": or_["ci_low"], "ci_high": or_["ci_high"],
            "or_corrected": or_["corrected"]}


def genotypic_test(cases: tuple, controls: tuple) -> dict:
    """Genotypic association on the 2x3 table (cases/controls x AA/AB/BB),
    Pearson chi-square df = 2."""
    cells = [list(map(float, cases)), list(map(float, controls))]
    if min(min(r) for r in cells) < 0:
        raise ValueError("cell counts must be >= 0")
    rows = [sum(r) for r in cells]
    cols = [cells[0][j] + cells[1][j] for j in range(3)]
    n = sum(rows)
    if n == 0 or min(rows) == 0 or min(cols) == 0:
        raise ValueError("degenerate table (zero margin)")
    stat = 0.0
    for i in range(2):
        for j in range(3):
            e = rows[i] * cols[j] / n
            stat += (cells[i][j] - e) ** 2 / e
    return {"statistic": stat, "df": 2, "p": chi2_sf(stat, 2),
            "table": cells}


def bonferroni(pvals: list) -> list:
    """Bonferroni-adjusted p-values: min(p * m, 1), input order kept."""
    m = len(pvals)
    if any(p < 0 or p > 1 for p in pvals):
        raise ValueError("p-values must be in [0, 1]")
    return [min(1.0, p * m) for p in pvals]


def benjamini_hochberg(pvals: list) -> list:
    """Benjamini-Hochberg (1995) adjusted p-values (step-up FDR),
    input order kept: p_(i) * m / i with monotone enforcement from the
    largest down."""
    m = len(pvals)
    if any(p < 0 or p > 1 for p in pvals):
        raise ValueError("p-values must be in [0, 1]")
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, pvals[i] * m / rank)
        adj[i] = running
    return adj
