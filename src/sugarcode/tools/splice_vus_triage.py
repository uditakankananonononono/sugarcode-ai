"""splice-vus-triage: score splice-region SNVs (donor +3..+6, acceptor -3..-14)
with the best cross-validated model (logistic on PWM + MaxEntScan features,
AUROC 0.9674; falls back to the ClinVar CNN without maxentpy), optional
SpliceAI, and a calibrated PPV.

Evidence (mega27-01, discovery/splice_region_vus/): gene-grouped 5-fold CV
AUROC 0.936 (CNN) vs 0.889 (PWM); SpliceAI is stronger (0.9775 vs 0.929,
n=757), so SpliceAI is used as the primary score when installed and the CNN is
a cheap, calibrated second opinion. Output is research triage, not a clinical
classification.

Usage:
  splice-vus-triage variants.tsv --genome hg38.2bit [--spliceai] [--prior 0.03] > out.tsv
Input TSV columns: name (HGVS with c.N+k / c.N-k), chrom, pos (1-based GRCh38), ref, alt
Or: name, ref_ctx, alt_ctx (81-nt transcript-oriented windows, variant at index 40).
"""
from __future__ import annotations
import argparse, csv, json, re, sys
from pathlib import Path

F = 40
_DATA = Path(__file__).with_name("data")
_RC = str.maketrans("ACGTN", "TGCAN")
KS = [3, 4, 5, 6] + list(range(-14, -2))


def rc(s: str) -> str:
    return s.translate(_RC)[::-1]


def parse_offset(name: str) -> int:
    m = re.search(r"c\.[0-9]+([+-][0-9]+)", name)
    if not m:
        raise ValueError(f"no intronic offset in {name!r}")
    k = int(m.group(1))
    if not ((3 <= k <= 6) or (-14 <= k <= -3)):
        raise ValueError(f"offset {k} outside supported donor +3..+6 / acceptor -14..-3")
    return k


def windows_from_genome(genome, chrom: str, pos: int, ref: str, alt: str, k: int):
    ch = "chrM" if chrom in ("MT", "M", "chrM") else (chrom if chrom.startswith("chr") else "chr" + chrom)
    p = pos - 1
    seq = genome[ch][p - F:p + F + 1].upper()
    if len(seq) != 2 * F + 1 or seq[F] != ref.upper():
        raise ValueError("reference allele mismatch")
    alt_seq = seq[:F] + alt.upper() + seq[F + 1:]
    ok = []
    for strand in "+-":
        s = seq if strand == "+" else rc(seq)
        if k > 0:
            ok.append(s[F - k + 1:F - k + 3] == "GT")
        else:
            e = F - k
            ok.append(s[e - 2:e] == "AG")
    if ok.count(True) != 1:
        raise ValueError("could not infer strand from canonical GT/AG")
    strand = "+" if ok[0] else "-"
    return (seq, alt_seq, strand) if strand == "+" else (rc(seq), rc(alt_seq), strand)


def pwm_features(ref_ctx: str, alt_ctx: str, k: int) -> list[float]:
    from sugarcode.modules.deepsplice import core as ds
    site = "donor" if k > 0 else "acceptor"
    if site == "donor":
        b = F - k; rw, aw = ref_ctx[b - 2:b + 7], alt_ctx[b - 2:b + 7]
    else:
        e = F - k; rw, aw = ref_ctx[e - 14:e + 1], alt_ctx[e - 14:e + 1]
    v = ds.variant_effect(rw, aw, site)
    f = [float(v["ref_score"]), float(v["alt_score"]), float(v["delta"]), 1.0 if site == "donor" else 0.0]
    return f + [1.0 if k == kk else 0.0 for kk in KS]


_NET = None


def _net():
    global _NET
    if _NET is None:
        import torch, torch.nn as nn

        class Net(nn.Module):
            def __init__(s, nf):
                super().__init__()
                s.c = nn.Sequential(nn.Conv1d(8, 64, 9, padding=4), nn.ReLU(), nn.Dropout(0.2),
                                    nn.Conv1d(64, 64, 7, padding=3), nn.ReLU(), nn.AdaptiveMaxPool1d(1))
                s.h = nn.Sequential(nn.Linear(64 + nf, 32), nn.ReLU(), nn.Linear(32, 1))

            def forward(s, x, f):
                return s.h(torch.cat([s.c(x).squeeze(-1), f], 1)).squeeze(-1)
        n = Net(4 + len(KS)); n.load_state_dict(torch.load(_DATA / "splice_cnn_v1.pt", map_location="cpu")); n.eval()
        _NET = n
    return _NET


def cnn_score(ref_ctx: str, alt_ctx: str, k: int) -> float:
    import numpy as np, torch
    M = {"A": 0, "C": 1, "G": 2, "T": 3}

    def oh(s):
        a = np.zeros((4, len(s)), np.float32)
        for i, c in enumerate(s):
            if c in M:
                a[M[c], i] = 1
        return a
    x = torch.tensor(np.concatenate([oh(ref_ctx), oh(alt_ctx)])[None])
    f = torch.tensor([pwm_features(ref_ctx, alt_ctx, k)], dtype=torch.float32)
    with torch.no_grad():
        return float(torch.sigmoid(_net()(x, f))[0])


def maxent_scores(ref_ctx: str, alt_ctx: str, k: int):
    """MaxEntScan (Yeo & Burge 2004) ref/alt scores via maxentpy; None if not installed."""
    try:
        from maxentpy import maxent
    except ImportError:
        return None
    global _ME
    try:
        _ME
    except NameError:
        _ME = (maxent.load_matrix5(), maxent.load_matrix3())
    if k > 0:
        b = F - k
        return maxent.score5(ref_ctx[b - 2:b + 7], matrix=_ME[0]), maxent.score5(alt_ctx[b - 2:b + 7], matrix=_ME[0])
    e = F - k
    return maxent.score3(ref_ctx[e - 20:e + 3], matrix=_ME[1]), maxent.score3(alt_ctx[e - 20:e + 3], matrix=_ME[1])


def logit_me_score(ref_ctx: str, alt_ctx: str, k: int):
    """Best CV model (AUROC 0.9674 vs MaxEntScan 0.9635): logistic on PWM + MaxEntScan features."""
    me = maxent_scores(ref_ctx, alt_ctx, k)
    if me is None:
        return None
    import math
    m = json.load(open(_DATA / "splice_logit_me_v1.json"))
    f = pwm_features(ref_ctx, alt_ctx, k)
    x = f[:4] + [me[0] / 10, me[1] / 10, (me[0] - me[1]) / 10] + f[4:]
    z = m["intercept"] + sum(c * v for c, v in zip(m["coef"], x))
    return 1 / (1 + math.exp(-z))


def calibrated(cnn: float, prior: float, table: str = "cnn") -> dict:
    if table == "logit_me":
        tab = json.load(open(_DATA / "splice_logit_me_v1.json"))["calibration"]
    else:
        tab = json.load(open(_DATA / "splice_cnn_calibration.json"))["thresholds"]
    best = None
    for t in sorted(tab, key=float):
        if cnn >= float(t):
            best = t
    if best is None:
        return {"threshold_bin": "<0.5", "sensitivity": None, "fpr": None, "ppv": None}
    s, fpr = tab[best]["sensitivity"], tab[best]["fpr"]
    ppv = s * prior / (s * prior + fpr * (1 - prior))
    return {"threshold_bin": best, "sensitivity": s, "fpr": fpr, "ppv": round(ppv, 4)}


def tier(cnn: float, sai: float | None) -> str:
    if sai is not None:
        if sai >= 0.8 and cnn >= 0.9:
            return "strong: SpliceAI>=0.8 and model>=0.9"
        if sai >= 0.5 and cnn >= 0.5:
            return "moderate: SpliceAI>=0.5 and model>=0.5"
        if sai < 0.2 and cnn < 0.5:
            return "unlikely splice-disruptive"
        return "discordant: review"
    return "strong (model only)" if cnn >= 0.98 else "moderate (model only)" if cnn >= 0.9 else "weak/none (model only)"


def spliceai_score(genome, chrom, pos, ref, alt, strand, D=50):
    import numpy as np, os
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    from keras.models import load_model
    from pkg_resources import resource_filename
    from spliceai.utils import one_hot_encode
    global _SAI
    try:
        _SAI
    except NameError:
        _SAI = [load_model(resource_filename("spliceai", f"models/spliceai{i}.h5"), compile=False) for i in range(1, 6)]
    W = 5000 + D
    ch = chrom if chrom.startswith("chr") else "chr" + chrom
    p = pos - 1
    seq = genome[ch][p - W:p + W + 1].upper()
    alts = seq[:W] + alt + seq[W + 1:]
    if strand == "-":
        seq, alts = rc(seq), rc(alts)
    x = np.stack([one_hot_encode(seq), one_hot_encode(alts)])
    y = np.mean([m.predict(x, verbose=0) for m in _SAI], axis=0)
    r, a = y[0], y[1]
    return float(max((a[:, 1] - r[:, 1]).max(), (r[:, 1] - a[:, 1]).max(), (a[:, 2] - r[:, 2]).max(), (r[:, 2] - a[:, 2]).max()))


def triage_row(row: dict, genome=None, use_spliceai=False, prior=0.03) -> dict:
    k = parse_offset(row["name"])
    strand = row.get("strand", "")
    if row.get("ref_ctx") and row.get("alt_ctx"):
        R, A = row["ref_ctx"].upper(), row["alt_ctx"].upper()
    else:
        if genome is None:
            raise ValueError("need --genome or ref_ctx/alt_ctx columns")
        R, A, strand = windows_from_genome(genome, row["chrom"], int(row["pos"]), row["ref"], row["alt"], k)
    c = cnn_score(R, A, k)
    lm = logit_me_score(R, A, k)
    me = maxent_scores(R, A, k)
    score, model = (lm, "logit_me") if lm is not None else (c, "cnn")
    sai = None
    if use_spliceai and genome is not None and row.get("chrom"):
        sai = spliceai_score(genome, row["chrom"], int(row["pos"]), row["ref"].upper(), row["alt"].upper(), strand)
    cal = calibrated(score, prior, model)
    return {"name": row["name"], "site": "donor" if k > 0 else "acceptor", "offset": k, "strand": strand,
            "model": model, "model_score": round(score, 5), "cnn": round(c, 5),
            "maxent_delta": (round(me[0] - me[1], 3) if me else "NA"),
            "spliceai_ds_max": (round(sai, 4) if sai is not None else "NA"),
            "score_bin": cal["threshold_bin"], "ppv_at_prior": cal["ppv"], "tier": tier(score, sai)}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="splice-vus-triage", description=__doc__.split("\n\n")[0])
    ap.add_argument("variants"); ap.add_argument("--genome"); ap.add_argument("--spliceai", action="store_true")
    ap.add_argument("--prior", type=float, default=0.03, help="assumed pathogenic fraction among inputs (for PPV)")
    a = ap.parse_args(argv)
    genome = None
    if a.genome:
        import twobitreader
        genome = twobitreader.TwoBitFile(a.genome)
    cols = ["name", "site", "offset", "strand", "model", "model_score", "cnn", "maxent_delta", "spliceai_ds_max", "score_bin", "ppv_at_prior", "tier", "error"]
    w = csv.DictWriter(sys.stdout, cols, delimiter="\t", extrasaction="ignore"); w.writeheader()
    for row in csv.DictReader(open(a.variants), delimiter="\t"):
        try:
            w.writerow(triage_row(row, genome, a.spliceai, a.prior))
        except Exception as e:
            w.writerow({"name": row.get("name", ""), "error": str(e)[:120]})
    return 0


if __name__ == "__main__":
    sys.exit(main())
