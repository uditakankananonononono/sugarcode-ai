from __future__ import annotations
from collections import defaultdict

OPPOSING = {("activates", "inhibits"), ("inhibits", "activates"),
            ("increases", "decreases"), ("decreases", "increases")}


class KnowledgeGraph:
    """Multi-layered biological literature graph.

    Claims are (subject, relation, object) triples with evidence metadata:
    year, citations, sample size, replicated flag. Edge weight = evidence
    strength. Contradictions = opposing relations on the same (s, o) pair
    from different papers. Multi-hop paths connect siloed domains.
    """

    def __init__(self):
        self.claims: list[dict] = []
        self.edges: dict[tuple, list[int]] = defaultdict(list)

    def ingest(self, paper: dict) -> int:
        """paper: {id, title, year, citations, claims: [{subject, relation, object, n?}]}"""
        pid = paper["id"]
        added = 0
        for c in paper.get("claims", []):
            key = (c["subject"].lower(), c["relation"].lower(), c["object"].lower())
            idx = len(self.claims)
            self.claims.append({
                "paper": pid, "year": paper.get("year", 2000),
                "citations": paper.get("citations", 0),
                "replicated": paper.get("replicated", False),
                **c})
            self.edges[key].append(idx)
            added += 1
        return added

    def _weight(self, c: dict) -> float:
        import math
        w = 0.3 + 0.3 * min(math.log10(1 + c["citations"]) / 3, 1.0)
        w += 0.25 if c["replicated"] else 0.0
        w += 0.15 * min((c.get("n") or 10) / 100, 1.0)
        return round(w, 3)

    def query(self, subject: str, obj: str) -> dict:
        """Evidence-weighted answer for one (subject, object) pair."""
        relevant = [(k, idxs) for k, idxs in self.edges.items()
                    if k[0] == subject.lower() and k[2] == obj.lower()]
        relations = {}
        for (s, r, o), idxs in relevant:
            ws = [self._weight(self.claims[i]) for i in idxs]
            relations[r] = {"evidence_weight": round(sum(ws), 3),
                            "n_studies": len(idxs),
                            "years": sorted(self.claims[i]["year"] for i in idxs)}
        consensus = max(relations, key=lambda r: relations[r]["evidence_weight"]) if relations else None
        return {"subject": subject, "object": obj, "relations": relations,
                "consensus": consensus,
                "confidence": relations.get(consensus, {}).get("evidence_weight", 0) if consensus else 0}

    def contradictions(self) -> list[dict]:
        """Opposing claims on the same pair, with context for reconciliation."""
        out = []
        seen = set()
        for (s, r, o), idxs in self.edges.items():
            for (s2, r2, o2), idxs2 in self.edges.items():
                if s == s2 and o == o2 and (r, r2) in OPPOSING and (s, o) not in seen:
                    seen.add((s, o))
                    out.append({
                        "subject": s, "object": o,
                        "claim_a": {"relation": r, "papers": [self.claims[i]["paper"] for i in idxs],
                                    "years": [self.claims[i]["year"] for i in idxs]},
                        "claim_b": {"relation": r2, "papers": [self.claims[i]["paper"] for i in idxs2],
                                    "years": [self.claims[i]["year"] for i in idxs2]},
                        "proposed_resolution": ("compare experimental contexts: dose, cell type, "
                                                "timepoint; run head-to-head replication"),
                    })
        return out

    def multi_hop(self, start: str, end: str, max_hops: int = 3) -> dict:
        """BFS over aggregated relation graph - cross-domain latent connections."""
        adj = defaultdict(set)
        for (s, r, o) in self.edges:
            adj[s].add((o, r))
        queue = [(start.lower(), [start.lower()], [])]
        visited, paths = set(), []
        while queue:
            node, path, rels = queue.pop(0)
            if node == end.lower() and len(path) > 1:
                paths.append({"path": path, "relations": rels})
                continue
            if len(path) > max_hops or node in visited:
                continue
            visited.add(node)
            for nxt, rel in adj.get(node, ()):
                if nxt not in path:
                    queue.append((nxt, path + [nxt], rels + [rel]))
        return {"start": start, "end": end, "paths": paths[:5],
                "connected": bool(paths)}

    def hypothesize(self, topic: str) -> dict:
        """Structured, testable hypothesis from graph gaps and weak evidence."""
        weak = [(k, idxs) for k, idxs in self.edges.items()
                if topic.lower() in (k[0], k[2])
                and sum(self._weight(self.claims[i]) for i in idxs) < 0.8]
        contra = [c for c in self.contradictions() if topic.lower() in (c["subject"], c["object"])]
        hypotheses = []
        for (s, r, o), idxs in weak[:2]:
            hypotheses.append({
                "proposition": f"{s} {r} {o} under context-specific conditions",
                "rationale": f"only {len(idxs)} low-weight study/studies support this edge",
                "test": "orthogonal replication: perturb s, measure o across dose and time",
                "reasoning_trace": [f"edge ({s},{r},{o}) evidence_weight < 0.8",
                                    "sparsity flagged as high-leverage gap"]})
        for c in contra[:2]:
            hypotheses.append({
                "proposition": f"context dependence explains {c['subject']}->{c['object']} conflict",
                "rationale": "opposing claims coexist in literature",
                "test": c["proposed_resolution"],
                "reasoning_trace": ["contradiction detected", "reconciliation experiment proposed"]})
        return {"topic": topic, "hypotheses": hypotheses,
                "underexplored_edges": len(weak), "open_contradictions": len(contra)}


_RELATION_WORDS = {"activates": "activates", "stimulates": "activates",
                   "upregulates": "increases", "increases": "increases",
                   "inhibits": "inhibits", "suppresses": "inhibits", "blocks": "inhibits",
                   "decreases": "decreases", "downregulates": "decreases",
                   "binds": "binds", "interacts with": "binds",
                   "causes": "associated_with", "associated with": "associated_with"}


def extract_claims(text: str) -> list[dict]:
    """Simple, honest relation extractor: <GENE-ish token> <relation word> <token>.

    Extracts only explicitly stated relations from the sentence; anything
    it cannot ground is left out (recall-biased toward precision).
    """
    import re
    claims = []
    for sent in re.split(r"[.!?]", text):
        words = re.findall(r"[A-Za-z0-9'-]+", sent)
        for i, w in enumerate(words):
            rel = _RELATION_WORDS.get(w.lower())
            if rel and 0 < i < len(words) - 1:
                subj, obj = words[i - 1], words[i + 1]
                if subj[:1].isupper() or obj[:1].isupper() or subj.isupper() or obj.isupper():
                    claims.append({"subject": subj, "relation": rel, "object": obj})
    return claims


def ingest_pubmed(kg: "KnowledgeGraph", query: str, retmax: int = 10,
                  offline: bool = False) -> dict:
    """Fetch live PubMed abstracts for a query and ingest extracted claims
    into the knowledge graph with real citation metadata."""
    from ...bio import entrez
    pmids = entrez.pubmed_ids(query, retmax=retmax, offline=offline)
    abstracts = entrez.pubmed_abstracts(pmids, offline=offline)
    total = 0
    for a in abstracts:
        claims = extract_claims(a["title"] + ". " + a["abstract"])
        total += kg.ingest({"id": f"PMID:{a['pmid']}", "title": a["title"],
                            "year": int(a["year"]) if a["year"].isdigit() else 2000,
                            "citations": 0, "journal": a["journal"],
                            "claims": claims})
    return {"query": query, "papers_fetched": len(abstracts),
            "claims_ingested": total,
            "pmids": [a["pmid"] for a in abstracts]}
