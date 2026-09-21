from __future__ import annotations
import numpy as np
from ...bio.sequence import clean_dna, gc_content
from ..crispr_opt.core import score_on_target, score_off_targets, PAMS


class MuseAgent:
    """Policy-gradient-flavored guide designer.

    Policy: per-position nucleotide logits (20 x 4). Reward = composite of
    on-target model, GC window fit, off-target penalty and (simulated)
    experimental edit-efficiency feedback. Updates shift logits toward
    sampled guides that scored above the running baseline.
    """

    def __init__(self, seed: int = 0):
        self.rng = np.random.default_rng(seed)
        self.logits = np.zeros((20, 4))
        self.baseline = 0.5
        self.rounds = 0
        self.history: list[dict] = []

    BASES = "ACGT"

    def sample_guides(self, n: int = 32) -> list[str]:
        probs = _softmax(self.logits, axis=1)
        guides = []
        for _ in range(n):
            g = "".join(self.BASES[int(self.rng.choice(4, p=probs[i]))] for i in range(20))
            guides.append(g)
        return guides

    def reward(self, guide: str, pam: str = "NGG", background: str | None = None,
               observed_efficiency: float | None = None) -> float:
        on = score_on_target(guide)
        gc = gc_content(guide)
        gc_fit = 1.0 - min(abs(gc - 0.5) / 0.5, 1.0)
        off = 0.0
        if background:
            hits = score_off_targets(guide, background, max_mismatches=3)
            off = sum(h["risk"] for h in hits if h["mismatches"] > 0)
        r = 0.55 * on + 0.25 * gc_fit - 0.20 * min(off, 2.0)
        if observed_efficiency is not None:
            r = 0.6 * r + 0.4 * observed_efficiency  # lab feedback dominates
        return float(r)

    def update(self, samples: list[tuple[str, float]], lr: float = 0.4) -> dict:
        rewards = np.array([r for _, r in samples])
        adv = rewards - self.baseline
        for (g, _), a in zip(samples, adv):
            for i, b in enumerate(g):
                self.logits[i, self.BASES.index(b)] += lr * a
        self.logits -= self.logits.mean(axis=1, keepdims=True)  # recenter
        self.baseline = 0.9 * self.baseline + 0.1 * float(rewards.mean())
        self.rounds += 1
        summary = {"round": self.rounds, "mean_reward": round(float(rewards.mean()), 4),
                   "best_reward": round(float(rewards.max()), 4),
                   "baseline": round(self.baseline, 4)}
        self.history.append(summary)
        return summary

    def best_guide(self) -> str:
        probs = _softmax(self.logits, axis=1)
        return "".join(self.BASES[int(np.argmax(probs[i]))] for i in range(20))


def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def train_round(agent: MuseAgent, background: str | None = None,
                n_samples: int = 32, simulated_lab: bool = True) -> dict:
    """One design->simulate->feedback round.

    With simulated_lab on, a noisy 'NGS edit efficiency' observation is
    synthesized from the on-target model to emulate experimental feedback.
    """
    guides = agent.sample_guides(n_samples)
    samples = []
    for g in guides:
        obs = None
        if simulated_lab:
            obs = float(np.clip(score_on_target(g) + agent.rng.normal(0, 0.08), 0, 1))
        samples.append((g, agent.reward(g, background=background, observed_efficiency=obs)))
    summary = agent.update(samples)
    summary["current_best_guide"] = agent.best_guide()
    summary["best_guide_on_target"] = round(score_on_target(agent.best_guide()), 3)
    summary["pam_compatibility"] = {k: v for k, v in PAMS.items()}
    return summary
