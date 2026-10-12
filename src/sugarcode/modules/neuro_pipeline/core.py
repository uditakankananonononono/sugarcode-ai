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
    """Train on a synthetic toy task (Gaussian features -> class).

    Toy-task entry point retained for compatibility and smoke tests (Gaussian features, no biological content). For biological
    sequence classification (DNA motifs), use train_on_sequences()."""
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
        "plasticity_note": ("stdp_mod applies STDP-style co-activation potentiation "
                            "to W1; it is NOT an EWC penalty. For continual learning "
                            "with a weight-anchor penalty (no Fisher term), use "
                            "continual_update()."),
    }


def lesion_study(model: MLP, n_in: int | None = None, seed: int = 42,
                 X: np.ndarray | None = None, y: np.ndarray | None = None) -> dict:
    """Virtual lesioning: ablate each hidden unit, measure accuracy drop.

    Pass X/y to lesion on a specific dataset (e.g. encoded DNA sequences);
    defaults to the built-in toy task."""
    if X is None or y is None:
        n_in = model.W1.shape[0] if n_in is None else n_in
        if n_in < 3:
            raise ValueError("built-in toy task needs >= 3 inputs; pass X/y")
        rng = np.random.default_rng(seed + 1)
        X = rng.normal(0, 1, (200, n_in))
        y = ((X[:, 0] + X[:, 1] - X[:, 2]) > 0).astype(float).reshape(-1, 1)
    X = np.asarray(X, float); y = np.asarray(y, float).reshape(-1, 1)
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
    """Per-layer forward trace for one input (activation magnitudes, single forward pass)."""
    model.forward(x, record=True)
    h, y = model.trace
    return {
        "input_norm": round(float(np.linalg.norm(x)), 3),
        "hidden_mean_abs": round(float(np.mean(np.abs(h))), 3),
        "hidden_active_fraction": round(float(np.mean(np.abs(h) > 0.5)), 3),
        "output": [round(float(v), 3) for v in np.atleast_1d(y).ravel()],
        "note": "per-layer activation magnitudes from one forward pass; for per-step activations over an input sequence see temporal_activation_trace",
    }


def rsa(model: MLP, n_in: int | None = None, n_stimuli: int = 40, seed: int = 7,
        X: np.ndarray | None = None) -> dict:
    """Representational similarity analysis: correlate input-space and hidden-space
    dissimilarity matrices (are model embeddings organized like the data?).

    n_in defaults to the model's input width (a fixed 6 crashed on every
    sequence-trained model); pass X to supply your own stimuli (e.g. encoded DNA)."""
    if X is None:
        rng = np.random.default_rng(seed)
        X = rng.normal(0, 1, (n_stimuli, model.W1.shape[0] if n_in is None else n_in))
    X = np.asarray(X, float); n_stimuli = len(X)
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

# ---------------------------------------------------------------------------
# Biological sequence support (DNA motif classification).
# ---------------------------------------------------------------------------

_DNA = "ACGT"


def one_hot_encode(sequences, max_len: int | None = None) -> np.ndarray:
    """One-hot encode DNA sequences (A/C/G/T) into a flat float array.

    Non-ACGT bases raise ValueError. Sequences are truncated or
    zero-padded to max_len (default: longest input)."""
    seqs = [str(s).upper() for s in sequences]
    if not seqs:
        raise ValueError("at least one sequence required")
    bad = {b for s in seqs for b in s if b not in _DNA}
    if bad:
        raise ValueError(f"invalid DNA base(s): {sorted(bad)}")
    L = max_len or max(len(s) for s in seqs)
    X = np.zeros((len(seqs), L * 4))
    for i, s in enumerate(seqs):
        for j, base in enumerate(s[:L]):
            k = _DNA.find(base)
            if k >= 0:
                X[i, j * 4 + k] = 1.0
    return X


def kmer_encode(sequences, k: int = 3) -> np.ndarray:
    """Normalised k-mer frequency vectors for DNA sequences (4**k features)."""
    if not 1 <= k <= 5:
        raise ValueError("k must be in 1..5")
    seqs = [str(s).upper() for s in sequences]
    if not seqs:
        raise ValueError("at least one sequence required")
    bad = {b for s in seqs for b in s if b not in _DNA}
    if bad:
        raise ValueError(f"invalid DNA base(s): {sorted(bad)}")
    idx = {}
    n = 0
    for a in range(4 ** k):
        pass
    # map k-mer -> column index
    order = []
    def _rec(prefix, depth):
        if depth == k:
            order.append(prefix); return
        for b in _DNA:
            _rec(prefix + b, depth + 1)
    _rec("", 0)
    idx = {w: i for i, w in enumerate(order)}
    X = np.zeros((len(seqs), 4 ** k))
    for i, s in enumerate(seqs):
        counts = np.zeros(4 ** k)
        for j in range(len(s) - k + 1):
            w = s[j:j + k]
            if w in idx:
                counts[idx[w]] += 1
        total = counts.sum()
        X[i] = counts / total if total else counts
    return X


def synthetic_promoter_dataset(n: int = 400, seq_len: int = 50,
                               motif: str = "TATAAA", seed: int = 42) -> dict:
    """Promoter-like DNA dataset: half the sequences carry a planted motif.

    Positives get `motif` (default TATA-box consensus) inserted at a random
    position; negatives are random sequence with the motif censored. This is
    synthetic data: the A/C/G/T alphabet, random background and one planted
    fixed motif. It carries no genomic data and no motif grammar. Returns {sequences, labels, motif, seq_len}."""
    rng = np.random.default_rng(seed)
    seqs, labels = [], []
    m = str(motif).upper()
    for i in range(n):
        s = "".join(rng.choice(list(_DNA), size=seq_len))
        if i % 2 == 0:
            pos = int(rng.integers(0, seq_len - len(m) + 1))
            s = s[:pos] + m + s[pos + len(m):]
            labels.append(1.0)
        else:
            while m in s:  # censor accidental motif in negatives
                pos = s.index(m)
                s = s[:pos] + "".join(rng.choice(list(_DNA), size=len(m))) + s[pos + len(m):]
            labels.append(0.0)
        seqs.append(s)
    return {"sequences": seqs, "labels": np.array(labels).reshape(-1, 1),
            "motif": m, "seq_len": seq_len}


def _stratified_split(labels, holdout, seed):
    y = np.asarray(labels).ravel()
    rng = np.random.default_rng(seed + 1000)
    test = []
    for c in np.unique(y):
        idx = rng.permutation(np.flatnonzero(y == c))
        test.extend(idx[:int(round(holdout * len(idx)))].tolist())
    test = np.array(sorted(test), int)
    train = np.setdiff1d(np.arange(len(y)), test)
    return train, test


def _encode(sequences, encoding, k, max_len=None):
    return kmer_encode(sequences, k=k) if encoding == "kmer" else one_hot_encode(sequences, max_len=max_len)


def train_on_sequences(sequences=None, labels=None, k: int = 3,
                       encoding: str = "onehot", n_hidden: int = 24,
                       epochs: int = 800, lr: float = 0.8,
                       stdp_mod: float = 0.0, seed: int = 42,
                       holdout: float = 0.2) -> dict:
    """Train the MLP to classify DNA sequences by motif content.

    Defaults to synthetic_promoter_dataset() (TATA-box vs random). Pass your
    own sequences + labels (0/1) to use your own sequence data. encoding is
    'onehot' (default, position-specific) or 'kmer' (4**k frequency features).

    A stratified `holdout` fraction (default 0.2) is kept out of training and
    scored separately: training accuracy alone hid severe overfitting (default
    one-hot run: train 0.975 vs 0.562 on fresh sequences). Set holdout=0 to
    train on everything (no generalisation estimate is then reported)."""
    if encoding not in ("onehot", "kmer"):
        raise ValueError("encoding must be 'onehot' or 'kmer'")
    if not 0 <= holdout < 1:
        raise ValueError("holdout must be in [0, 1)")
    if sequences is None:
        data = synthetic_promoter_dataset(seed=seed)
        sequences, labels = data["sequences"], data["labels"]
        dataset_note = ("built-in synthetic promoter dataset: planted "
                        f"{data['motif']} motif vs motif-free random DNA")
    else:
        if labels is None:
            raise ValueError("labels required when sequences are provided")
        dataset_note = "user-supplied sequences"
    labels = np.asarray(labels, float).reshape(-1, 1)
    sequences = list(sequences)
    if len(sequences) != len(labels):
        raise ValueError("sequences and labels differ in length")
    max_len = max(len(s) for s in sequences) if encoding == "onehot" else None
    X = _encode(sequences, encoding, k, max_len)
    tr, te = _stratified_split(labels, holdout, seed) if holdout > 0 else (np.arange(len(X)), np.array([], int))
    model = MLP(X.shape[1], n_hidden, 1, seed=seed)
    losses = []
    for _ in range(epochs):
        losses.append(model.backward(X[tr], labels[tr], lr, stdp_mod))
    acc = float(np.mean((model.forward(X[tr]) > 0.5) == labels[tr]))
    hacc = float(np.mean((model.forward(X[te]) > 0.5) == labels[te])) if len(te) else None
    return {
        "model": model, "final_loss": round(losses[-1], 4),
        "train_accuracy": round(acc, 3),
        "holdout_accuracy": None if hacc is None else round(hacc, 3),
        "generalization_gap": None if hacc is None else round(acc - hacc, 3),
        "n_train": int(len(tr)), "n_holdout": int(len(te)),
        "holdout_index": te.tolist(),
        "loss_curve": [round(l, 4) for l in losses[:: max(1, epochs // 20)]],
        "encoding": encoding, "k": k if encoding == "kmer" else None,
        "max_len": max_len,
        "n_sequences": len(sequences), "n_features": int(X.shape[1]),
        "dataset": dataset_note,
        "plasticity_note": ("stdp_mod applies STDP-style co-activation potentiation; "
                            "use continual_update() for a weight-anchor penalty "
                            "(no Fisher term)."),
    }


def predict_sequences(run: dict, sequences) -> np.ndarray:
    """Score new sequences with a train_on_sequences() result, using the same
    encoding and one-hot width as training (sequences are padded/truncated)."""
    X = _encode(list(sequences), run["encoding"], run["k"] or 3, run.get("max_len"))
    return run["model"].forward(X).ravel()


def sequence_pipeline_demo(seed: int = 42) -> dict:
    """End-to-end biological demo: train on the TATA-box promoter dataset,
    then lesion the trained model on its held-out sequences, encoded the same
    way as training."""
    run = train_on_sequences(seed=seed)
    data = synthetic_promoter_dataset(seed=seed)
    te = np.array(run["holdout_index"], int)
    X = _encode([data["sequences"][i] for i in te], run["encoding"], run["k"] or 3, run["max_len"])
    y = data["labels"][te]
    lesion = lesion_study(run["model"], X=X, y=y)
    return {"training": {k: v for k, v in run.items() if k not in ("model", "holdout_index")},
            "lesion_on_sequences": lesion, "lesion_data": "held-out sequences"}

# Explicit multimodal, continual-learning and causal-debugging extensions.
def align_modalities(modalities,latent_dim=4):
    if len(modalities)<2: raise ValueError('at least two modalities required')
    embeddings={}; reconstruction={}
    for name,X in modalities.items():
        X=np.asarray(X,float); centered=X-X.mean(0); u,s,vt=np.linalg.svd(centered,full_matrices=False); k=min(latent_dim,vt.shape[0]); z=centered@vt[:k].T; embeddings[name]=z; reconstruction[name]=float(np.mean((centered-z@vt[:k])**2))
    n=min(map(len,embeddings.values())); names=list(embeddings); similarities={}
    for i,a in enumerate(names):
        for b in names[i+1:]:
            za=embeddings[a][:n]; zb=embeddings[b][:n]; k=min(za.shape[1],zb.shape[1]); similarities[f'{a}:{b}']=float(np.mean(np.sum(za[:,:k]*zb[:,:k],1)/(np.linalg.norm(za[:,:k],axis=1)*np.linalg.norm(zb[:,:k],axis=1)+1e-9)))
    return {'embeddings':{k:v.tolist() for k,v in embeddings.items()},'cross_modal_cosine':similarities,'reconstruction_mse':reconstruction,'latent_dim':latent_dim}

def spiking_dynamics(inputs,threshold=1,decay=.9,refractory_steps=1):
    X=np.asarray(inputs,float); v=np.zeros(X.shape[1]); ref=np.zeros(X.shape[1],int); spikes=[]; voltage=[]
    for x in X:
        v=decay*v+x; v[ref>0]=0; fire=v>=threshold; spikes.append(fire.astype(int).tolist()); v[fire]=0; ref=np.maximum(0,ref-1); ref[fire]=refractory_steps; voltage.append(v.copy().tolist())
    return {'spikes':spikes,'voltage':voltage,'firing_rate':np.asarray(spikes).mean(0).tolist()}

def predictive_coding(observations,steps=20,learning_rate=.1):
    y=np.asarray(observations,float); state=np.zeros_like(y[0]); errors=[]; trajectory=[]
    target=y.mean(0)
    for _ in range(steps):
        err=target-state; errors.append(float(np.mean(err**2))); state+=learning_rate*err; trajectory.append(state.copy().tolist())
    return {'latent_state':state.tolist(),'prediction_error':errors,'trajectory':trajectory}

def continual_update(model,X,y,previous=None,lr=.1,epochs=20,ewc_lambda=1):
    """Train with a weight-anchor penalty: each step pulls W1 and W2 back toward the
    previous weights, scaled by ewc_lambda. There is no Fisher term, so this is not
    full EWC; the output key keeps the name ewc_lambda."""
    old=[model.W1.copy(),model.W2.copy()] if previous is None else previous
    losses=[]
    for _ in range(epochs):
        loss=model.backward(np.asarray(X,float),np.asarray(y,float),lr); model.W1-=lr*ewc_lambda*(model.W1-old[0])/len(X); model.W2-=lr*ewc_lambda*(model.W2-old[1])/len(X); losses.append(loss)
    drift=float(np.linalg.norm(model.W1-old[0])+np.linalg.norm(model.W2-old[1])); return {'model':model,'loss_curve':losses,'parameter_drift':drift,'ewc_lambda':ewc_lambda}

def functional_connectivity(model,threshold=.15):
    strength=np.abs(model.W1[:,:,None]*model.W2[None,:,:]).sum(2); edges=[]
    for i in range(strength.shape[0]):
        for h in range(strength.shape[1]):
            if strength[i,h]>=threshold: edges.append({'source':f'input:{i}','target':f'hidden:{h}','strength':float(strength[i,h])})
    return {'nodes':strength.shape[0]+strength.shape[1]+model.W2.shape[1],'edges':edges,'density':len(edges)/max(1,strength.size)}

def causal_intervention(model,X,feature,value=0):
    X=np.asarray(X,float); baseline=model.forward(X); do=X.copy(); do[:,feature]=value; changed=model.forward(do); delta=changed-baseline; return {'feature':feature,'value':value,'baseline_mean':baseline.mean(0).tolist(),'intervened_mean':changed.mean(0).tolist(),'average_causal_effect':delta.mean(0).tolist(),'individual_effects':delta.tolist()}

def physics_cotraining(model,X,y,simulator_targets,lr=.1,physics_weight=.5,epochs=20):
    X=np.asarray(X,float); y=np.asarray(y,float); sim=np.asarray(simulator_targets,float); target=(1-physics_weight)*y+physics_weight*sim; losses=[]
    for _ in range(epochs): losses.append(model.backward(X,target,lr))
    pred=model.forward(X); return {'model':model,'loss_curve':losses,'data_mse':float(np.mean((pred-y)**2)),'physics_mse':float(np.mean((pred-sim)**2)),'physics_weight':physics_weight}

def feedback_reward_update(prior_alpha,prior_beta,outcomes):
    o=np.asarray(outcomes,float); a=prior_alpha+o.sum(); b=prior_beta+len(o)-o.sum(); return {'alpha':float(a),'beta':float(b),'reward_mean':float(a/(a+b)),'uncertainty':float(np.sqrt(a*b/((a+b)**2*(a+b+1))))}

def pipeline_report(seed=42):
    run=train(epochs=80,seed=seed); model=run['model']; lesion=lesion_study(model); connectivity=functional_connectivity(model); x=np.eye(6); causal=causal_intervention(model,x,0); return {'training':{k:v for k,v in run.items() if k!='model'},'connectivity':connectivity,'lesion':lesion,'causal':causal,'rsa':rsa(model),'feedback':feedback_reward_update(1,1,[1,0,1]),'model_status':'A small NumPy MLP and explicit algorithms; no biological foundation model or autonomous lab agent is bundled.'}

def neuro_diagnostics(seed=42):
    r=pipeline_report(seed); t=r['training']; l=r['lesion']; c=r['connectivity']; ca=r['causal']; return {'final_loss':t['final_loss'],'train_accuracy':t['train_accuracy'],'stdp_modulation':t['stdp_modulation'],'connectivity_edges':float(len(c['edges'])),'connectivity_density':c['density'],'lesion_baseline_accuracy':l['baseline_accuracy'],'critical_unit_count':float(len(l['critical_units'])),'max_lesion_drop':max((x['accuracy_drop'] for x in l['lesions']),default=0),'rsa_correlation':r['rsa']['rsa_correlation'],'causal_effect_abs':float(np.mean(np.abs(ca['average_causal_effect']))),'reward_mean':r['feedback']['reward_mean'],'reward_uncertainty':r['feedback']['uncertainty']}

# --- Timing-dependent plasticity, Fisher-weighted anchoring, temporal traces,
# --- paired alignment and a two-level predictive-coding hierarchy. -----------

def stdp_timing_update(weights, pre_spikes, post_spikes, a_plus=0.01, a_minus=0.012, tau=5.0):
    """Pair-based spike-timing-dependent plasticity on binary spike trains.

    pre_spikes: (T, n_pre), post_spikes: (T, n_post), e.g. spiking_dynamics()['spikes'].
    For each pre/post spike pair the weight change is a_plus * exp(-dt / tau) when the
    pre spike comes first (dt > 0) and -a_minus * exp(dt / tau) when the post spike
    comes first (dt < 0). Simultaneous spikes (dt == 0) add nothing. Returns the new
    weights (n_pre, n_post) and the per-synapse delta. It is not connected to MLP
    training: the MLP's stdp_mod term remains a co-activation term."""
    pre = np.asarray(pre_spikes, float); post = np.asarray(post_spikes, float)
    W = np.asarray(weights, float)
    if pre.ndim != 2 or post.ndim != 2 or pre.shape[0] != post.shape[0]:
        raise ValueError("pre_spikes and post_spikes must be (T, n) with equal T")
    if W.shape != (pre.shape[1], post.shape[1]):
        raise ValueError("weights must be (n_pre, n_post)")
    if tau <= 0:
        raise ValueError("tau must be positive")
    T = pre.shape[0]
    delta = np.zeros_like(W)
    for i in range(pre.shape[1]):
        t_pre = np.flatnonzero(pre[:, i])
        for j in range(post.shape[1]):
            t_post = np.flatnonzero(post[:, j])
            for tp in t_pre:
                for tq in t_post:
                    dt = float(tq - tp)
                    if dt > 0:
                        delta[i, j] += a_plus * np.exp(-dt / tau)
                    elif dt < 0:
                        delta[i, j] -= a_minus * np.exp(dt / tau)
    return {"weights": W + delta, "delta": delta, "steps": T,
            "rule": "pair-based STDP (all pairs, exponential windows)"}


def _logit_grads(model, X):
    """Per-sample gradient of the output logit with respect to (W1, b1, W2, b2)."""
    h = np.tanh(X @ model.W1 + model.b1)
    d1 = model.W2[:, 0][None, :] * (1 - h ** 2)            # (n, hidden)
    gW1 = X[:, :, None] * d1[:, None, :]                   # (n, in, hidden)
    gb1 = d1
    gW2 = h[:, :, None]                                    # (n, hidden, 1)
    gb2 = np.ones((len(X), 1))
    p = 1 / (1 + np.exp(-(h @ model.W2 + model.b2)))
    return p, gW1, gb1, gW2, gb2


def fisher_diagonal(model, X):
    """Exact diagonal Fisher information of the Bernoulli output head:
    F_i = mean over inputs of p(1-p) * (d logit / d theta_i)^2, for W1, b1, W2, b2."""
    X = np.asarray(X, float)
    p, gW1, gb1, gW2, gb2 = _logit_grads(model, X)
    w = (p * (1 - p))[:, 0]
    f = lambda g: np.tensordot(w, g ** 2, axes=(0, 0)) / len(X)
    return {"W1": f(gW1), "b1": f(gb1), "W2": f(gW2), "b2": f(gb2)}


def continual_update_fisher(model, X, y, fisher, previous=None, lr=0.1, epochs=20, ewc_lambda=1.0):
    """Training with a Fisher-weighted quadratic anchor on all four parameter blocks:
    after each loss step, theta <- theta - min(lr * ewc_lambda * F, 1) * (theta - theta_old).
    fisher comes from fisher_diagonal() on the earlier task. Reduces drift on
    high-Fisher parameters; it does not guarantee old-task retention."""
    names = ("W1", "b1", "W2", "b2")
    old = {k: getattr(model, k).copy() for k in names} if previous is None else previous
    X = np.asarray(X, float); y = np.asarray(y, float); losses = []
    for _ in range(epochs):
        losses.append(model.backward(X, y, lr))
        for k in names:
            cur = getattr(model, k)
            cur -= np.minimum(lr * ewc_lambda * fisher[k], 1.0) * (cur - old[k])
    drift = float(sum(np.linalg.norm(getattr(model, k) - old[k]) for k in names))
    return {"model": model, "loss_curve": losses, "parameter_drift": drift, "ewc_lambda": ewc_lambda,
            "penalty": "Fisher-diagonal weighted anchor on W1, b1, W2, b2"}


def temporal_activation_trace(model, x_sequence, threshold=0.5):
    """Hidden/output activations for each time step of an input sequence (T, n_in).

    Returns per-step hidden activations and outputs, and for each hidden unit the first
    step at which |activation| >= threshold (None if never) plus the units ordered by that
    onset step. The MLP has no state between steps, so each step is an independent
    forward pass over a time-indexed input; this is an onset ordering of activations,
    not spike timing."""
    X = np.asarray(x_sequence, float)
    if X.ndim != 2 or X.shape[1] != model.W1.shape[0]:
        raise ValueError("x_sequence must be (T, n_in)")
    h = np.tanh(X @ model.W1 + model.b1)
    y = model.forward(X)
    onset = []
    for u in range(h.shape[1]):
        hit = np.flatnonzero(np.abs(h[:, u]) >= threshold)
        onset.append(int(hit[0]) if len(hit) else None)
    order = sorted((u for u in range(len(onset)) if onset[u] is not None), key=lambda u: (onset[u], u))
    return {"steps": int(X.shape[0]), "hidden": h.tolist(), "output": y.tolist(),
            "onset_step": onset, "onset_order": order, "threshold": threshold}


def procrustes_alignment(A, B):
    """Orthogonal Procrustes alignment of two paired embeddings (same rows, same width).

    Finds the orthogonal R minimising ||A R - B||_F after column-centering both, and
    reports the error before and after rotation. Rows must correspond (paired samples);
    unpaired data gives no meaningful result. Fitted and scored on the same rows."""
    A = np.asarray(A, float); B = np.asarray(B, float)
    if A.shape != B.shape or A.ndim != 2:
        raise ValueError("A and B must be 2-D arrays of equal shape (paired rows)")
    Ac = A - A.mean(0); Bc = B - B.mean(0)
    u, _, vt = np.linalg.svd(Ac.T @ Bc)
    R = u @ vt
    before = float(np.linalg.norm(Ac - Bc) / max(np.linalg.norm(Bc), 1e-12))
    after = float(np.linalg.norm(Ac @ R - Bc) / max(np.linalg.norm(Bc), 1e-12))
    return {"rotation": R, "error_before": before, "error_after": after}


def align_paired_modalities(modalities, latent_dim=4):
    """PCA each modality to latent_dim, then Procrustes-align every later modality to the
    first on their paired rows. Requires equal row counts (row i is the same sample)."""
    if len(modalities) < 2:
        raise ValueError("at least two modalities required")
    zs = {}
    for name, X in modalities.items():
        X = np.asarray(X, float); c = X - X.mean(0)
        _, _, vt = np.linalg.svd(c, full_matrices=False)
        zs[name] = c @ vt[:min(latent_dim, vt.shape[0])].T
    if len({len(z) for z in zs.values()}) != 1:
        raise ValueError("paired alignment needs equal row counts")
    k = min(z.shape[1] for z in zs.values())
    names = list(zs); ref = names[0]; out = {}
    for n in names[1:]:
        r = procrustes_alignment(zs[n][:, :k], zs[ref][:, :k])
        out[f"{n}->{ref}"] = {"error_before": r["error_before"], "error_after": r["error_after"]}
    return {"alignments": out, "latent_dim": k, "pairing": "row i of every modality is the same sample"}


def predictive_coding_hierarchy(X, latent_dims=(4, 2), steps=30, infer_lr=0.1, learn_lr=0.01, epochs=60, seed=0):
    """Two-level linear predictive-coding network trained by prediction-error updates.

    Level 1 predicts the data from z1 (x_hat = z1 W1); level 2 predicts z1 from z2
    (z1_hat = z2 W2). For each sample the latents relax by gradient steps on the summed
    squared prediction errors; the generative weights then take a Hebbian-style step
    (error times latent). Returns the mean squared reconstruction error per epoch. It is
    a deterministic point-estimate model: there are no priors or posterior distributions."""
    X = np.asarray(X, float); X = X - X.mean(0)
    n, d = X.shape; d1, d2 = latent_dims
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, 0.3, (d1, d)); W2 = rng.normal(0, 0.3, (d2, d1))
    history = []
    for _ in range(epochs):
        z1 = np.zeros((n, d1)); z2 = np.zeros((n, d2))
        for _ in range(steps):
            e0 = X - z1 @ W1
            e1 = z1 - z2 @ W2
            z1 += infer_lr * (e0 @ W1.T - e1)
            z2 += infer_lr * (e1 @ W2.T)
        e0 = X - z1 @ W1; e1 = z1 - z2 @ W2
        W1 += learn_lr * z1.T @ e0 / n
        W2 += learn_lr * z2.T @ e1 / n
        history.append(float(np.mean(e0 ** 2)))
    return {"W1": W1, "W2": W2, "reconstruction_mse": history, "latent_dims": (d1, d2)}
