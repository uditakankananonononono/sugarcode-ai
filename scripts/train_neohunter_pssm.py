"""Fit per-allele position-specific scoring matrices (ridge on one-hot 9-mers) from the
IEDB 2013 MHC-I binding benchmark (measured IC50 nM):
  http://tools.iedb.org/static/main/binding_data_2013.zip  (bdata.20130222.mhci.txt)
Target y = 1 - ln(IC50)/ln(50000) clipped to [0,1] (NetMHC convention). Only
inequality '=' rows, human, 9-mers. 80/20 split by fixed hash for held-out metrics.
Data is a static 2013 snapshot (not a live IEDB query). Stored metrics come from the 80% fit;
shipped weights are refit on all rows; held-out peptides can have close training neighbours
(optimistic for novel peptides).
Usage: python scripts/train_neohunter_pssm.py bdata.20130222.mhci.txt
"""
import sys, json, math, hashlib, collections
import numpy as np

AA = "ACDEFGHIKLMNPQRSTVWY"
ALLELES = ["HLA-A*02:01", "HLA-A*03:01", "HLA-A*24:02", "HLA-B*07:02", "HLA-B*44:03"]
LAM = 5.0


def onehot(seq):
    x = np.zeros(9 * 20)
    for i, a in enumerate(seq):
        x[i * 20 + AA.index(a)] = 1
    return x


def auc(y_true_bind, score):
    order = np.argsort(score); r = np.empty(len(score)); r[order] = np.arange(1, len(score) + 1)
    pos = y_true_bind.sum(); neg = len(score) - pos
    return float((r[y_true_bind].sum() - pos * (pos + 1) / 2) / (pos * neg))


def main(path):
    data = collections.defaultdict(list)
    for line in open(path).read().splitlines()[1:]:
        sp, mhc, L, seq, ineq, meas = line.split("\t")
        if sp == "human" and mhc in ALLELES and L == "9" and ineq == "=" and set(seq) <= set(AA):
            data[mhc].append((seq, float(meas)))
    out = {"source": "IEDB MHC-I binding benchmark 2013 (bdata.20130222.mhci.txt), measured IC50 nM",
           "target": "1 - ln(IC50 nM)/ln(50000), clipped 0..1", "method": f"ridge(lambda={LAM}) on one-hot 9-mer", "alleles": {}}
    for al, rows in data.items():
        X = np.array([onehot(s) for s, _ in rows]); ic = np.array([m for _, m in rows])
        y = np.clip(1 - np.log(np.clip(ic, 1, None)) / math.log(50000), 0, 1)
        test = np.array([int(hashlib.md5(s.encode()).hexdigest(), 16) % 5 == 0 for s, _ in rows])
        def fit(Xa, ya):
            Xa1 = np.hstack([Xa, np.ones((len(Xa), 1))]); R = LAM * np.eye(Xa1.shape[1]); R[-1, -1] = 0
            return np.linalg.solve(Xa1.T @ Xa1 + R, Xa1.T @ ya)
        w = fit(X[~test], y[~test]); pred = np.hstack([X[test], np.ones((test.sum(), 1))]) @ w
        pear = float(np.corrcoef(pred, y[test])[0, 1]); a = auc(ic[test] < 500, pred)
        wf = fit(X, y)
        out["alleles"][al] = {"n_train_total": len(rows), "n_heldout": int(test.sum()), "heldout_pearson_r": round(pear, 4),
                              "heldout_auc_ic50_lt_500nM": round(a, 4), "bias": float(wf[-1]),
                              "weights": {str(i): {AA[j]: round(float(wf[i * 20 + j]), 5) for j in range(20)} for i in range(9)}}
        print(al, len(rows), "r=%.3f auc=%.3f" % (pear, a))
    json.dump(out, open("src/sugarcode/modules/neohunter/data_pssm_iedb2013.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
