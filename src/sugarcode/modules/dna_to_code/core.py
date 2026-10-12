from __future__ import annotations

CONCEPTS: dict[str, dict] = {
    "transcription": {
        "analogy": "Reading a read-only source file into a working buffer.",
        "code": (
            "def transcribe(dna_template: str) -> str:\n"
            "    # RNA polymerase = a streaming reader with a writable handle\n"
            "    # it walks the template 3'->5' and writes the complement 5'->3'\n"
            "    pair = {'A': 'U', 'T': 'A', 'G': 'C', 'C': 'G'}\n"
            "    with open_readonly(dna_template) as src:   # template given 5'->3'\n"
            "        mrna = ''.join(pair[b] for b in reversed(src.read()))\n"
            "    return mrna  # = coding strand with T->U\n"
        ),
        "detail": "The template strand is read 3'->5'; the product is a disposable copy (mRNA) that leaves the nucleus while the master copy (DNA) stays protected.",
    },
    "translation": {
        "analogy": "A parser that reads 3-byte tokens and emits typed objects.",
        "code": (
            "def translate(mrna: str) -> list:\n"
            "    protein = []\n"
            "    for codon in chunks(mrna, 3):          # tokenizer: 3 nt per token\n"
            "        aa = CODON_TABLE[codon]           # lookup table = tRNA pool\n"
            "        if aa == 'STOP':                  # null terminator\n"
            "            break\n"
            "        protein.append(aa)\n"
            "    return protein\n"
        ),
        "detail": "The ribosome is an interpreter; tRNAs are the symbol resolver mapping codons to amino-acid values.",
    },
    "pcr": {
        "analogy": "Exponential retry-with-duplication loop bounded by resource pool.",
        "code": (
            "def pcr(template: str, primers: tuple, cycles: int = 30) -> list:\n"
            "    pool = [template]\n"
            "    for _ in range(cycles):\n"
            "        batch = []\n"
            "        for strand in pool:\n"
            "            if flanked_by(strand, primers):\n"
            "                batch.extend([strand, copy(strand)])  # 2x per cycle\n"
            "        pool = batch or pool\n"
            "    return pool  # 2^n amplification\n"
        ),
        "detail": "Denature/anneal/extend = fork, attach handles, replicate; each cycle doubles product until reagents exhaust (the plateau phase).",
    },
    "crispr": {
        "analogy": "Address-guided patch: regex search + targeted rewrite with checksum.",
        "code": (
            "def crispr_edit(genome: str, guide: str, payload: str) -> str:\n"
            "    match = search_with_pam(genome, guide)   # gRNA = address\n"
            "    if not match:\n"
            "        raise OffTargetRisk('no confident locus')\n"
            "    cut = match.cut_site                     # Cas9 = patch tool\n"
            "    return genome[:cut] + payload + genome[cut:]\n"
        ),
        "detail": "The guide RNA supplies the address; Cas9 performs the cut; HDR is the merge strategy that applies the patch from a template.",
    },
    "gene_regulation": {
        "analogy": "Feature flags and circuit breakers over expression services.",
        "code": (
            "class Promoter:\n"
            "    def __init__(self):\n"
            "        self.repressors = []   # circuit breakers\n"
            "        self.activators = []   # load balancers raising throughput\n"
            "    def expression_rate(self) -> float:\n"
            "        if any(r.bound for r in self.repressors):\n"
            "            return 0.0        # circuit open: transcription halted\n"
            "        return 1.0 + sum(a.gain for a in self.activators)\n"
        ),
        "detail": "Promoters are gateways; repressors trip the circuit, activators raise the rate limit. Hill kinetics = soft degradation instead of hard cutoffs.",
    },
    "mutation": {
        "analogy": "A single-character diff whose blast radius depends on the call graph.",
        "code": (
            "def point_mutation(gene: str, pos: int, base: str) -> dict:\n"
            "    before = compile_protein(gene)\n"
            "    mutant = gene[:pos] + base + gene[pos+1:]\n"
            "    after = compile_protein(mutant)\n"
            "    return {'silent': before == after,     # same behavior\n"
            "            'missense': len(before) == len(after) and before != after,\n"
            "            'nonsense': len(after) < len(before)}  # early crash\n"
        ),
        "detail": "Silent = refactor with no behavior change; missense = changed return value; nonsense = unhandled early exit (truncated protein).",
    },
}



# Returned snippets are self-contained string algorithms. Helpers operate only
# on supplied strings; none opens a file, calls a service or models a lab result.
_SNIPPET_SCOPE = "Executable educational string analogy only; no biological prediction or experiment."
_SNIPPET_COMMON = r"""
def _sequence(value, alphabet, limit=10000):
    if not isinstance(value, str) or not value or len(value) > limit:
        raise ValueError("a nonempty bounded sequence string is required")
    value = value.upper()
    if set(value) - set(alphabet):
        raise ValueError("unsupported sequence characters")
    return value
"""

_SNIPPET_HELPERS = {
    "transcription": r"""
from io import StringIO

def open_readonly(sequence):
    # In-memory sequence buffer, not a filesystem operation.
    return StringIO(_sequence(sequence, "ACGT"))
""",
    "translation": r"""
def chunks(sequence, width):
    sequence = _sequence(sequence, "ACGU")
    if type(width) is not int or width != 3 or len(sequence) % width:
        raise ValueError("complete three-base RNA codons are required")
    return [sequence[i:i+width] for i in range(0, len(sequence), width)]
""",
    "pcr": r"""
def flanked_by(sequence, primers):
    sequence = _sequence(sequence, "ACGT", 1000)
    if not isinstance(primers, tuple) or len(primers) != 2:
        raise ValueError("two literal boundary strings are required")
    left, right = (_sequence(p, "ACGT", 1000) for p in primers)
    return sequence.startswith(left) and sequence.endswith(right)

def copy(sequence):
    return str(sequence)
""",
    "crispr": r"""
from types import SimpleNamespace

class OffTargetRisk(ValueError):
    # Compatibility name for an ambiguous string address, not a risk model.
    pass

def search_with_pam(sequence, guide):
    sequence = _sequence(sequence, "ACGT")
    guide = _sequence(guide, "ACGT", 20)
    if len(guide) != 20:
        raise ValueError("a 20-character string address is required")
    hits = [i for i in range(len(sequence) - 22)
            if sequence[i:i+20] == guide and sequence[i+21:i+23] == "GG"]
    if len(hits) > 1:
        raise OffTargetRisk("ambiguous exact string address")
    return SimpleNamespace(cut_site=hits[0]+17) if hits else None
""",
    "mutation": r"""
def compile_protein(sequence):
    sequence = _sequence(sequence, "ACGT")
    if len(sequence) % 3:
        raise ValueError("complete coding-frame codons are required")
    protein = []
    for i in range(0, len(sequence), 3):
        aa = CODON_TABLE[sequence[i:i+3].replace("T", "U")]
        if aa == "STOP":
            break
        protein.append(aa)
    return "".join(protein)
""",
}


def _executable_source(key):
    from ...bio.sequence import STANDARD_CODE
    helper = _SNIPPET_HELPERS.get(key, "")
    table = ""
    if key in {"translation", "mutation"}:
        mapping = {k.replace("T", "U"): ("STOP" if v == "*" else v)
                   for k, v in STANDARD_CODE.items()}
        table = "CODON_TABLE = " + repr(mapping) + "\n"
    code = CONCEPTS[key]["code"]
    if key == "pcr":
        code = code.replace("cycles: int = 30", "cycles: int = 4")
        code = code.replace("    pool = [template]", "    if type(cycles) is not int or not 0 <= cycles <= 10:\n        raise ValueError('cycles must be integer 0..10')\n    template = _sequence(template, 'ACGT', 1000)\n    flanked_by(template, primers)  # validate even when cycles=0\n    pool = [template]")
    elif key == "crispr":
        code = code.replace("    match = search_with_pam", "    genome = _sequence(genome, 'ACGT')\n    payload = _sequence(payload, 'ACGT', 1000)\n    match = search_with_pam")
    elif key == "mutation":
        code = code.replace("    before = compile_protein(gene)", "    gene = _sequence(gene, 'ACGT')\n    if type(pos) is not int or not 0 <= pos < len(gene):\n        raise ValueError('position outside sequence')\n    base = _sequence(base, 'ACGT', 1)\n    before = compile_protein(gene)")
    return "# " + _SNIPPET_SCOPE + "\n" + _SNIPPET_COMMON + table + helper + "\n" + code


# Keep the public CONCEPTS source blocks consistent with translate_concept.
for _concept_key in CONCEPTS:
    CONCEPTS[_concept_key]["code"] = _executable_source(_concept_key)
    CONCEPTS[_concept_key]["scope"] = _SNIPPET_SCOPE

def translate_concept(concept: str) -> dict:
    key = concept.lower().replace(" ", "_").replace("-", "_")
    if key not in CONCEPTS:
        raise KeyError(f"unknown concept {concept!r}; have {sorted(CONCEPTS)}")
    c = CONCEPTS[key]
    return {"concept": key, "analogy": c["analogy"], "python": c["code"], "scope": c["scope"],
            "explanation": c["detail"]}

def execute_transcription(dna):
 s=''.join(x for x in dna.upper() if x in 'ACGT'); return s.replace('T','U')
def execute_translation(rna):
 from ...bio.sequence import translate
 return translate(rna.replace('U','T'),to_stop=True)
def execute_mutation(dna,pos,base):
 """Point substitution in a coding sequence read from position 0 (frame 0).

 ``consequence`` uses Sequence Ontology / Ensembl VEP terms: start_lost,
 stop_lost, stop_retained_variant, stop_gained, synonymous_variant,
 missense_variant. ``silent``/``nonsense`` are kept for backward compatibility.
 """
 from ...bio.sequence import STANDARD_CODE
 dna=dna.upper()
 if not 0<=pos<len(dna) or base not in 'ACGT': raise ValueError('invalid mutation')
 before=execute_translation(dna); mutant=dna[:pos]+base+dna[pos+1:]; after=execute_translation(mutant)
 ci=pos//3; ref=dna[ci*3:ci*3+3]; alt=mutant[ci*3:ci*3+3]
 if len(ref)<3: cons='incomplete_terminal_codon_variant'
 else:
  ra=STANDARD_CODE.get(ref,'X'); aa=STANDARD_CODE.get(alt,'X')
  if ci==0 and ref=='ATG' and alt!='ATG': cons='start_lost'
  elif ra=='*' and aa!='*': cons='stop_lost'
  elif ra=='*': cons='stop_retained_variant'
  elif aa=='*': cons='stop_gained'
  elif ra==aa: cons='synonymous_variant'
  else: cons='missense_variant'
 return {'mutant_dna':mutant,'before_protein':before,'after_protein':after,'silent':before==after,'nonsense':len(after)<len(before),'consequence':cons}
def analogy_limits(concept):
 limits={'transcription':['RNA processing and chromatin are omitted'],'translation':['ribosome kinetics and folding are omitted'],'crispr':['off-target search and DNA repair outcomes are simplified'],'mutation':['cell context and regulation are omitted']}; return {'concept':concept,'limits':limits.get(concept,['analogy is educational, not a mechanistic simulator']),'status':'educational analogy'}
def concept_report(concept,sequence=None):
 base=translate_concept(concept); result=None
 if sequence and base['concept']=='transcription':result=execute_transcription(sequence)
 if sequence and base['concept']=='translation':result=execute_translation(sequence)
 return {**base,'executable_example_result':result,'limits':analogy_limits(base['concept']),'model_status':'Deterministic educational utilities; no biological prediction model.'}
