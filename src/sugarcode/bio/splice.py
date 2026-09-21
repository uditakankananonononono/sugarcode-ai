"""Real human splice-site PWMs learned from RefSeqGene records.

Data: 1,215 GT-AG splice junctions extracted live from NCBI RefSeqGene
records for 28 clinically relevant genes (see data/splice_sites/PROVENANCE.md).
Donor window: 9 nt (3 exonic + 6 intronic). Acceptor window: 15 nt
(14 intronic + 1 exonic). Learned consensus: AAG|GTAAGT and (T)nCAG|G,
matching the published mammalian consensus.
"""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

from .pwm import log_odds_matrix

DATA = Path(__file__).parent / "data" / "splice_sites"


class SpliceDataMissing(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load(name: str) -> list[dict[str, float]]:
    p = DATA / name
    if not p.exists():
        raise SpliceDataMissing(f"missing vendored splice data: {p}")
    payload = json.loads(p.read_text())
    return payload["pwm"]


def donor_pwm() -> list[dict[str, float]]:
    return _load("donor_pwm.json")


def acceptor_pwm() -> list[dict[str, float]]:
    return _load("acceptor_pwm.json")


def donor_lod() -> list[dict[str, float]]:
    return log_odds_matrix(donor_pwm())


def acceptor_lod() -> list[dict[str, float]]:
    return log_odds_matrix(acceptor_pwm())


def n_sites() -> dict[str, int]:
    return {"donor": json.loads((DATA / "donor_pwm.json").read_text())["n_sites"],
            "acceptor": json.loads((DATA / "acceptor_pwm.json").read_text())["n_sites"]}
