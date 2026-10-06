import numpy as np
import pytest
from sugarcode.modules.crispr_muse import MuseAgent, train_round


def test_no_fake_lab_feedback_by_default():
    a = MuseAgent(seed=1)
    s = train_round(a, n_samples=16)
    assert s["measured_feedback_samples"] == 0
    assert "no experimental feedback" in s["feedback_source"]
    assert s["lab_validated"] is False


def test_synthetic_noise_is_labeled_and_validated():
    s = train_round(MuseAgent(seed=1), n_samples=8, synthetic_noise=0.1)
    assert "NOT lab data" in s["feedback_source"]
    with pytest.raises(ValueError):
        train_round(MuseAgent(seed=1), synthetic_noise=-1)


def test_measured_feedback_moves_the_policy():
    """A guide measured as ~0 efficiency must lose probability vs measured ~1 (fails on a fake loop)."""
    a = MuseAgent(seed=5); b = MuseAgent(seed=5)
    for _ in range(25):
        for agent, eff in ((a, 1.0), (b, 0.0)):
            gs = agent.sample_guides(32)
            samples = [(g, agent.reward(g, observed_efficiency=eff if g[0] == "G" else 1 - eff)) for g in gs]
            agent.update(samples)
    pa = np.exp(a.logits[0]) / np.exp(a.logits[0]).sum(); pb = np.exp(b.logits[0]) / np.exp(b.logits[0]).sum()
    assert pa[2] > pb[2]  # G index
