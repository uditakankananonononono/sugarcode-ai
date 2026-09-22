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

# Structured evidence reasoning; no trained transformer/GNN is bundled and
# outputs are not clinical guidance.
import math,json
import numpy as np

def evidence_quality(paper,claim=None):
    claim=claim or {}; n=float(claim.get('n',paper.get('sample_size',10))); replicated=bool(paper.get('replicated',False)); citations=float(paper.get('citations',0)); rigor=float(paper.get('rigor',.5)); prereg=float(paper.get('preregistered',False)); reproducibility=.35*replicated+.2*prereg+.25*min(1,math.log10(1+citations)/3)+.2*min(1,n/100); strength=.55*rigor+.45*reproducibility; return {"sample_size":n,"rigor":rigor,"reproducibility":reproducibility,"strength":strength,"preliminary":strength<.45}

def parse_full_text(document):
    text=' '.join(str(document.get(k,'')) for k in ('title','abstract','full_text','methods')); claims=extract_claims(text); entities=sorted({c[k] for c in claims for k in ('subject','object')}); methods={"has_randomization":"random" in text.lower(),"has_blinding":"blind" in text.lower(),"has_replication":"replicat" in text.lower(),"sample_size_mentions":text.lower().count('n=')}; return {"claims":claims,"entities":entities,"methods":methods,"supplement_count":len(document.get('supplements',[])),"figure_count":len(document.get('figures',[]))}

def temporal_consensus(kg,subject,obj):
    relevant=[c for c in kg.claims if c['subject'].lower()==subject.lower() and c['object'].lower()==obj.lower()]; years=sorted({c['year'] for c in relevant}); trajectory=[]
    for year in years:
        subset=[c for c in relevant if c['year']<=year]; weights=defaultdict(float)
        for c in subset: weights[c['relation']]+=kg._weight(c)
        total=sum(weights.values()); trajectory.append({"year":year,"relations":dict(weights),"consensus":max(weights,key=weights.get),"agreement":max(weights.values())/total if total else 0})
    return {"subject":subject,"object":obj,"trajectory":trajectory,"status":"emerging" if trajectory and trajectory[-1]['agreement']<.7 else "consolidated" if trajectory else "unknown"}

def contradiction_context(kg,subject,obj):
    claims=[c for c in kg.claims if c['subject'].lower()==subject.lower() and c['object'].lower()==obj.lower()]; grouped=defaultdict(list)
    for c in claims: grouped[c['relation']].append(c)
    conflicts=[]
    for a,b in OPPOSING:
        if a in grouped and b in grouped:
            contexts={r:{"papers":[x['paper'] for x in grouped[r]],"years":[x['year'] for x in grouped[r]],"sample_sizes":[x.get('n') for x in grouped[r]],"conditions":[x.get('condition','unspecified') for x in grouped[r]]} for r in (a,b)}; conflicts.append({"relations":[a,b],"contexts":contexts,"resolution_experiment":"matched cell type, dose and time-course perturbation with blinded outcome assessment"})
    return {"conflicts":conflicts,"count":len(conflicts)}

def evidence_paths(kg,start,end,max_hops=4):
    base=kg.multi_hop(start,end,max_hops); paths=[]
    for p in base['paths']:
        support=[]
        for a,r,b in zip(p['path'],p['relations'],p['path'][1:]):
            idx=kg.edges.get((a,r,b),[]); support.append({"edge":[a,r,b],"papers":[kg.claims[i]['paper'] for i in idx],"evidence_weight":sum(kg._weight(kg.claims[i]) for i in idx)})
        paths.append({**p,"support":support,"path_strength":min((x['evidence_weight'] for x in support),default=0)})
    return {**base,"paths":sorted(paths,key=lambda x:-x['path_strength'])}

def meta_analysis(effects,standard_errors):
    e=np.asarray(effects,float); se=np.asarray(standard_errors,float)
    if e.shape!=se.shape or not e.size or np.any(se<=0): raise ValueError("effects/SE invalid")
    w=1/se**2; mean=float(w@e/w.sum()); q=float(np.sum(w*(e-mean)**2)); tau=max(0,(q-(len(e)-1))/(w.sum()-np.sum(w*w)/w.sum())) if len(e)>1 else 0; rw=1/(se**2+tau); pooled=float(rw@e/rw.sum()); std=math.sqrt(1/rw.sum()); return {"fixed_effect":mean,"random_effect":pooled,"tau_squared":tau,"heterogeneity_q":q,"ci95":[pooled-1.96*std,pooled+1.96*std],"study_count":len(e)}

def prioritize_gaps(kg):
    gaps=[]
    for edge,idx in kg.edges.items():
        weight=sum(kg._weight(kg.claims[i]) for i in idx); disagreement=1 if any(edge[0]==x[0] and edge[2]==x[2] and (edge[1],x[1]) in OPPOSING for x in kg.edges) else 0; leverage=(1/(1+weight))*(1+disagreement)*(1+math.log1p(len(idx))); gaps.append({"edge":edge,"evidence_weight":weight,"contradiction":bool(disagreement),"information_leverage":leverage})
    return sorted(gaps,key=lambda x:-x['information_leverage'])

def structured_hypothesis(kg,topic):
    base=kg.hypothesize(topic); gaps=prioritize_gaps(kg); hypotheses=[]
    for h in base['hypotheses']:
        hypotheses.append({**h,"predicted_outcomes":["directional molecular response","context-dependent effect size"],"controls":["matched negative control","orthogonal perturbation"],"readouts":["target abundance","pathway activity"],"status":"non-procedural experimental rationale"})
    return {**base,"hypotheses":hypotheses,"highest_leverage_gaps":gaps[:5]}

def update_validation(kg,subject,relation,obj,confirmed,n=50):
    before=kg.query(subject,obj); kg.ingest({"id":f"feedback:{len(kg.claims)+1}","year":2026,"citations":0,"replicated":confirmed,"rigor":.9,"claims":[{"subject":subject,"relation":relation if confirmed else {'activates':'inhibits','inhibits':'activates','increases':'decreases','decreases':'increases'}.get(relation,relation),"object":obj,"n":n,"condition":"validation feedback"}]}); return {"before":before,"after":kg.query(subject,obj),"confirmed":confirmed}

def graph_diagnostics(kg):
    papers={c['paper'] for c in kg.claims}; entities={c[k].lower() for c in kg.claims for k in ('subject','object')}; weights=np.array([kg._weight(c) for c in kg.claims],float) if kg.claims else np.array([0.]); years=np.array([c['year'] for c in kg.claims],float) if kg.claims else np.array([0.]); return {"claim_count":float(len(kg.claims)),"paper_count":float(len(papers)),"entity_count":float(len(entities)),"edge_count":float(len(kg.edges)),"contradiction_count":float(len(kg.contradictions())),"evidence_mean":float(weights.mean()),"evidence_std":float(weights.std()),"evidence_min":float(weights.min()),"evidence_max":float(weights.max()),"year_min":float(years.min()),"year_max":float(years.max()),"year_span":float(years.max()-years.min()),"replicated_fraction":sum(c['replicated'] for c in kg.claims)/max(1,len(kg.claims)),"preliminary_fraction":sum(evidence_quality(c,c)['preliminary'] for c in kg.claims)/max(1,len(kg.claims))}

def literature_reasoning_report(kg,topic,start=None,end=None):
    return {"topic":topic,"hypotheses":structured_hypothesis(kg,topic),"contradictions":[c for c in kg.contradictions() if topic.lower() in (c['subject'],c['object'])],"evidence_paths":evidence_paths(kg,start,end) if start and end else None,"diagnostics":graph_diagnostics(kg),"model_status":"Structured evidence/statistical reasoning; no trained transformer/GNN and not clinical guidance.","audit_note":"Every path preserves paper IDs and edge weights; generated hypotheses are labeled and non-procedural."}
