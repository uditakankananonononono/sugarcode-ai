"""Shim: the parser lives in sugarcode.bio.genbank (drop 25); scripts import it."""
import sys
sys.path.insert(0, "src")
from sugarcode.bio.genbank import parse_genbank, revcomp, transcript_exons  # noqa: F401
