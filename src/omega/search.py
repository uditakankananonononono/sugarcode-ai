"""Unified search across the module registry and full spec corpus."""
from __future__ import annotations
import math
import re
from collections import Counter
from pathlib import Path
from .registry import REGISTRY

_SPEC_DIR = Path(__file__).resolve().parents[2] / "spec"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class UnifiedSearch:
    """BM25-ish ranking over module summaries + spec text."""

    def __init__(self, spec_dir: Path | None = None):
        self.spec_dir = spec_dir or _SPEC_DIR
        self.docs: dict[str, str] = {}
        for slug, spec in REGISTRY.items():
            body = f"{spec.name} {spec.summary}"
            spec_file = self.spec_dir / f"{slug}.md"
            if spec_file.exists():
                body += " " + spec_file.read_text(errors="replace")[:20000]
            self.docs[slug] = body
        self.tokens = {s: _tokenize(t) for s, t in self.docs.items()}
        df: Counter = Counter()
        for toks in self.tokens.values():
            for t in set(toks):
                df[t] += 1
        self.idf = {t: math.log(1 + (len(self.docs) - c + 0.5) / (c + 0.5))
                    for t, c in df.items()}

    def search(self, query: str, limit: int = 10) -> list[dict]:
        q = _tokenize(query)
        if not q:
            return []
        scored = []
        for slug, toks in self.tokens.items():
            tf = Counter(toks)
            score = sum(self.idf.get(t, 0.0) * tf.get(t, 0) for t in q)
            if score > 0:
                name = REGISTRY[slug].name.lower()
                if any(t in name for t in q):
                    score *= 1.5
                scored.append((score, slug))
        scored.sort(reverse=True)
        return [
            {"slug": s, "name": REGISTRY[s].name,
             "subnetwork": REGISTRY[s].subnetwork,
             "summary": REGISTRY[s].summary, "score": round(sc, 3)}
            for sc, s in scored[:limit]
        ]


def biological_search(query: str, limit: int = 10) -> dict:
    """High-fidelity biological search entry point (Neuro-Hub gateway)."""
    engine = UnifiedSearch()
    return {"query": query, "results": engine.search(query, limit),
            "modules_indexed": len(engine.docs)}
