from __future__ import annotations

CONCEPTS: dict[str, dict] = {
    "transcription": {
        "analogy": "Reading a read-only source file into a working buffer.",
        "code": (
            "def transcribe(dna_template: str) -> str:\n"
            "    # RNA polymerase = a streaming reader with a writable handle\n"
            "    with open_readonly(dna_template) as src:\n"
            "        mrna = src.read().replace('T', 'U')  # swap alphabet\n"
            "    return mrna\n"
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
