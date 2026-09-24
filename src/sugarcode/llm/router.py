"""Trained module router: natural-language question -> most relevant SugarCode modules.

A TF-IDF (word unigram + bigram) softmax-regression classifier trained on
SugarCode's own text: each module's spec document, registry summary, and the
docstrings of its functions. Training is reproducible with
`python scripts/train_router.py`; weights ship in `llm/data/router.npz` along
with a JSON report of held-out accuracy against two baselines.

This is a small classical model, trained here, not a neural network. It
narrows 231 tools to the handful an LLM should see for a given question,
which is what makes small local open-weight models usable as the copilot.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np

DATA = Path(__file__).with_name("data")
_WORD = re.compile(r"[a-z0-9][a-z0-9\-']*")
_STOP = set("""a an the and or of to in on for with by from as at is are was were be been being this that
these those it its into via than then so such can may might will would should could not no nor do does did
has have had which who whom whose what when where why how all any each both few more most other some own
same very just also only over under between within without about across per their they them we our you your
i me my he she his her us up down out off again further once here there""".split())


def tokenize(text: str) -> list[str]:
    words = [w.strip("-'") for w in _WORD.findall(text.lower().replace("_", " "))]
    words = [w for w in words if w and w not in _STOP and len(w) > 1]
    return words + [f"{a} {b}" for a, b in zip(words, words[1:])]


class Vectorizer:
    def __init__(self, vocab: list[str], idf: np.ndarray):
        self.vocab = vocab
        self.index = {t: i for i, t in enumerate(vocab)}
        self.idf = idf.astype(np.float64)

    @classmethod
    def fit(cls, docs: list[str], max_features: int = 6000, min_df: int = 2) -> "Vectorizer":
        df: Counter = Counter()
        for d in docs:
            df.update(set(tokenize(d)))
        terms = [t for t, c in df.items() if c >= min_df]
        terms.sort(key=lambda t: (-df[t], t))
        terms = sorted(terms[:max_features])
        n = len(docs)
        idf = np.array([math.log((1 + n) / (1 + df[t])) + 1.0 for t in terms])
        return cls(terms, idf)

    def transform(self, docs: list[str]) -> np.ndarray:
        X = np.zeros((len(docs), len(self.vocab)))
        for i, d in enumerate(docs):
            for t, c in Counter(tokenize(d)).items():
                j = self.index.get(t)
                if j is not None:
                    X[i, j] = 1.0 + math.log(c)
        X *= self.idf
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        return X / np.maximum(norms, 1e-12)


def _softmax(Z: np.ndarray) -> np.ndarray:
    Z = Z - Z.max(axis=1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)


def train_softmax(X: np.ndarray, y: np.ndarray, n_classes: int, l2: float = 1e-4,
                  epochs: int = 300, lr: float = 2.0, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Full-batch gradient descent with Nesterov momentum on L2-regularized cross-entropy."""
    rng = np.random.default_rng(seed)
    W = rng.normal(0, 1e-3, (X.shape[1], n_classes))
    b = np.zeros(n_classes)
    Y = np.eye(n_classes)[y]
    vW, vb = np.zeros_like(W), np.zeros_like(b)
    # inverse-frequency weights so modules with short specs are not drowned out
    counts = np.bincount(y, minlength=n_classes).astype(float)
    sw = (1.0 / np.maximum(counts[y], 1.0))
    sw *= len(y) / sw.sum()
    for _ in range(epochs):
        Wn, bn = W + 0.9 * vW, b + 0.9 * vb
        P = _softmax(X @ Wn + bn)
        G = (P - Y) * sw[:, None] / len(y)
        gW = X.T @ G + l2 * Wn
        gb = G.sum(axis=0)
        vW = 0.9 * vW - lr * gW
        vb = 0.9 * vb - lr * gb
        W, b = W + vW, b + vb
    return W, b


class Router:
    def __init__(self, vec: Vectorizer, W: np.ndarray, b: np.ndarray, labels: list[str]):
        self.vec, self.W, self.b, self.labels = vec, W.astype(np.float64), b.astype(np.float64), labels

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        return _softmax(self.vec.transform(texts) @ self.W + self.b)

    def route(self, text: str, k: int = 3) -> list[dict]:
        p = self.predict_proba([text])[0]
        order = np.argsort(-p)[:k]
        return [{"module": self.labels[i], "probability": round(float(p[i]), 4)} for i in order]

    def save(self, path: Path) -> None:
        np.savez_compressed(path, vocab=np.array(self.vec.vocab), idf=self.vec.idf.astype(np.float32),
                            W=self.W.astype(np.float16), b=self.b.astype(np.float32),
                            labels=np.array(self.labels))

    @classmethod
    def load(cls, path: Path) -> "Router":
        z = np.load(path, allow_pickle=False)
        vec = Vectorizer([str(t) for t in z["vocab"]], z["idf"])
        return cls(vec, z["W"], z["b"], [str(s) for s in z["labels"]])


@lru_cache(maxsize=1)
def default_router() -> Router:
    path = DATA / "router.npz"
    if not path.exists():
        raise FileNotFoundError("router weights missing; run `python scripts/train_router.py`")
    return Router.load(path)


def training_report() -> dict:
    p = DATA / "router_report.json"
    return json.loads(p.read_text()) if p.exists() else {}


def route(text: str, k: int = 3) -> list[dict]:
    return default_router().route(text, k)
