import numpy as np
from sugarcode.modules.neuro_pipeline import core


def _spikes(T, pre_t, post_t):
    pre = np.zeros((T, 1)); post = np.zeros((T, 1))
    for t in pre_t: pre[t, 0] = 1
    for t in post_t: post[t, 0] = 1
    return pre, post


def test_stdp_pre_before_post_potentiates():
    pre, post = _spikes(20, [3], [6])
    d = core.stdp_timing_update(np.zeros((1, 1)), pre, post)["delta"][0, 0]
    assert d > 0


def test_stdp_post_before_pre_depresses():
    pre, post = _spikes(20, [6], [3])
    d = core.stdp_timing_update(np.zeros((1, 1)), pre, post)["delta"][0, 0]
    assert d < 0


def test_stdp_effect_decays_with_delay():
    near = core.stdp_timing_update(np.zeros((1, 1)), *_spikes(40, [3], [5]))["delta"][0, 0]
    far = core.stdp_timing_update(np.zeros((1, 1)), *_spikes(40, [3], [25]))["delta"][0, 0]
    assert near > far > 0
    assert core.stdp_timing_update(np.zeros((1, 1)), *_spikes(40, [3], [3]))["delta"][0, 0] == 0


def _two_tasks():
    rng = np.random.default_rng(0)
    XA = rng.normal(size=(300, 2)); yA = (XA[:, 0] > 0).astype(float)[:, None]
    XB = rng.normal(size=(300, 2)); yB = (XB[:, 1] > 0).astype(float)[:, None]
    return XA, yA, XB, yB


def _acc(m, X, y):
    return float(np.mean((m.forward(X) > .5) == y))


def _trained_on_a(XA, yA):
    m = core.MLP(2, 8, 1)
    for _ in range(500): m.backward(XA, yA, .8)
    return m


def test_fisher_diagonal_is_nonnegative_and_matches_finite_difference():
    XA, yA, _, _ = _two_tasks()
    m = _trained_on_a(XA[:50], yA[:50])
    F = core.fisher_diagonal(m, XA[:50])
    assert all((F[k] >= 0).all() for k in F) and F["W1"].shape == m.W1.shape
    # finite difference of logit for one W1 entry, compared with the analytic value
    X = XA[:50]; eps = 1e-6
    def logit(): return (np.tanh(X @ m.W1 + m.b1) @ m.W2 + m.b2)[:, 0]
    base = logit(); p = 1 / (1 + np.exp(-base)); m.W1[0, 0] += eps
    g = (logit() - base) / eps; m.W1[0, 0] -= eps
    assert np.isclose(np.mean(p * (1 - p) * g ** 2), F["W1"][0, 0], rtol=1e-3)


def test_fisher_anchor_retains_old_task_better_than_none_and_isotropic():
    XA, yA, XB, yB = _two_tasks()
    res = {}
    for name in ("none", "iso", "fisher"):
        m = _trained_on_a(XA, yA)
        F = core.fisher_diagonal(m, XA)
        if name == "none": core.continual_update(m, XB, yB, lr=.5, epochs=400, ewc_lambda=0)
        elif name == "iso": core.continual_update(m, XB, yB, lr=.5, epochs=400, ewc_lambda=10)
        else: core.continual_update_fisher(m, XB, yB, F, lr=.5, epochs=400, ewc_lambda=10)
        res[name] = _acc(m, XA, yA)
    assert res["none"] < 0.6
    assert res["fisher"] > 0.9
    assert res["fisher"] > res["iso"] + 0.1


def test_temporal_trace_orders_units_by_onset():
    m = core.MLP(2, 4, 1)
    m.W1 = np.array([[2., 0., 0., 0.], [0., 2., 0., 0.]]); m.b1 = np.zeros(4)
    seq = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 0.]])
    r = core.temporal_activation_trace(m, seq, threshold=0.5)
    assert r["steps"] == 4 and len(r["hidden"]) == 4
    assert r["onset_step"][:2] == [1, 2] and r["onset_step"][2:] == [None, None]
    assert r["onset_order"] == [0, 1]


def test_activation_trace_note_no_longer_claims_spike_trains():
    m = core.MLP(2, 3, 1)
    note = str(core.activation_trace(m, np.zeros((2, 2))).get("note", ""))
    assert "spike-train" not in note


def test_procrustes_recovers_rotation():
    rng = np.random.default_rng(1)
    A = rng.normal(size=(60, 3)); Q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    B = A @ Q + 0.01 * rng.normal(size=A.shape)
    r = core.procrustes_alignment(A, B)
    assert r["error_before"] > 0.5 and r["error_after"] < 0.05
    assert np.allclose(r["rotation"].T @ r["rotation"], np.eye(3), atol=1e-8)


def test_paired_modality_alignment_rejects_unpaired_sizes():
    rng = np.random.default_rng(2)
    try:
        core.align_paired_modalities({"a": rng.normal(size=(10, 5)), "b": rng.normal(size=(9, 5))})
    except ValueError:
        return
    raise AssertionError("unequal rows must raise")


def test_hierarchical_predictive_coding_learns():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(300, 2)) @ rng.normal(size=(2, 6)) + .05 * rng.normal(size=(300, 6))
    r = core.predictive_coding_hierarchy(X, (2, 1), epochs=100, learn_lr=.05)
    h = r["reconstruction_mse"]
    assert h[-1] < 0.1 * h[0]
    assert h[-1] < 0.1 * float(np.var(X - X.mean(0)))
