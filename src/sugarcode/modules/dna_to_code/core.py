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


def translate_concept(concept: str) -> dict:
    key = concept.lower().replace(" ", "_").replace("-", "_")
    if key not in CONCEPTS:
        raise KeyError(f"unknown concept {concept!r}; have {sorted(CONCEPTS)}")
    c = CONCEPTS[key]
    return {"concept": key, "analogy": c["analogy"], "python": c["code"],
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
