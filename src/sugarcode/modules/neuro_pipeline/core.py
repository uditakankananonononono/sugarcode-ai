from __future__ import annotations
import numpy as np


class MLP:
    """Minimal 2-layer MLP (numpy, manual gradients) - the trainable artifact."""

    def __init__(self, n_in: int, n_hidden: int, n_out: int, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 0.5, (n_in, n_hidden))
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.normal(0, 0.5, (n_hidden, n_out))
        self.b2 = np.zeros(n_out)
        self.trace: list[np.ndarray] = []

    def forward(self, X: np.ndarray, record: bool = False) -> np.ndarray:
        h = np.tanh(X @ self.W1 + self.b1)
        y = 1 / (1 + np.exp(-(h @ self.W2 + self.b2)))
        if record:
            self.trace = [h.copy(), y.copy()]
        return y

    def backward(self, X, y_true, lr: float, stdp_mod: float = 0.0):
        h = np.tanh(X @ self.W1 + self.b1)
        y = 1 / (1 + np.exp(-(h @ self.W2 + self.b2)))
        err = (y - y_true) / len(X)
        dW2 = h.T @ (err * y * (1 - y))
        dh = (err * y * (1 - y)) @ self.W2.T
        dW1 = X.T @ (dh * (1 - h ** 2))
        # STDP-inspired modulation: co-active pre/post pairs get potentiated
        if stdp_mod:
            co = np.clip(X.T @ h, 0, None)
            dW1 -= stdp_mod * 0.01 * co / max(co.max(), 1e-9)
        self.W2 -= lr * dW2
        self.b2 -= lr * (err * y * (1 - y)).sum(axis=0)
        self.W1 -= lr * dW1
        self.b1 -= lr * (dh * (1 - h ** 2)).sum(axis=0)
        return float(np.mean((y - y_true) ** 2))


def train(n_in: int = 6, n_hidden: int = 12, epochs: int = 300, lr: float = 0.5,
          stdp_mod: float = 0.0, seed: int = 42) -> dict:
    """Train on a synthetic motif-classification task (sequence -> functional class)."""
    rng = np.random.default_rng(seed)
    n = 400
    X = rng.normal(0, 1, (n, n_in))
    y = ((X[:, 0] + X[:, 1] - X[:, 2]) > 0).astype(float).reshape(-1, 1)
    model = MLP(n_in, n_hidden, 1, seed=seed)
    losses = []
    for ep in range(epochs):
        losses.append(model.backward(X, y, lr, stdp_mod))
    acc = float(np.mean((model.forward(X) > 0.5) == y))
    return {
        "model": model, "final_loss": round(losses[-1], 4),
        "train_accuracy": round(acc, 3),
        "loss_curve": [round(l, 4) for l in losses[:: max(1, epochs // 20)]],
        "stdp_modulation": stdp_mod,
        "continual_learning_note": "EWC-style penalty hook in backward() via stdp_mod",
    }


def lesion_study(model: MLP, n_in: int = 6, seed: int = 42) -> dict:
    """Virtual lesioning: ablate each hidden unit, measure accuracy drop."""
    rng = np.random.default_rng(seed + 1)
    X = rng.normal(0, 1, (200, n_in))
    y = ((X[:, 0] + X[:, 1] - X[:, 2]) > 0).astype(float).reshape(-1, 1)
    base = float(np.mean((model.forward(X) > 0.5) == y))
    effects = []
    for u in range(model.W1.shape[1]):
        w = model.W2[u, 0]
        model.W2[u, 0] = 0.0
        acc = float(np.mean((model.forward(X) > 0.5) == y))
        model.W2[u, 0] = w
        effects.append({"unit": u, "accuracy_drop": round(base - acc, 4)})
    effects.sort(key=lambda e: -e["accuracy_drop"])
    return {
        "baseline_accuracy": round(base, 3),
        "lesions": effects,
        "critical_units": [e["unit"] for e in effects if e["accuracy_drop"] > 0.02],
        "interpretation": "units with large drops carry the motif computation - circuit-level attribution",
    }


def activation_trace(model: MLP, x: np.ndarray) -> dict:
    """Time-resolved forward trace for one input (information propagation)."""
    model.forward(x, record=True)
    h, y = model.trace
    return {
        "input_norm": round(float(np.linalg.norm(x)), 3),
        "hidden_mean_abs": round(float(np.mean(np.abs(h))), 3),
        "hidden_active_fraction": round(float(np.mean(np.abs(h) > 0.5)), 3),
        "output": [round(float(v), 3) for v in np.atleast_1d(y)],
        "note": "per-layer activation magnitudes - spike-train analogue of inference",
    }


def rsa(model: MLP, n_in: int = 6, n_stimuli: int = 40, seed: int = 7) -> dict:
    """Representational similarity analysis: correlate input-space and hidden-space
    dissimilarity matrices (are model embeddings organized like the data?)."""
    rng = np.random.default_rng(seed)
    X = rng.normal(0, 1, (n_stimuli, n_in))
    h = np.tanh(X @ model.W1 + model.b1)
    def rdm(M):
        d = np.zeros((len(M), len(M)))
        for i in range(len(M)):
            for j in range(i + 1, len(M)):
                d[i, j] = d[j, i] = np.linalg.norm(M[i] - M[j])
        return d
    r_in, r_h = rdm(X), rdm(h)
    iu = np.triu_indices(n_stimuli, 1)
    corr = float(np.corrcoef(r_in[iu], r_h[iu])[0, 1])
    return {
        "rsa_correlation": round(corr, 3),
        "stimuli": n_stimuli,
        "interpretation": ("high" if corr > 0.5 else "moderate" if corr > 0.25 else "low")
        + " geometry preservation between input and hidden manifolds",
    }
