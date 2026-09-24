"""Baum-Welch (forward-backward EM) training for profile HMMs.

Durbin et al. 1998, Chapter 3.3 (Baum-Welch for HMMs) applied to the Chapter 5
profile HMM (Section 5.x: estimating a profile HMM from unaligned sequences).

E-step: for each training sequence, forward values f and backward values b give
expected counts

    E_k(a)  = 1/P(x) * sum_{i: x_i = a} f_k(i) b_k(i)                (emitting k)
    A_kl    = 1/P(x) * sum_i f_k(i) a_kl e_l(x_{i+1}) b_l(i+1)       (emitting l)
    A_kl    = 1/P(x) * sum_i f_k(i) a_kl b_l(i)                      (silent l = D)

summed over sequences. M-step: each probability row is (counts + pseudocount)
normalised over the transitions that exist. With pseudocount 0 this is classic
maximum-likelihood Baum-Welch and the training log-likelihood never decreases.
With pseudocount alpha > 0 it is MAP-EM under a symmetric Dirichlet(alpha + 1)
prior: the monotone quantity is the objective log P(data) + alpha * sum log theta,
reported alongside the log-likelihood. Training stops when the change in total
training log-likelihood falls below ``tol`` or after ``max_iter`` iterations.
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .core import NEG_INF, TO_D, TO_I, TO_M, ProfileHMM, _logsumexp, forward

_PARAMS = ("match_emissions", "insert_emissions", "t_match", "t_insert", "t_delete")


def _logs(model: ProfileHMM):
    with np.errstate(divide="ignore"):
        return (np.log(model.match_emissions), np.log(model.insert_emissions),
                np.log(model.t_match), np.log(model.t_insert), np.log(model.t_delete))


def _forward_tables(model: ProfileHMM, x: list[int]):
    L, n = model.length, len(x)
    eM, eI, tM, tI, tD = _logs(model)
    FM = np.full((L + 1, n + 1), NEG_INF)
    FI = np.full((L + 1, n + 1), NEG_INF)
    FD = np.full((L + 1, n + 1), NEG_INF)
    FM[0][0] = 0.0
    for i in range(n + 1):
        for j in range(L + 1):
            if j >= 1 and i >= 1:
                s = _logsumexp([FM[j - 1][i - 1] + tM[j - 1][TO_M], FI[j - 1][i - 1] + tI[j - 1][TO_M],
                                (FD[j - 1][i - 1] + tD[j - 1][TO_M]) if j >= 2 else NEG_INF])
                FM[j][i] = eM[j][x[i - 1]] + s if s != NEG_INF else NEG_INF
            if i >= 1:
                s = _logsumexp([FM[j][i - 1] + tM[j][TO_I], FI[j][i - 1] + tI[j][TO_I],
                                (FD[j][i - 1] + tD[j][TO_I]) if j >= 1 else NEG_INF])
                FI[j][i] = eI[j][x[i - 1]] + s if s != NEG_INF else NEG_INF
            if j >= 1:
                FD[j][i] = _logsumexp([FM[j - 1][i] + tM[j - 1][TO_D], FI[j - 1][i] + tI[j - 1][TO_D],
                                       (FD[j - 1][i] + tD[j - 1][TO_D]) if j >= 2 else NEG_INF])
    logp = _logsumexp([FM[L][n] + tM[L][TO_M], FI[L][n] + tI[L][TO_M], FD[L][n] + tD[L][TO_M]])
    return FM, FI, FD, logp


def _backward_tables(model: ProfileHMM, x: list[int]):
    """B_s(j, i) = log P(x_{i+1..n}, End | in state s at column j after i residues)."""
    L, n = model.length, len(x)
    eM, eI, tM, tI, tD = _logs(model)
    BM = np.full((L + 1, n + 1), NEG_INF)
    BI = np.full((L + 1, n + 1), NEG_INF)
    BD = np.full((L + 1, n + 1), NEG_INF)
    for i in range(n, -1, -1):
        for j in range(L, -1, -1):
            for B, t in ((BM, tM), (BI, tI), (BD, tD)):
                if B is BD and j == 0:
                    continue
                terms = []
                if j == L:
                    if i == n:
                        terms.append(t[j][TO_M])                          # -> End
                else:
                    if i < n:
                        terms.append(t[j][TO_M] + eM[j + 1][x[i]] + BM[j + 1][i + 1])
                    terms.append(t[j][TO_D] + BD[j + 1][i])
                if i < n:
                    terms.append(t[j][TO_I] + eI[j][x[i]] + BI[j][i + 1])
                B[j][i] = _logsumexp(terms)
    return BM, BI, BD, BM[0][0]


def zero_counts(model: ProfileHMM) -> dict:
    return {p: np.zeros_like(getattr(model, p)) for p in _PARAMS}


def expected_counts(model: ProfileHMM, sequences) -> tuple[dict, float]:
    """E-step: expected emission/transition counts and total log-likelihood."""
    counts = zero_counts(model)
    L = model.length
    eM, eI, tM, tI, tD = _logs(model)
    total = 0.0
    for seq in sequences:
        x = model.encode(seq)
        n = len(x)
        FM, FI, FD, logp = _forward_tables(model, x)
        BM, BI, BD, logp_b = _backward_tables(model, x)
        if logp == NEG_INF:
            raise ValueError(f"sequence {seq!r} has zero probability under the model")
        assert math.isclose(logp, logp_b, rel_tol=1e-9, abs_tol=1e-9)
        total += logp
        for i in range(n + 1):
            for j in range(L + 1):
                if i >= 1:
                    if j >= 1 and FM[j][i] != NEG_INF:
                        counts["match_emissions"][j][x[i - 1]] += math.exp(FM[j][i] + BM[j][i] - logp)
                    if FI[j][i] != NEG_INF:
                        counts["insert_emissions"][j][x[i - 1]] += math.exp(FI[j][i] + BI[j][i] - logp)
                for F, t, key, ok in ((FM, tM, "t_match", True), (FI, tI, "t_insert", True),
                                      (FD, tD, "t_delete", j >= 1)):
                    if not ok or F[j][i] == NEG_INF:
                        continue
                    f = F[j][i]
                    row = counts[key][j]
                    if j == L:
                        if i == n:
                            row[TO_M] += math.exp(f + t[j][TO_M] - logp)
                    else:
                        if i < n:
                            row[TO_M] += math.exp(f + t[j][TO_M] + eM[j + 1][x[i]] + BM[j + 1][i + 1] - logp)
                        row[TO_D] += math.exp(f + t[j][TO_D] + BD[j + 1][i] - logp)
                    if i < n:
                        row[TO_I] += math.exp(f + t[j][TO_I] + eI[j][x[i]] + BI[j][i + 1] - logp)
    return counts, total


def _free_rows(model: ProfileHMM, update_inserts: bool):
    """(param, row index, column mask) for every free probability row."""
    L = model.length
    full3, last3 = np.array([1.0, 1.0, 1.0]), np.array([1.0, 1.0, 0.0])
    A = len(model.alphabet)
    rows = [("match_emissions", k, np.ones(A)) for k in range(1, L + 1)]
    if update_inserts:
        rows += [("insert_emissions", k, np.ones(A)) for k in range(L + 1)]
    for p, start in (("t_match", 0), ("t_insert", 0), ("t_delete", 1)):
        rows += [(p, k, last3 if k == L else full3) for k in range(start, L + 1)]
    return rows


def maximize(model: ProfileHMM, counts: dict, *, pseudocount: float = 0.0,
             update_insert_emissions: bool = True) -> ProfileHMM:
    """M-step: normalise (counts + pseudocount) row by row. A row with no counts
    and no pseudocount keeps its previous values (it cannot affect the likelihood)."""
    if pseudocount < 0:
        raise ValueError("pseudocount must be non-negative")
    new = {p: getattr(model, p).copy() for p in _PARAMS}
    for p, k, mask in _free_rows(model, update_insert_emissions):
        c = (counts[p][k] + pseudocount) * mask
        s = c.sum()
        if s > 0:
            new[p][k] = c / s
    return replace(model, **new)


def log_prior(model: ProfileHMM, pseudocount: float, update_insert_emissions: bool = True) -> float:
    """alpha * sum log theta over free parameters (0 when alpha = 0)."""
    if pseudocount == 0:
        return 0.0
    total = 0.0
    for p, k, mask in _free_rows(model, update_insert_emissions):
        vals = getattr(model, p)[k][mask > 0]
        with np.errstate(divide="ignore"):
            total += pseudocount * float(np.log(vals).sum())
    return total


def log_likelihood(model: ProfileHMM, sequences) -> float:
    return float(sum(forward(model, s)["log_prob"] for s in sequences))


def baum_welch(model: ProfileHMM, sequences, *, heldout=None, max_iter: int = 100,
               tol: float = 1e-6, pseudocount: float = 1.0,
               update_insert_emissions: bool = True) -> tuple[ProfileHMM, dict]:
    """Train ``model`` on unaligned ``sequences`` by forward-backward EM.

    Returns (trained model, report). The report has per-iteration training
    log-likelihood, objective (log-likelihood + log prior), held-out
    log-likelihood when ``heldout`` is given, convergence flag and reason.
    Iteration 0 is the starting model.
    """
    seqs = list(sequences)
    if not seqs:
        raise ValueError("no training sequences")
    if max_iter < 1 or tol <= 0:
        raise ValueError("max_iter must be >= 1 and tol > 0")
    held = list(heldout) if heldout is not None else None
    n_train = sum(len(model.encode(s)) for s in seqs)
    n_held = sum(len(model.encode(s)) for s in held) if held else 0
    history, converged, reason = [], False, "max_iter reached"
    current = model
    counts, ll = expected_counts(current, seqs)
    for it in range(max_iter + 1):
        entry = {"iteration": it, "train_log_likelihood": ll,
                 "objective": ll + log_prior(current, pseudocount, update_insert_emissions)}
        if held is not None:
            h = log_likelihood(current, held)
            entry["heldout_log_likelihood"] = h
            entry["heldout_per_residue"] = h / n_held if n_held else None
        history.append(entry)
        if it > 0 and abs(ll - history[-2]["train_log_likelihood"]) < tol:
            converged, reason = True, f"|delta log-likelihood| < {tol}"
            break
        if it == max_iter:
            break
        current = maximize(current, counts, pseudocount=pseudocount,
                           update_insert_emissions=update_insert_emissions)
        counts, ll = expected_counts(current, seqs)
    report = {"iterations": history[-1]["iteration"], "converged": converged, "reason": reason,
              "history": history, "pseudocount": pseudocount,
              "final_train_log_likelihood": history[-1]["train_log_likelihood"],
              "final_train_per_residue": history[-1]["train_log_likelihood"] / n_train if n_train else None}
    if held is not None:
        report["final_heldout_log_likelihood"] = history[-1]["heldout_log_likelihood"]
        report["final_heldout_per_residue"] = history[-1]["heldout_per_residue"]
    return current, report


def random_profile_hmm(length: int, alphabet: str = "ACGT", *, seed: int = 0,
                       emission_concentration: float = 1.0,
                       transition_concentration=(8.0, 1.0, 1.0)) -> ProfileHMM:
    """Random-seeded starting model: Dirichlet emissions and match-biased
    Dirichlet transitions (concentrations for [->M, ->I, ->D]); uniform background."""
    if length < 1:
        raise ValueError("length must be >= 1")
    rng = np.random.default_rng(seed)
    A, L = len(alphabet), length
    conc = np.asarray(transition_concentration, dtype=float)

    def trans(first):
        t = np.zeros((L + 1, 3))
        for k in range(first, L + 1):
            if k == L:
                t[k][:2] = rng.dirichlet(conc[:2])
            else:
                t[k] = rng.dirichlet(conc)
        return t

    me = np.zeros((L + 1, A))
    me[1:] = rng.dirichlet(np.full(A, emission_concentration), size=L)
    ie = rng.dirichlet(np.full(A, emission_concentration), size=L + 1)
    return ProfileHMM(alphabet, L, me, ie, trans(0), trans(0), trans(1),
                      np.full(A, 1.0 / A), list(range(L)), 0)
