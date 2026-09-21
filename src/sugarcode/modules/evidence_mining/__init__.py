"""Live, cached evidence mining from PubMed and ClinicalTrials.gov."""
from .client import CachedHTTPClient, EvidenceAPIError, OfflineCacheMiss
from .extract import extract_text_evidence
from .core import EvidenceMiner
from .models import EvidenceRecord, MISSING
from .pubmed import PubMedClient
from .trials import ClinicalTrialsClient
from .table import build_evidence_table, deduplicate

__all__ = ["EvidenceMiner", "CachedHTTPClient", "EvidenceAPIError", "OfflineCacheMiss", "EvidenceRecord",
           "MISSING", "PubMedClient", "ClinicalTrialsClient", "extract_text_evidence",
           "build_evidence_table", "deduplicate"]
