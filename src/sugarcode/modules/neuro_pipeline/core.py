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

    Kept for backward compatibility and quick smoke tests. For biological
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
                            "with an EWC anchor penalty, use continual_update()."),
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
    """Time-resolved forward trace for one input (information propagation)."""
    model.forward(x, record=True)
    h, y = model.trace
    return {
        "input_norm": round(float(np.linalg.norm(x)), 3),
        "hidden_mean_abs": round(float(np.mean(np.abs(h))), 3),
        "hidden_active_fraction": round(float(np.mean(np.abs(h) > 0.5)), 3),
        "output": [round(float(v), 3) for v in np.atleast_1d(y).ravel()],
        "note": "per-layer activation magnitudes - spike-train analogue of inference",
    }


def rsa(model: MLP, n_in: int | None = None, n_stimuli: int = 40, seed: int = 7,
        X: np.ndarray | None = None) -> dict:
    """Representational similarity analysis: correlate input-space and hidden-space
    dissimilarity matrices (are model embeddings organized like the data?).

    n_in defaults to the model's input width (a fixed 6 crashed on every
    sequence-trained model); pass X to use real stimuli (e.g. encoded DNA)."""
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
    synthetic-but-biological data (real DNA alphabet, real motif grammar),
    not Gaussian blobs. Returns {sequences, labels, motif, seq_len}."""
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
    own sequences + labels (0/1) for real biological data. encoding is
    'onehot' (default, position-specific) or 'kmer' (4**k frequency features).

    A stratified `holdout` fraction (default 0.2) is kept out of training and
    scored separately: training accuracy alone hid severe overfitting (default
    one-hot run: train 0.965 vs 0.64 on fresh sequences). Set holdout=0 to
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
                            "use continual_update() for EWC."),
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
    run=train(epochs=80,seed=seed); model=run['model']; lesion=lesion_study(model); connectivity=functional_connectivity(model); x=np.eye(6); causal=causal_intervention(model,x,0); return {'training':{k:v for k,v in run.items() if k!='model'},'connectivity':connectivity,'lesion':lesion,'causal':causal,'rsa':rsa(model),'feedback':feedback_reward_update(1,1,[1,0,1]),'model_status':'A real small NumPy MLP and explicit algorithms; no biological foundation model or autonomous lab agent is bundled.'}

def neuro_diagnostics(seed=42):
    r=pipeline_report(seed); t=r['training']; l=r['lesion']; c=r['connectivity']; ca=r['causal']; return {'final_loss':t['final_loss'],'train_accuracy':t['train_accuracy'],'stdp_modulation':t['stdp_modulation'],'connectivity_edges':float(len(c['edges'])),'connectivity_density':c['density'],'lesion_baseline_accuracy':l['baseline_accuracy'],'critical_unit_count':float(len(l['critical_units'])),'max_lesion_drop':max((x['accuracy_drop'] for x in l['lesions']),default=0),'rsa_correlation':r['rsa']['rsa_correlation'],'causal_effect_abs':float(np.mean(np.abs(ca['average_causal_effect']))),'reward_mean':r['feedback']['reward_mean'],'reward_uncertainty':r['feedback']['uncertainty']}
