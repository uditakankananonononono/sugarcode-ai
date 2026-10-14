"""Model Updating - exact Bayesian revision of belief in rival hypotheses after observations.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
hypotheses, a dict of 2..6 hypotheses (names 1..12 characters a-z and _), each a dict with
exactly prior (a [num, den] pair) and likelihood (a dict mapping every symbol to a
[num, den] pair); observations, a list of 1..10 symbols. Fractions need num >= 0,
den 1..100, value <= 1. The priors must sum to 1 and every hypothesis's likelihoods must
sum to 1 over the same 1..6 symbols (names a-z and _, 1..12 characters).

Rule: after each observation every hypothesis weight is multiplied by its likelihood of
that symbol and the weights are renormalised. If the weights all become 0 the evidence was
impossible under every hypothesis and the call is refused. The result gives the posterior
(Fraction strings) after each observation, the final posterior, and the hypothesis with
the highest final posterior (ties to the alphabetically first).

Scope: PARTIAL for the Model Updating line. Exact Bayes' rule over a small discrete model
the caller wrote, with independent observations. It learns no model and checks none.

Not claimed: that the priors or likelihoods are right, that observations are independent
in reality, that the top hypothesis is true, or anything about the real world. Every claim
flag in the result is False.
"""
import re
from fractions import Fraction

_NAME = re.compile(r"[a-z_]{1,12}\Z")
_H = frozenset({"prior", "likelihood"})
_TOP = frozenset({"hypotheses", "observations"})

NOT_CLAIMED = (
    "the priors or likelihoods are right",
    "observations are independent in reality",
    "the top hypothesis is true",
    "real-world outcome",
)
CLAIMS = {"inputs_right": False, "independent_in_reality": False, "top_is_true": False, "real_world": False}


class UpdateError(ValueError):
    pass


def _frac(p, name):
    if not isinstance(p, list) or len(p) != 2:
        raise UpdateError(f"{name} must be a [num, den] pair")
    n, d = p
    for v in (n, d):
        if type(v) is not int:
            raise UpdateError(f"{name} must be a [num, den] pair of ints")
    if d < 1 or d > 100 or n < 0 or n > d:
        raise UpdateError(f"{name} out of range")
    return Fraction(n, d)


def _name(v, what):
    if not type(v) is str or not _NAME.match(v):
        raise UpdateError(f"{what} must be 1..12 characters from a-z and _")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise UpdateError("data keys must be exactly hypotheses, observations")
    hs = data["hypotheses"]
    if not isinstance(hs, dict) or not 2 <= len(hs) <= 6:
        raise UpdateError("hypotheses must be a dict of 2..6 hypotheses")
    prior, like, symbols = {}, {}, None
    for h, body in hs.items():
        _name(h, "hypothesis name")
        if not isinstance(body, dict) or set(body) != _H:
            raise UpdateError("hypothesis keys must be exactly likelihood, prior")
        prior[h] = _frac(body["prior"], "prior")
        lk = body["likelihood"]
        if not isinstance(lk, dict) or not 1 <= len(lk) <= 6:
            raise UpdateError("likelihood must be a dict of 1..6 symbols")
        for s in lk:
            _name(s, "symbol")
        if symbols is None:
            symbols = set(lk)
        elif set(lk) != symbols:
            raise UpdateError("every hypothesis must give likelihoods for the same symbols")
        like[h] = {s: _frac(v, "likelihood") for s, v in lk.items()}
        if sum(like[h].values()) != 1:
            raise UpdateError("likelihoods must sum to 1")
    if sum(prior.values()) != 1:
        raise UpdateError("priors must sum to 1")
    ob = data["observations"]
    if not isinstance(ob, list) or not 1 <= len(ob) <= 10:
        raise UpdateError("observations must be a list of 1..10 symbols")
    for o in ob:
        if not type(o) is str or o not in symbols:
            raise UpdateError("observation must be a known symbol")
    return prior, like, list(ob)


def bayes_update(data):
    prior, like, obs = _validate(data)
    names = sorted(prior)
    cur = dict(prior)
    history = []
    for o in obs:
        w = {h: cur[h] * like[h][o] for h in names}
        tot = sum(w.values())
        if tot == 0:
            raise UpdateError("evidence has probability zero under every hypothesis")
        cur = {h: w[h] / tot for h in names}
        history.append({h: str(cur[h]) for h in names})
    top = names[0]
    for h in names[1:]:
        if cur[h] > cur[top]:
            top = h
    return {
        "status": "completed",
        "history": history,
        "posterior": history[-1],
        "top": top,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
