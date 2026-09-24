"""Profile hidden Markov models built from a multiple alignment.

Topology and algorithms follow Durbin, Eddy, Krogh & Mitchison, "Biological
Sequence Analysis" (Cambridge University Press 1998, ISBN 978-0-521-62971-3,
DOI 10.1017/CBO9780511790492), Chapter 5 "Profile HMMs for sequence families",
and Krogh et al. 1994 (J Mol Biol 235:1501-1531, DOI 10.1006/jmbi.1994.1104).

Architecture (Durbin Fig. 5.2): Begin (= M0), match states M1..ML, insert
states I0..IL, delete states D1..DL, End (= M_{L+1}). Every state at position
k moves to M_{k+1}, I_k or D_{k+1} (the nine transition types, including D->I
and I->D). At the last position the M_{L+1}/D_{L+1} targets collapse to End;
D_{L+1} does not exist, so the last states choose only End or I_L.

Construction (Durbin 5.3): a column is a match column when its gap fraction is
at most ``gap_threshold`` (default 0.5, i.e. columns with more than half gaps
are insert columns) unless match columns are given explicitly. Each sequence's
path through the model is read off the alignment; emission and transition
counts are accumulated and pseudocounts added (default 1 = Laplace's rule)
before normalising. Insert emissions are counted the same way by default, or
set to the background distribution with ``insert_emissions="background"``.

Scoring (Durbin 5.4): Viterbi (best state path) and Forward (sum over all
paths) in natural-log space, reported as log P(x | model), bits, and log-odds
against an i.i.d. background null (log P(x|M) - sum_i log q(x_i)).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

GAP_CHARS = frozenset("-.")
DNA, RNA = "ACGT", "ACGU"
PROTEIN = "ACDEFGHIKLMNPQRSTVWY"
NEG_INF = -math.inf
# transition target indices within each state's row
TO_M, TO_I, TO_D = 0, 1, 2
REFERENCE = {
    "topology": "Durbin, Eddy, Krogh & Mitchison, Biological Sequence Analysis (CUP 1998), Chapter 5, Fig. 5.2",
    "isbn": "978-0-521-62971-3",
    "doi": "10.1017/CBO9780511790492",
    "original": "Krogh et al. J Mol Biol 1994;235:1501-1531, DOI 10.1006/jmbi.1994.1104, PMID 8107089",
}


def _logsumexp(values) -> float:
    vals = [v for v in values if v != NEG_INF]
    if not vals:
        return NEG_INF
    m = max(vals)
    return m + math.log(sum(math.exp(v - m) for v in vals))


def _log(p: float) -> float:
    return math.log(p) if p > 0 else NEG_INF


def infer_alphabet(sequences) -> str:
    chars = {c for s in sequences for c in s.upper() if c not in GAP_CHARS}
    if chars <= set(DNA):
        return DNA
    if chars <= set(RNA):
        return RNA
    if chars <= set(PROTEIN):
        return PROTEIN
    raise ValueError(f"cannot infer alphabet; unexpected symbols {sorted(chars - set(PROTEIN))}")


@dataclass
class ProfileHMM:
    """A profile HMM with L match positions.

    ``match_emissions``  (L+1, A): row k = M_k emissions (row 0 unused, Begin is silent)
    ``insert_emissions`` (L+1, A): row k = I_k emissions
    ``t_match``  (L+1, 3): from M_k (k=0 is Begin) to [M_{k+1}|End, I_k, D_{k+1}]
    ``t_insert`` (L+1, 3): from I_k to [M_{k+1}|End, I_k, D_{k+1}]
    ``t_delete`` (L+1, 3): from D_k (row 0 unused) to [M_{k+1}|End, I_k, D_{k+1}]
    Column TO_D of row L is always 0 (there is no D_{L+1}).
    """
    alphabet: str
    length: int
    match_emissions: np.ndarray
    insert_emissions: np.ndarray
    t_match: np.ndarray
    t_insert: np.ndarray
    t_delete: np.ndarray
    background: np.ndarray
    match_columns: list
    n_sequences: int = 0

    # ---- helpers -------------------------------------------------------
    def encode(self, sequence: str) -> list[int]:
        seq = "".join(str(sequence).split()).upper()
        if self.alphabet == RNA:
            seq = seq.replace("T", "U")
        elif self.alphabet == DNA:
            seq = seq.replace("U", "T")
        idx = {c: i for i, c in enumerate(self.alphabet)}
        bad = sorted(set(seq) - set(idx))
        if bad:
            raise ValueError(f"symbol(s) {bad} not in model alphabet {self.alphabet}")
        return [idx[c] for c in seq]

    def consensus(self) -> str:
        return "".join(self.alphabet[int(np.argmax(self.match_emissions[k]))]
                       for k in range(1, self.length + 1))

    def transition(self, src: tuple[str, int], dst: tuple[str, int]) -> float:
        """Probability of src -> dst; states are ("B",0) ("M",k) ("I",k) ("D",k) ("E",0)."""
        kind, k = src
        L = self.length
        table = {"B": self.t_match, "M": self.t_match, "I": self.t_insert, "D": self.t_delete}[kind]
        k = 0 if kind == "B" else k
        dkind, dk = dst
        if dkind == "E":
            return float(table[k][TO_M]) if k == L else 0.0
        if dkind == "M" and dk == k + 1 and dk <= L:
            return float(table[k][TO_M])
        if dkind == "I" and dk == k:
            return float(table[k][TO_I])
        if dkind == "D" and dk == k + 1 and dk <= L:
            return float(table[k][TO_D])
        return 0.0

    def to_dict(self) -> dict:
        return {"alphabet": self.alphabet, "length": self.length,
                "match_columns": list(self.match_columns), "n_sequences": self.n_sequences,
                "consensus": self.consensus(),
                "match_emissions": self.match_emissions[1:].tolist(),
                "insert_emissions": self.insert_emissions.tolist(),
                "t_match": self.t_match.tolist(), "t_insert": self.t_insert.tolist(),
                "t_delete": self.t_delete.tolist(), "background": self.background.tolist(),
                "reference": REFERENCE}


def _state_path_of_row(row: str, match_columns: list[int]) -> list[tuple[str, int, str | None]]:
    """Durbin 5.3: read a sequence's state path off an aligned row."""
    path, k = [], 0
    mset = set(match_columns)
    for col, ch in enumerate(row):
        if col in mset:
            k += 1
            path.append(("D", k, None) if ch in GAP_CHARS else ("M", k, ch))
        elif ch not in GAP_CHARS:
            path.append(("I", k, ch))
    return path


def build_profile_hmm(alignment, *, alphabet: str | None = None, gap_threshold: float = 0.5,
                      match_columns=None, pseudocount: float = 1.0,
                      transition_pseudocount: float | None = None,
                      insert_emissions: str = "counted", background="uniform") -> ProfileHMM:
    """Build a profile HMM from aligned sequences (equal length, '-' or '.' as gaps).

    ``match_columns``: explicit 0-based match columns (overrides gap_threshold).
    ``pseudocount``: added to every emission count (Laplace = 1).
    ``transition_pseudocount``: added to every existing transition (default = pseudocount).
    ``insert_emissions``: "counted" (counts + pseudocount) or "background".
    ``background``: "uniform", "alignment" (residue frequencies + pseudocount) or a
    mapping symbol -> probability; used for log-odds and background inserts.
    """
    rows = ["".join(str(r).split()).upper() for r in alignment]
    if not rows:
        raise ValueError("alignment is empty")
    width = len(rows[0])
    if width == 0 or any(len(r) != width for r in rows):
        raise ValueError("aligned sequences must be non-empty and of equal length")
    alpha = alphabet or infer_alphabet(rows)
    if alpha == RNA:
        rows = [r.replace("T", "U") for r in rows]
    idx = {c: i for i, c in enumerate(alpha)}
    bad = sorted({c for r in rows for c in r} - set(idx) - GAP_CHARS)
    if bad:
        raise ValueError(f"symbol(s) {bad} not in alphabet {alpha}")
    if pseudocount < 0 or (transition_pseudocount is not None and transition_pseudocount < 0):
        raise ValueError("pseudocounts must be non-negative")
    tpc = pseudocount if transition_pseudocount is None else transition_pseudocount
    if match_columns is None:
        if not 0.0 <= gap_threshold < 1.0:
            raise ValueError("gap_threshold must be in [0, 1)")
        match_columns = [c for c in range(width)
                         if sum(r[c] in GAP_CHARS for r in rows) / len(rows) <= gap_threshold]
    else:
        match_columns = sorted(set(int(c) for c in match_columns))
        if any(c < 0 or c >= width for c in match_columns):
            raise ValueError("match column out of range")
    L = len(match_columns)
    if L == 0:
        raise ValueError("no match columns (every column exceeds the gap threshold)")
    A = len(alpha)

    em_m = np.zeros((L + 1, A))
    em_i = np.zeros((L + 1, A))
    tr = {"M": np.zeros((L + 1, 3)), "I": np.zeros((L + 1, 3)), "D": np.zeros((L + 1, 3))}
    for row in rows:
        prev = ("M", 0)                                   # Begin
        for kind, k, ch in _state_path_of_row(row, match_columns):
            pk, pkk = prev
            target = {"M": TO_M, "I": TO_I, "D": TO_D}[kind]
            tr[pk][pkk][target] += 1
            if kind == "M":
                em_m[k][idx[ch]] += 1
            elif kind == "I":
                em_i[k][idx[ch]] += 1
            prev = (kind, k)
        pk, pkk = prev
        tr[pk][pkk][TO_M] += 1                            # -> End

    if background == "uniform":
        bg = np.full(A, 1.0 / A)
    elif background == "alignment":
        counts = np.array([sum(r.count(c) for r in rows) for c in alpha], dtype=float) + max(pseudocount, 1e-12)
        bg = counts / counts.sum()
    else:
        bg = np.array([float(background.get(c, 0.0)) for c in alpha])
        if not math.isclose(bg.sum(), 1.0, rel_tol=1e-9) or (bg <= 0).any():
            raise ValueError("background must give every symbol a positive probability summing to 1")

    def norm_rows(counts, extra, first_row=0):
        out = np.zeros_like(counts)
        for k in range(first_row, counts.shape[0]):
            c = counts[k] + extra
            s = c.sum()
            out[k] = c / s if s > 0 else np.full(len(c), 1.0 / len(c))
        return out

    match_e = norm_rows(em_m, pseudocount, 1)
    match_e[0] = 0.0
    if insert_emissions == "background":
        insert_e = np.tile(bg, (L + 1, 1))
    elif insert_emissions == "counted":
        insert_e = norm_rows(em_i, pseudocount)
    else:
        raise ValueError('insert_emissions must be "counted" or "background"')

    def norm_trans(counts, first_row=0):
        out = np.zeros_like(counts)
        for k in range(first_row, L + 1):
            mask = np.array([1.0, 1.0, 0.0 if k == L else 1.0])
            c = (counts[k] + tpc) * mask
            s = c.sum()
            out[k] = c / s if s > 0 else mask / mask.sum()
        return out

    return ProfileHMM(alpha, L, match_e, insert_e, norm_trans(tr["M"]), norm_trans(tr["I"]),
                      norm_trans(tr["D"], 1), bg, match_columns, len(rows))


def _dp(model: ProfileHMM, x: list[int], mode: str):
    """Shared DP. mode 'viterbi' (max, with pointers) or 'forward' (log-sum-exp)."""
    L, n = model.length, len(x)
    with np.errstate(divide="ignore"):
        eM, eI = np.log(model.match_emissions), np.log(model.insert_emissions)
        tM, tI, tD = np.log(model.t_match), np.log(model.t_insert), np.log(model.t_delete)
    VM = np.full((L + 1, n + 1), NEG_INF)
    VI = np.full((L + 1, n + 1), NEG_INF)
    VD = np.full((L + 1, n + 1), NEG_INF)
    ptr = {} if mode == "viterbi" else None
    comb = max if mode == "viterbi" else _logsumexp
    VM[0][0] = 0.0                                        # Begin
    for i in range(n + 1):
        for j in range(L + 1):
            if j >= 1 and i >= 1:
                c = [VM[j - 1][i - 1] + tM[j - 1][TO_M], VI[j - 1][i - 1] + tI[j - 1][TO_M],
                     (VD[j - 1][i - 1] + tD[j - 1][TO_M]) if j - 1 >= 1 else NEG_INF]
                best = comb(c)
                VM[j][i] = eM[j][x[i - 1]] + best if best != NEG_INF else NEG_INF
                if ptr is not None:
                    ptr[("M", j, i)] = "MID"[int(np.argmax(c))]
            if i >= 1:
                c = [VM[j][i - 1] + tM[j][TO_I], VI[j][i - 1] + tI[j][TO_I],
                     (VD[j][i - 1] + tD[j][TO_I]) if j >= 1 else NEG_INF]
                best = comb(c)
                VI[j][i] = eI[j][x[i - 1]] + best if best != NEG_INF else NEG_INF
                if ptr is not None:
                    ptr[("I", j, i)] = "MID"[int(np.argmax(c))]
            if j >= 1:
                c = [VM[j - 1][i] + tM[j - 1][TO_D], VI[j - 1][i] + tI[j - 1][TO_D],
                     (VD[j - 1][i] + tD[j - 1][TO_D]) if j - 1 >= 1 else NEG_INF]
                VD[j][i] = comb(c)
                if ptr is not None:
                    ptr[("D", j, i)] = "MID"[int(np.argmax(c))]
    end = [VM[L][n] + tM[L][TO_M], VI[L][n] + tI[L][TO_M], VD[L][n] + tD[L][TO_M]]
    return comb(end), end, ptr


def _summary(model: ProfileHMM, x: list[int], logp: float) -> dict:
    null = float(sum(math.log(model.background[c]) for c in x))
    return {"log_prob": logp, "bits": logp / math.log(2) if logp != NEG_INF else NEG_INF,
            "log_odds": logp - null if logp != NEG_INF else NEG_INF,
            "log_odds_bits": (logp - null) / math.log(2) if logp != NEG_INF else NEG_INF,
            "null_log_prob": null}


def viterbi(model: ProfileHMM, sequence: str) -> dict:
    """Most probable state path and its log probability (Durbin 5.4)."""
    x = model.encode(sequence)
    logp, end, ptr = _dp(model, x, "viterbi")
    path = []
    if logp != NEG_INF:
        kind, j, i = "MID"[int(np.argmax(end))], model.length, len(x)
        while not (kind == "M" and j == 0):
            path.append((kind, j, i))
            prev = ptr[(kind, j, i)]
            if kind == "M":
                j, i = j - 1, i - 1
            elif kind == "I":
                i = i - 1
            else:
                j = j - 1
            kind = prev
        path.reverse()
    states = [f"{k}{j}" for k, j, _ in path]
    aligned = []
    for kind, j, i in path:
        aligned.append({"state": f"{kind}{j}",
                        "residue": sequence_residue(model, x, i) if kind != "D" else "-",
                        "position": i if kind != "D" else None})
    return {**_summary(model, x, logp), "state_path": states, "alignment": aligned,
            "algorithm": "viterbi"}


def sequence_residue(model: ProfileHMM, x: list[int], i: int) -> str:
    return model.alphabet[x[i - 1]]


def forward(model: ProfileHMM, sequence: str) -> dict:
    """Total probability over all state paths (Durbin 5.4 forward algorithm)."""
    x = model.encode(sequence)
    logp, _, _ = _dp(model, x, "forward")
    return {**_summary(model, x, logp), "algorithm": "forward"}


def brute_force(model: ProfileHMM, sequence: str, *, max_paths: int = 2_000_000) -> dict:
    """Independent verifier: enumerate every Begin->End state path that emits the
    sequence, using only ``model.transition`` and the emission tables (no DP).
    Returns the max path probability, total probability and the best path."""
    x = model.encode(sequence)
    n, L = len(x), model.length
    best_p, best_path, total, count = 0.0, None, 0.0, 0

    def successors(state):
        kind, k = state
        k = 0 if kind == "B" else k
        out = [("I", k)]
        if k < L:
            out += [("M", k + 1), ("D", k + 1)]
        else:
            out.append(("E", 0))
        return out

    stack = [(("B", 0), 0, 1.0, [])]
    while stack:
        state, i, p, path = stack.pop()
        for nxt in successors(state):
            t = model.transition(state, nxt)
            if t == 0.0:
                continue
            q, j = p * t, i
            kind, k = nxt
            if kind == "E":
                if i == n:
                    count += 1
                    total += q
                    if q > best_p:
                        best_p, best_path = q, path
                    if count > max_paths:
                        raise RuntimeError("too many paths for brute force")
                continue
            if kind in ("M", "I"):
                if i == n:
                    continue
                q *= (model.match_emissions if kind == "M" else model.insert_emissions)[k][x[i]]
                j = i + 1
            if q > 0:
                stack.append((nxt, j, q, path + [f"{kind}{k}"]))
    return {"viterbi_prob": best_p, "forward_prob": total, "best_path": best_path,
            "path_count": count}


def brute_force_paths(model: ProfileHMM, sequence: str, *, max_paths: int = 200_000) -> list:
    """Every Begin->End state path emitting ``sequence`` with its joint probability,
    by plain enumeration (no DP). Returns [(["M1", "D2", ...], prob), ...]."""
    x = model.encode(sequence)
    n, L = len(x), model.length
    out = []
    stack = [(("B", 0), 0, 1.0, [])]
    while stack:
        state, i, p, path = stack.pop()
        kind0, k0 = state
        k0 = 0 if kind0 == "B" else k0
        nexts = [("I", k0)] + ([("M", k0 + 1), ("D", k0 + 1)] if k0 < L else [("E", 0)])
        for nxt in nexts:
            t = model.transition(state, nxt)
            if t == 0.0:
                continue
            q, j = p * t, i
            kind, k = nxt
            if kind == "E":
                if i == n:
                    out.append((path, q))
                    if len(out) > max_paths:
                        raise RuntimeError("too many paths for brute force")
                continue
            if kind in ("M", "I"):
                if i == n:
                    continue
                q *= (model.match_emissions if kind == "M" else model.insert_emissions)[k][x[i]]
                j = i + 1
            if q > 0:
                stack.append((nxt, j, q, path + [(kind, k)]))
    return [([f"{kd}{kk}" for kd, kk in pth], q) for pth, q in out]


def brute_force_expected_counts(model: ProfileHMM, sequences) -> dict:
    """Exact posterior expected counts by weighting every enumerated path by
    P(path | x) - an independent check of the forward-backward E-step."""
    counts = {p: np.zeros_like(getattr(model, p)) for p in
              ("match_emissions", "insert_emissions", "t_match", "t_insert", "t_delete")}
    L = model.length
    key = {"B": "t_match", "M": "t_match", "I": "t_insert", "D": "t_delete"}
    col = {"M": TO_M, "I": TO_I, "D": TO_D}
    for seq in sequences:
        x = model.encode(seq)
        paths = brute_force_paths(model, seq)
        px = sum(q for _, q in paths)
        for names, q in paths:
            w = q / px
            prev, i = ("B", 0), 0
            for name in names + ["E0"]:
                kind, k = name[0], int(name[1:])
                pk, pkk = prev
                target = TO_M if kind == "E" else col[kind]
                counts[key[pk]][pkk][target] += w
                if kind == "M":
                    counts["match_emissions"][k][x[i]] += w; i += 1
                elif kind == "I":
                    counts["insert_emissions"][k][x[i]] += w; i += 1
                prev = (kind, k)
    return counts
