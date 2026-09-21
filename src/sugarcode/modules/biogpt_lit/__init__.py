"""BioGPT Lit: temporal evidence-weighted knowledge graph + contradiction detection."""
from .core import KnowledgeGraph, extract_claims, ingest_pubmed
__all__ = ["KnowledgeGraph", "extract_claims", "ingest_pubmed"]
