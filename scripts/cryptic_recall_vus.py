"""Drop 46: cryptic-site scan recall on the drop-42 VUS sweep. Question: do
the 179 strong-loss VUS also create/strengthen a CRYPTIC site in their
flanking intron (compound mechanism), and at what rate vs weak-VUS controls?
For each VUS at a natural site, extract +/-100 nt of flanking sequence in
transcript orientation from the RefSeqGene record (genomic position derived
from the same span math as load_gene), apply the substitution, and run
deepsplice.cryptic_scan on the pair.

Honest design: cryptic_scan's own validation (drop 23) found new-site events
are high-precision/rare, strengthen events candidate-generating only. The
report keeps both classes separate and never upgrades a VUS on this basis -
enrichment over the control rate is the measured quantity, not per-variant
calls.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.modules.deepsplice import cryptic_scan
from validate_multigene_splice import load_gene, GENES as G1, TX_OVERRIDE as T1
import validate_extended_splice as ext
import validate_round3_splice as r3
from gb_parse import parse_genbank, transcript_exons, revcomp

GENES = {"BRCA1": "NG_005905.2", **G1, **ext.GENES, **r3.GENES}
GENES.pop("GJB2", None)
FLANK = 100


def gene_context(acc):
    """seq, strand, and span math to locate any donor/acceptor window."""
    txt = entrez._get("efetch.fcgi", {"db": "nuccore", "id": acc,
                                      "rettype": "gb", "retmode": "text"}).decode()
    gb = parse_genbank(txt)
    seq = gb["sequence"]
    cds = max((f for f in gb["features"] if f["key"] == "CDS" and len(f["spans"]) >= 2),
              key=lambda c: len(c["spans"]))
    return seq, cds["strand"], transcript_exons(cds)


def locate(seq, strand, spans, site_type, cn):
    """Genomic slice (start, end) of the natural-site window for c. number
    cn, in record coordinates; plus a function to render any genomic slice
    in transcript orientation."""
    def cdna_of(pos):
        n = 0
        for a, b in spans:
            if strand == 1:
                if pos < a: return None
                if a <= pos <= b: return n + (pos - a + 1)
                n += b - a + 1
            else:
                if pos > b: return None
                if a <= pos <= b: return n + (b - pos + 1)
                n += b - a + 1
        return None
    for i, ((a, b), (c, d)) in enumerate(zip(spans, spans[1:])):
        if strand == 1:
            if site_type == "donor" and cdna_of(b) == cn:
                return b - 3, b + 6
            if site_type == "acceptor" and cdna_of(c) == cn:
                return c - 15, c
        else:
            if site_type == "donor" and cdna_of(a) == cn:
                return a - 7, a + 2
            if site_type == "acceptor" and cdna_of(d) == cn:
                return d - 1, d + 14
    return None


def context_pair(seq, strand, w0, w1, idx, altb):
    """Ref/alt +/-FLANK context in transcript orientation around the
    variant at window index idx."""
    wlen = w1 - w0
    if strand == 1:
        g = w0 + idx
        ref = seq[g - FLANK:g + FLANK + 1]
        alt = ref[:FLANK] + altb + ref[FLANK + 1:]
    else:
        g = w1 - 1 - idx
        ref = revcomp(seq[g - FLANK:g + FLANK + 1])
        alt = ref[:FLANK] + altb + ref[FLANK + 1:]
    return ref, alt


def main():
    fix = json.loads(Path("tests/fixtures/vus_splice_golden.json").read_text())
    strong, control = [], []
    for g, gd in fix["genes"].items():
        for c in gd["cases"]:
            m = re.match(r"c\.(\d+)([+-])(\d+)([ACGT])>([ACGT])", c["notation"])
            row = (g.upper(), c["site_type"], int(m.group(1)), c["index"],
                   m.group(5), c["notation"], c["delta"])
            (strong if c["delta"] <= -0.15 else control).append(row)
    control = [r for r in control if r[6] > -0.05]  # clear no-signal band
    print(f"strong-loss VUS: {len(strong)}  weak controls: {len(control)}")

    ctx = {}
    results = {"strong": {"new": 0, "natural_reclass": 0, "strengthened": 0,
                          "n": 0, "skipped": 0},
               "control": {"new": 0, "natural_reclass": 0, "strengthened": 0,
                           "n": 0, "skipped": 0}}
    detail = []
    for label, rows in (("strong", strong), ("control", control)):
        for g, st, cn, idx, altb, notation, delta in rows:
            if g not in GENES:  # MUTYH/SCN1A use cdna maps - skip loudly
                results[label]["skipped"] += 1
                continue
            if g not in ctx:
                ctx[g] = gene_context(GENES[g])
            seq, strand, spans = ctx[g]
            loc = locate(seq, strand, spans, st, cn)
            if not loc:
                results[label]["skipped"] += 1
                continue
            ref, alt = context_pair(seq, strand, loc[0], loc[1], idx, altb)
            cs = cryptic_scan(ref, alt)
            # the variant sits at flank index FLANK; the natural window spans
            # [FLANK-idx, FLANK-idx+wlen). Findings inside it are the NATURAL
            # site reclassified (e.g. BRCA2 c.7976+2C>T: GC donor -> GT donor
            # at the same position), not cryptic sites - count separately.
            wlen = loc[1] - loc[0]
            nat0, nat1 = FLANK - idx, FLANK - idx + wlen
            def in_natural(f):
                return f["position"] < nat1 and f["position"] + (9 if f["site_type"] == "donor" else 15) > nat0
            new_c = [f for f in cs["strong_findings"] if not in_natural(f)]
            new_n = [f for f in cs["strong_findings"] if in_natural(f)]
            str_c = [f for f in cs["findings"]
                     if f["type"] == "strengthened_site" and not in_natural(f)]
            results[label]["new"] += bool(new_c)
            results[label]["natural_reclass"] += bool(new_n)
            results[label]["strengthened"] += bool(str_c)
            results[label]["n"] += 1
            if label == "strong" and (new_c or new_n):
                detail.append({"gene": g, "notation": notation, "delta": delta,
                               "new_cryptic": len(new_c),
                               "natural_reclass": len(new_n),
                               "strengthened": len(str_c),
                               "cryptic_findings": new_c[:2],
                               "natural_findings": new_n[:1]})
    print(json.dumps(results, indent=1))
    json.dump({"source": "cryptic_scan recall on drop-42 VUS (flanks from RefSeqGene "
                         "records, +/-100 nt, transcript orientation); enrichment vs "
                         "weak-VUS controls is the measured quantity - per-variant "
                         "calls are NOT upgraded on this basis",
               "results": results, "strong_with_cryptic": detail},
              open("tests/fixtures/cryptic_recall_vus.json", "w"), indent=1)
    for d in detail[:10]:
        print(f'  {d["gene"]:7s} {d["notation"]:16s} delta={d["delta"]:+.3f} '
              f'cryptic={d["new_cryptic"]} natural={d["natural_reclass"]}')

if __name__ == "__main__":
    main()
