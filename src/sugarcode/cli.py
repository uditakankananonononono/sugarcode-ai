"""SugarCode AI command-line interface (drops 57 + 60).

Subcommands (all offline except splice assess, all JSON on stdout):
  version                          print version
  modules                          list the 93 registered modules
  splice assess GENE NOTATION      deepsplice live assessment [--transcript NM] [--offline]
  codon cai SEQ                    codon adaptation index vs a published table
  codon optimize PROTEIN           codon-optimized DNA (GC-window repair, motif avoidance)
  fasta stats FILE                 record count, lengths, GC
  genbank features FILE            locus feature summary (type counts, spans)
  pwm score SEQ --motif NAME       normalized log-odds score on a shipped splice matrix

Exit codes: 0 ok, 2 usage error.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .modules.deepsplice import live_splice_assessment

_SPECIES = ("e_coli_316407", "h_sapiens_9606", "s_cerevisiae_4932")


def _motif_lods():
    from .bio import splice
    return {
        "donor": splice.donor_lod,
        "acceptor": splice.acceptor_lod,
        "gc-donor": splice.gc_donor_lod,
        "u12-atac-donor": splice.u12_atac_donor_lod,
        "u12-atac-acceptor": splice.u12_atac_acceptor_lod,
        "u12-gtag-donor": splice.u12_gtag_donor_lod,
        "u12-gtag-acceptor": splice.u12_gtag_acceptor_lod,
    }


def _emit(obj) -> int:
    json.dump(obj, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


def _cmd_splice_assess(args) -> int:
    return _emit(live_splice_assessment(args.gene, args.notation,
                                        offline=args.offline,
                                        transcript=args.transcript))


def _cmd_version(_args) -> int:
    print(f"sugarcode-ai {__version__}")
    return 0


def _cmd_modules(_args) -> int:
    # The product surface is the canonical registry; since the audit fix every
    # package in src/sugarcode/modules/ is registered, so this lists all of them.
    from omega.registry import module_slugs
    names = sorted(module_slugs())
    print(f"{len(names)} modules")
    for n in names:
        print(n)
    return 0


def _cmd_codon_cai(args) -> int:
    from .bio.codon import cai, load_published_table
    table = load_published_table(args.species)
    seq = args.sequence.upper().replace(" ", "")
    return _emit({"species": args.species, "length": len(seq),
                  "cai": round(cai(seq, table), 6)})


def _cmd_codon_optimize(args) -> int:
    from .bio.codon import cai, load_published_table, optimize_sequence
    from .bio.sequence import gc_content
    table = load_published_table(args.species)
    avoid = [m for m in (args.avoid or "").split(",") if m]
    dna = optimize_sequence(args.protein.upper(), table,
                            gc_min=args.gc_min, gc_max=args.gc_max,
                            avoid_motifs=avoid or None)
    return _emit({"species": args.species, "protein_length": len(args.protein),
                  "dna": dna, "gc": round(gc_content(dna), 4),
                  "cai": round(cai(dna, table), 6)})


def _cmd_fasta_stats(args) -> int:
    from .bio.fasta import parse_fasta
    from .bio.sequence import gc_content
    text = Path(args.file).read_text()
    recs = parse_fasta(text)
    return _emit({
        "file": args.file, "records": len(recs),
        "total_length": sum(len(r["sequence"]) for r in recs),
        "entries": [{"id": r["id"], "length": len(r["sequence"]),
                     "gc": round(gc_content(r["sequence"]), 4)} for r in recs],
    })


def _cmd_genbank_features(args) -> int:
    from .bio.genbank import parse_genbank
    text = Path(args.file).read_text()
    gb = parse_genbank(text)
    counts: dict[str, int] = {}
    for f in gb["features"]:
        counts[f["key"]] = counts.get(f["key"], 0) + 1
    return _emit({"file": args.file, "sequence_length": len(gb["sequence"]),
                  "feature_counts": dict(sorted(counts.items())),
                  "features": [{"key": f["key"], "strand": f["strand"],
                                "spans": f["spans"]} for f in gb["features"]]})


def _cmd_pwm_score(args) -> int:
    from .bio.pwm import normalized_score, scan
    lods = _motif_lods()
    lod = lods[args.motif]()
    seq = args.sequence.upper().replace(" ", "")
    out = {"motif": args.motif, "length": len(seq),
           "window": len(lod),
           "normalized_score": None, "hits": None}
    if len(seq) == len(lod):
        out["normalized_score"] = round(normalized_score(seq, lod), 6)
    if len(seq) >= len(lod):
        hits = scan(seq, lod, threshold=args.threshold)
        out["hits"] = [{"position": h["position"], "score": round(h["score"], 6)}
                       for h in hits[: args.max_hits]]
    return _emit(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sugarcode",
                                description="SugarCode AI - multi-omic bio-design platform")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("splice", help="deepsplice splice assessment")
    ssub = sp.add_subparsers(dest="sub", required=True)
    a = ssub.add_parser("assess", help="assess one ClinVar-style notation")
    a.add_argument("gene")
    a.add_argument("notation")
    a.add_argument("--transcript", default=None,
                   help="NM_ accession for an explicit transcript map")
    a.add_argument("--offline", action="store_true",
                   help="use the record cache only (no network)")
    a.set_defaults(func=_cmd_splice_assess)

    c = sub.add_parser("codon", help="codon usage tools (published tables)")
    csub = c.add_subparsers(dest="sub", required=True)
    ci = csub.add_parser("cai", help="codon adaptation index of a DNA sequence")
    ci.add_argument("sequence")
    ci.add_argument("--species", default="e_coli_316407", choices=_SPECIES)
    ci.set_defaults(func=_cmd_codon_cai)
    op = csub.add_parser("optimize", help="codon-optimize a protein sequence")
    op.add_argument("protein")
    op.add_argument("--species", default="e_coli_316407", choices=_SPECIES)
    op.add_argument("--gc-min", type=float, default=0.40)
    op.add_argument("--gc-max", type=float, default=0.60)
    op.add_argument("--avoid", default=None,
                    help="comma-separated forbidden DNA motifs")
    op.set_defaults(func=_cmd_codon_optimize)

    f = sub.add_parser("fasta", help="FASTA tools")
    fsub = f.add_subparsers(dest="sub", required=True)
    fs = fsub.add_parser("stats", help="record count, lengths, GC")
    fs.add_argument("file")
    fs.set_defaults(func=_cmd_fasta_stats)

    g = sub.add_parser("genbank", help="GenBank tools")
    gsub = g.add_subparsers(dest="sub", required=True)
    gf = gsub.add_parser("features", help="feature summary of a .gb file")
    gf.add_argument("file")
    gf.set_defaults(func=_cmd_genbank_features)

    w = sub.add_parser("pwm", help="splice-site matrix scoring")
    wsub = w.add_subparsers(dest="sub", required=True)
    ws = wsub.add_parser("score", help="score a sequence on a shipped matrix")
    ws.add_argument("sequence")
    ws.add_argument("--motif", required=True, choices=sorted(_motif_lods()))
    ws.add_argument("--threshold", type=float, default=0.0,
                    help="scan hit threshold (log-odds bits)")
    ws.add_argument("--max-hits", type=int, default=20)
    ws.set_defaults(func=_cmd_pwm_score)

    v = sub.add_parser("version", help="print version")
    v.set_defaults(func=_cmd_version)
    m = sub.add_parser("modules", help="list the 93 registered modules")
    m.set_defaults(func=_cmd_modules)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
