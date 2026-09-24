"""Train the SugarCode module router on the repo's own text.

Corpus: for every registered module, its spec document (spec/<slug>.md),
registry name + summary, and the docstrings of its public functions, cut into
short passages. A seeded, stratified 80/20 passage split gives a held-out
test set; a separate author-written query set (tests/fixtures/router_queries.json)
checks transfer to real user phrasing. Two baselines are reported: majority
class and an untrained nearest-centroid TF-IDF retriever.

Usage: python scripts/train_router.py   (writes src/sugarcode/llm/data/)
"""
from __future__ import annotations

import inspect
import importlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from omega.registry import REGISTRY  # noqa: E402
from sugarcode.llm.router import Router, Vectorizer, train_softmax  # noqa: E402

SEED = 7


def passages_for(slug: str) -> list[str]:
    spec = REGISTRY[slug]
    out = [f"{spec.name}. {spec.summary}", spec.summary]
    sp = ROOT / "spec" / f"{slug}.md"
    if sp.exists():
        text = re.sub(r"[#*`>|]", " ", sp.read_text(errors="ignore"))
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n{2,}", text) if len(s.strip()) > 25]
        for i in range(0, len(sents), 2):
            out.append(" ".join(sents[i:i + 2]))
    try:
        mod = importlib.import_module(f"sugarcode.modules.{slug}")
        for n in (getattr(mod, "__all__", None) or dir(mod)):
            f = getattr(mod, n, None)
            if inspect.isfunction(f) and f.__doc__ and getattr(f, "__module__", "").startswith(f"sugarcode.modules.{slug}"):
                doc = inspect.getdoc(f).split("\n\n")[0].replace("\n", " ")
                out.append(f"{n.replace('_', ' ')}. {doc}")
    except Exception:
        pass
    return out


def topk_hits(P: np.ndarray, gold: list[set[int]], k: int) -> float:
    top = np.argsort(-P, axis=1)[:, :k]
    return float(np.mean([bool(set(t) & g) for t, g in zip(top, gold)]))


def main() -> None:
    t0 = time.time()
    labels = sorted(REGISTRY)
    lid = {s: i for i, s in enumerate(labels)}
    docs, y = [], []
    for s in labels:
        for p in passages_for(s):
            docs.append(p)
            y.append(lid[s])
    y = np.array(y)
    rng = np.random.default_rng(SEED)
    test_mask = np.zeros(len(y), bool)
    for c in range(len(labels)):
        idx = np.flatnonzero(y == c)
        idx = idx[2:]  # keep name+summary passages always in train
        rng.shuffle(idx)
        test_mask[idx[: int(round(0.2 * len(idx)))]] = True
    tr, te = ~test_mask, test_mask
    tr_docs = [d for d, m in zip(docs, tr) if m]
    te_docs = [d for d, m in zip(docs, te) if m]

    vec = Vectorizer.fit(tr_docs)
    Xtr, Xte = vec.transform(tr_docs), vec.transform(te_docs)
    W, b = train_softmax(Xtr, y[tr], len(labels), seed=SEED)
    model = Router(vec, W, b, labels)

    qpath = ROOT / "tests/fixtures/router_queries.json"
    queries = json.loads(qpath.read_text())["queries"] if qpath.exists() else []
    if not queries:  # module display names as short queries (not in the held-out split)
        queries = [{"q": REGISTRY[s].name, "modules": [s]} for s in labels]
    q_text = [q["q"] for q in queries]
    q_gold = [{lid[m] for m in q["modules"]} for q in queries]

    def centroid_probs(vec_, Xfit, yfit, texts):
        C = np.zeros((len(labels), Xfit.shape[1]))
        for c in range(len(labels)):
            m = Xfit[yfit == c]
            if len(m):
                C[c] = m.mean(0)
        C /= np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-12)
        return vec_.transform(texts) @ C.T

    te_gold = [{c} for c in y[te]]
    maj = np.bincount(y[tr]).argmax()
    report = {
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "seed": SEED, "n_modules": len(labels), "n_passages": len(docs),
        "n_train": int(tr.sum()), "n_test": int(te.sum()), "vocab": len(vec.vocab),
        "heldout_passages": {
            "softmax_top1": topk_hits(model.predict_proba(te_docs), te_gold, 1),
            "softmax_top3": topk_hits(model.predict_proba(te_docs), te_gold, 3),
            "centroid_top1": topk_hits(centroid_probs(vec, Xtr, y[tr], te_docs), te_gold, 1),
            "centroid_top3": topk_hits(centroid_probs(vec, Xtr, y[tr], te_docs), te_gold, 3),
            "majority_top1": float(np.mean(y[te] == maj)),
        },
        "author_queries": {
            "n": len(queries),
            "softmax_top1": topk_hits(model.predict_proba(q_text), q_gold, 1),
            "softmax_top3": topk_hits(model.predict_proba(q_text), q_gold, 3),
            "centroid_top1": topk_hits(centroid_probs(vec, Xtr, y[tr], q_text), q_gold, 1),
            "centroid_top3": topk_hits(centroid_probs(vec, Xtr, y[tr], q_text), q_gold, 3),
        },
    }
    # final model: refit on every passage (held-out numbers above come from the split)
    vec_all = Vectorizer.fit(docs)
    W_all, b_all = train_softmax(vec_all.transform(docs), y, len(labels), seed=SEED)
    final = Router(vec_all, W_all, b_all, labels)
    report["final_model"] = {"trained_on": "all passages", "vocab": len(vec_all.vocab),
                             "author_queries_top3_after_refit": topk_hits(final.predict_proba(q_text), q_gold, 3)}
    report["train_seconds"] = round(time.time() - t0, 1)
    out = ROOT / "src/sugarcode/llm/data"
    out.mkdir(parents=True, exist_ok=True)
    final.save(out / "router.npz")
    (out / "router_report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
