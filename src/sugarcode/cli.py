"""SugarCode AI command-line interface (drops 57 + 60).

Subcommands (all offline except splice assess, all JSON on stdout):
  version                          print version
  modules                          list the 88 registered modules
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


def _cmd_models_list(args) -> int:
    from .llm.providers import profile_status
    return _emit(profile_status(probe=args.probe, allow_paid=args.allow_paid or None))


def _cmd_models_check(args) -> int:
    from .llm.providers import ProviderError, parse_route, resolve
    names = [args.profile] if args.profile else parse_route()
    out = []
    for n in names:
        try:
            out.append(resolve(n, allow_paid=args.allow_paid or None).health())
        except ProviderError as e:
            out.append({"profile": n, "ok": False, "error": str(e)})
    _emit(out)
    return 0 if any(r.get("ok") for r in out) else 1


def _cmd_route(args) -> int:
    from .llm.router import route
    from .llm.tools import tools_for_modules
    mods = route(args.question, k=args.k)
    return _emit({"modules": mods,
                  "tools": [t.name for t in tools_for_modules([m["module"] for m in mods])]})


def _cmd_tool(args) -> int:
    from .llm.tools import call_tool, catalog
    if args.name == "list":
        return _emit(sorted(catalog()))
    res = call_tool(args.name, args.arguments or "{}")
    _emit(res)
    return 0 if "error" not in res else 1


def _cmd_ask(args) -> int:
    from .llm.agent import ask
    res = ask(args.question, profile=args.profile, route=args.route, model=args.model,
              allow_paid=args.allow_paid or None)
    _emit(res.to_dict())
    return 0 if res.answer else 1


def _cmd_ailibrary(args) -> int:
    from .llm import ailibrary
    if args.sub == "search":
        return _emit(ailibrary.search(args.query, limit=args.limit))
    return _emit(ailibrary.tool(args.slug))


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
    m = sub.add_parser("modules", help="list the 88 registered modules")
    m.set_defaults(func=_cmd_modules)
    md = sub.add_parser("models", help="model profiles: list | check")
    mdsub = md.add_subparsers(dest="sub", required=True)
    ml = mdsub.add_parser("list", help="every model profile and whether it is configured")
    ml.add_argument("--probe", action="store_true", help="also run the zero-token health probe")
    ml.add_argument("--allow-paid", action="store_true")
    ml.set_defaults(func=_cmd_models_list)
    mc = mdsub.add_parser("check", help="zero-token health probe (GET /models)")
    mc.add_argument("profile", nargs="?", default=None)
    mc.add_argument("--allow-paid", action="store_true")
    mc.set_defaults(func=_cmd_models_check)

    r = sub.add_parser("route", help="trained router: which modules answer this question")
    r.add_argument("question")
    r.add_argument("-k", type=int, default=3)
    r.set_defaults(func=_cmd_route)

    t = sub.add_parser("tool", help="run one module tool: tool NAME 'JSON args' | tool list")
    t.add_argument("name")
    t.add_argument("arguments", nargs="?", default=None)
    t.set_defaults(func=_cmd_tool)

    k = sub.add_parser("ask", help="ask the copilot (router + module tools + chat model)")
    k.add_argument("question")
    k.add_argument("--profile", default=None, help="pin one model profile")
    k.add_argument("--route", default=None, help="ordered fallback, e.g. inkling-local,ollama,inkling")
    k.add_argument("--model", default=None)
    k.add_argument("--allow-paid", action="store_true", help="permit hosted_paid profiles (Fugu)")
    k.set_defaults(func=_cmd_ask)

    al = sub.add_parser("ailibrary", help="read-only AI Library (theailibrary.co) tool catalog")
    alsub = al.add_subparsers(dest="sub", required=True)
    als = alsub.add_parser("search", help="find tools by keywords")
    als.add_argument("query")
    als.add_argument("--limit", type=int, default=5)
    als.set_defaults(func=_cmd_ailibrary)
    alt = alsub.add_parser("tool", help="details for one tool slug")
    alt.add_argument("slug")
    alt.set_defaults(func=_cmd_ailibrary)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
