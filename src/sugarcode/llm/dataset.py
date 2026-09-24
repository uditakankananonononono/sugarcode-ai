"""Sugarcode domain dataset: tool-calling examples for fine-tuning a small on-device model.

Output is JSONL in the format cactus-compute/needle fine-tunes on
(https://github.com/cactus-compute/needle): one example per line with
`query`, `tools` and `answers`, the last two JSON-encoded strings.

Each example uses a real catalog tool with concrete inputs from a value bank
and is kept only if executing that exact call against the SugarCode module
succeeds, so every answer is a verified-executable call. Queries come from
phrasing templates filled with the tool's own description and inputs; they
are synthetic, and the build report says so.
"""
from __future__ import annotations

import json
import random
import time

from .tools import Tool, call_tool, catalog


def _rand_seq(rng: random.Random, alphabet: str, n: int) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


def value_bank(seed: int = 0) -> dict[str, list]:
    rng = random.Random(seed)
    dna = [_rand_seq(rng, "ACGT", n) for n in (60, 90, 120)]
    prot = [_rand_seq(rng, "ACDEFGHIKLMNPQRSTVWY", n) for n in (40, 80)]
    guides = [_rand_seq(rng, "ACGT", 20) for _ in range(3)]
    return {
        "gene": ["TP53", "BRCA1", "KRAS", "EGFR", "CFTR"],
        "tissue": ["liver", "muscle", "retina", "lung", "brain"],
        "smiles": ["CC(=O)Oc1ccccc1C(=O)O", "CCO", "c1ccccc1O", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"],
        "seq": dna + prot, "sequence": dna + prot, "dna": dna, "protein": prot,
        "guide": guides, "spacer": guides, "off_target": guides,
        "target": ["EGFR", "PD-L1", "HER2", "CD19"],
        "payload": ["Cas9", "GFP", "base editor", "shRNA"],
        "disease": ["cystic fibrosis", "type 2 diabetes", "Duchenne muscular dystrophy"],
        "pathogen": ["E. coli", "Pseudomonas aeruginosa", "Staphylococcus aureus"],
        "symptoms": [["seizures", "developmental delay"], ["muscle weakness", "fatigue"]],
        "drugs": [["imatinib", "dasatinib"], ["erlotinib"]],
        "variants": [["p.R175H"], ["p.G12D", "p.G13D"]],
        "ligand": ["ATP", "imatinib", "caffeine"], "chassis": ["E. coli", "S. cerevisiae", "B. subtilis"],
        "identifier": ["1CRN", "P69905"], "source": ["pubmed", "uniprot"],
        "inquiry": ["How do I export results?", "Need a custom model build"],
        "transgene_kb": [1.5, 3.0, 4.2], "mutant_aa": ["H", "D", "V"], "index": [1, 5, 10],
        "window": [dna[0][:30]], "win60": [dna[0][:60]], "background": [dna[1]],
        "pocket_residues": ["A:45,A:48,A:92"], "process": ["fermentation", "purification"],
        "module": ["crispr_opt", "codon_opt"], "doses": [[0.1, 1.0, 10.0]],
        "observations": [["cell count rose", "colonies turned blue"]], "candidates": [["A", "B", "C"]],
    }


TEMPLATES = [
    "{desc} Inputs: {args}.",
    "Can you {verb} with {args}?",
    "Use SugarCode to {verb}: {args}",
    "I need this for my lab: {verb} ({args})",
    "Run {name} on {args}",
    "{args} - {verb} please",
]


def _phrase(t: Tool, args: dict, rng: random.Random) -> str:
    desc = t.description.split(". ")[0].rstrip(".")
    verb = desc[0].lower() + desc[1:] if desc else t.function.replace("_", " ")
    shown = ", ".join(f"{k.replace('_', ' ')} {v if not isinstance(v, list) else ', '.join(map(str, v))}"
                      for k, v in args.items())
    return rng.choice(TEMPLATES).format(desc=desc + ".", verb=verb, args=shown or "defaults",
                                        name=t.function.replace("_", " "))


def _needle_schema(t: Tool) -> dict:
    req = t.parameters["required"]
    return {"name": t.name, "description": t.description,
            "parameters": {k: dict(v, required=k in req) for k, v in t.parameters["properties"].items()}}


def build(per_tool: int = 120, seed: int = 0, max_tools: int | None = None) -> tuple[list[dict], dict]:
    rng = random.Random(seed)
    bank = value_bank(seed)
    cat = sorted(catalog().values(), key=lambda t: t.name)
    rows, used, skipped = [], {}, {}
    for t in cat[:max_tools]:
        req = t.parameters["required"]
        if any(r not in bank for r in req):
            skipped[t.name] = "inputs not in value bank"
            continue
        if any(k in t.parameters["properties"] for k in ("offline", "live", "use_network")):
            skipped[t.name] = "network-backed tool"
            continue
        trial = {r: bank[r][0] for r in req}
        t0 = time.time()
        ok = "error" not in call_tool(t.name, trial)
        if time.time() - t0 > 0.25:
            skipped[t.name] = "too slow for bulk generation"
            continue
        if not ok:
            skipped[t.name] = "sample call failed"
            continue
        made = 0
        for _ in range(per_tool * 3):
            if made >= per_tool:
                break
            args = {r: rng.choice(bank[r]) for r in req}
            if "error" in call_tool(t.name, args):
                continue
            tools = [t] + rng.sample([x for x in cat if x.module != t.module], 3)  # distractors
            rng.shuffle(tools)
            rows.append({"query": _phrase(t, args, rng), "tools": json.dumps([_needle_schema(x) for x in tools]),
                         "answers": json.dumps([{"name": t.name, "arguments": args}])})
            made += 1
        used[t.name] = made
    rng.shuffle(rows)
    report = {"format": "needle JSONL (query, tools, answers)", "examples": len(rows),
              "tools_covered": len(used), "tools_skipped": len(skipped), "per_tool_target": per_tool,
              "queries": "synthetic, template-generated; every answer executed successfully",
              "skipped": skipped}
    return rows, report
