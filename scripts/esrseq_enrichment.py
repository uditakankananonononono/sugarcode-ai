"""Drop 48: ESRseq enrichment on the exonic donor golden (drop 45). Do
pathogenic exonic donor-window variants disrupt exonic splicing enhancers
more than VUS/benign? For each case, ref/alt 11-mers around the variant
(6 overlapping hexamers, transcript orientation, exonic context from the
RefSeqGene record) are scored with the vendored ESRseq hexamer model
(Ke et al. 2011 lineage - PROVENANCE). Enrichment by classification bucket
is the measured quantity; per-variant calls are NOT upgraded on this basis.
"""
from __future__ import annotations
import json, re, sys, statistics as st
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio.splice import esrseq_score
from cryptic_recall_vus import gene_context, locate, context_pair, GENES, FLANK

def main():
    fix = json.loads(Path("tests/fixtures/exonic_donor_golden.json").read_text())
    ctx = {}
    out = []
    skipped = 0
    for g, gd in fix["genes"].items():
        sym = g.upper()
        for c in gd["cases"]:
            m = re.match(r"c\.(\d+)([ACGT])>([ACGT])", c["notation"])
            if not m:
                skipped += 1
                continue
            cn, altb = int(m.group(1)), m.group(3)
            if sym not in GENES:
                skipped += 1
                continue
            if sym not in ctx:
                ctx[sym] = gene_context(GENES[sym])
            seq, strand, spans = ctx[sym]
            # donor key N: terminal base is c.N (offset -1). The donor at
            # c.N covers the variant; locate by the donor key N = cn - offset
            N = cn - c["exonic_offset"] - 1 if False else None
            # simpler: donor key for offset -1 is cn itself; -2 -> cn+1; -3 -> cn+2
            N = cn - c["exonic_offset"] - 1
            loc = locate(seq, strand, spans, "donor", N)
            if not loc:
                skipped += 1
                continue
            ref, alt = context_pair(seq, strand, loc[0], loc[1], c["index"], altb)
            ref11, alt11 = ref[FLANK - 5:FLANK + 6], alt[FLANK - 5:FLANK + 6]
            d_esr = round(esrseq_score(alt11) - esrseq_score(ref11), 4)
            # exonic-only ESRseq delta: ESRseq scores are defined on EXONIC
            # hexamers; of the 6 hexamers overlapping the variant only those
            # fully inside the exon count (offset -1: 1 hexamer, -2: 2, -3: 3).
            ex_end = 5 + (-c["exonic_offset"])       # index past exon in the 11-mer
            vpos = 5                                  # variant position in the 11-mer
            starts = [s for s in range(max(0, vpos - 5), vpos + 1)
                      if s + 6 <= ex_end]
            d_exon = round(sum(esrseq_score(alt11[s:s + 6]) - esrseq_score(ref11[s:s + 6])
                               for s in starts), 4)
            out.append({"gene": sym, "notation": c["notation"],
                        "exonic_offset": c["exonic_offset"], "sig": c["sig"],
                        "esrseq_delta": d_esr, "esrseq_delta_exonic": d_exon,
                        "n_exonic_hexamers": len(starts)})
    by = {}
    for r in out:
        by.setdefault(r["sig"], []).append(r)
    print(f"scored: {len(out)}  skipped: {skipped}")
    summary = {}
    for sig, v in sorted(by.items()):
        d_all = [r["esrseq_delta"] for r in v]
        d_ex = [r["esrseq_delta_exonic"] for r in v]
        summary[sig] = {"n": len(v),
                        "mean_esrseq_delta": round(st.mean(d_all), 4),
                        "mean_esrseq_delta_exonic": round(st.mean(d_ex), 4),
                        "frac_disrupting_exonic":
                            round(sum(1 for x in d_ex if x < -0.5) / len(v), 3)}
        print(f"{sig:12s} n={len(v):4d} all-hex {st.mean(d_all):+.3f} "
              f"exonic-only {st.mean(d_ex):+.3f} "
              f"disrupting(<-0.5): {sum(1 for x in d_ex if x < -0.5)/len(v):.1%}")
    json.dump({"source": "ESRseq (Ke et al. 2011 lineage, vendored - PROVENANCE) ref-vs-alt "
                         "11-mer deltas on the drop-45 exonic donor golden; enrichment by "
                         "classification bucket, NOT per-variant upgrades",
               "summary": summary, "cases": out},
              open("tests/fixtures/esrseq_enrichment.json", "w"), indent=1)

if __name__ == "__main__":
    main()
