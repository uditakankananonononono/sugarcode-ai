"""SugarCode AI command-line interface (drops 57 + 60).

Subcommands (all offline except splice assess, all JSON on stdout):
  version                          print version
  modules                          list the 89 registered modules
  splice assess GENE NOTATION      deepsplice live assessment [--transcript NM] [--offline]
  codon cai SEQ                    codon adaptation index vs a published table
  codon optimize PROTEIN           codon-optimized DNA (GC-window repair, motif avoidance)
  fasta stats FILE                 record count, lengths, GC
  genbank features FILE            locus feature summary (type counts, spans)
  pwm score SEQ --motif NAME       normalized log-odds score on a shipped splice matrix
  report splice GENE NOTATION    render an assessment as HTML/Markdown/bundle (drop 62)
  vcf stats FILE                 variant classes, Ti/Tv, genotype counts (drop 63)
  fastq stats FILE               FastQC-style read/quality summary (drop 64)
  gff stats FILE                 GFF3/GTF feature summary (drop 65)
  bed stats FILE                 BED interval summary (drop 66)
  sam stats FILE                 SAM mapping summary (drop 67)
  sam pileup FILE [--min-mapq N] [--min-baseq N] [--rname X] [--format json|mpileup]  (drop 70)
  phylo stats FILE               Newick tree summary (drop 68)
  phylo mrca FILE --leaves a,b,c
  phylo distance FILE --a X --b Y
  phylo prune FILE --drop a,b [--out F]
  msa stats FILE                 Stockholm/A3M summary, auto-detect (drop 69)
  pdb stats FILE                 structure summary, PDB or mmCIF (drop 71)
  protein props FILE|--sequence  pI, MW, extinction, instability, GRAVY (drop 72)
  primer tm SEQ                  SantaLucia NN Tm (drop 73)
  motif scan --sites F|--iupac S|--jaspar F --sequence S|--fasta F  (drop 74)
  digest run --fasta F --enzymes EcoRI,BamHI [--circular] [--cuts]  (drop 75)
  align run --a S1 --b S2 [--mode global|local] [--matrix BLOSUM62]  (drop 76)
  digest list [--match X] | digest info ENZYME
  motif info <source>            consensus, score range, PWM
  motif to-jaspar <source>
  primer check SEQ               GC/homopolymer/hairpin/dimer heuristics
  primer pick FILE --region S:E  primer pairs flanking a region
  pdb chains FILE [--residues [--chain X]]
  pdb contacts FILE --cutoff 5.0 [--chain-a A --chain-b B]
  pdb select FILE [--chain X] [--resname Y] [--names CA,CB] [--out F]
  msa consensus FILE [--threshold 0.5]
  msa pid FILE --a id1 --b id2
  msa filter FILE [--min-occupancy F] [--min-coverage F] [--out F]
  msa a2m FILE [--out F]         strip A3M inserts -> match states
  sam filter FILE [--mapped-only --min-mapq N --rname .. --primary-only]
  sam to-bed FILE                mapped reads to BED6
  bed merge FILE [--out F]       merge overlapping intervals
  bed filter FILE [--chrom .. --min-width N --min-score N]
  bed to-gff FILE [--feature-type T]
  gff query FILE --chrom X --start A --end B [--type ..]
  gff filter FILE [--type .. --seqid .. --no-children --out F]
  gff csv FILE
  fastq filter FILE [--min-mean-phred N --min-len N --max-n-frac F]
  fastq trim FILE [--window N --min-phred N --min-len N]
  fastq to-fasta FILE
  vcf filter FILE [--pass-only --min-qual N --chrom .. --type ..]
  vcf csv FILE [--sample NAME]   flatten records to CSV
  report notebook GENE NOTATION  executable .ipynb reproducing the assessment
  report validate-notebook FILE  structural nbformat check

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


def _cmd_report_splice(args) -> int:
    from .modules.report_studio import splice_assessment_report, bundle_report
    assessment = live_splice_assessment(args.gene, args.notation,
                                        offline=args.offline,
                                        transcript=args.transcript)
    rep = splice_assessment_report(assessment)
    if args.format == "json":
        bundle = bundle_report("splice-assessment", rep)
        return _emit({"name": bundle["name"], "created_utc": bundle["created_utc"],
                      "files": {fn: {"sha256": a["sha256"], "bytes": a["bytes"]}
                                for fn, a in bundle["artifacts"].items()},
                      "metadata": bundle["metadata"]})
    text = rep["html"] if args.format == "html" else rep["markdown"]
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_report_notebook(args) -> int:
    from .modules.report_studio import splice_notebook
    r = splice_notebook(args.gene, args.notation,
                        transcript=args.transcript, offline=args.offline)
    if args.out:
        Path(args.out).write_text(r["json"], encoding="utf-8")
        print(f"wrote {args.out} (valid={r['valid']})")
        return 0
    sys.stdout.write(r["json"])
    return 0


def _cmd_report_validate_notebook(args) -> int:
    from .report import validate_notebook
    nb = json.loads(Path(args.file).read_text())
    problems = validate_notebook(nb)
    return _emit({"file": args.file, "valid": not problems, "problems": problems})



def _cmd_vcf_stats(args) -> int:
    from .bio.vcf import parse_vcf, stats
    v = parse_vcf(Path(args.file).read_text())
    return _emit({"file": args.file, **stats(v)})


def _cmd_vcf_filter(args) -> int:
    from .bio.vcf import parse_vcf, write_vcf, filter_records
    v = parse_vcf(Path(args.file).read_text())
    out = filter_records(
        v, pass_only=args.pass_only, min_qual=args.min_qual,
        chroms=[c for c in (args.chrom or "").split(",") if c] or None,
        types=[x for x in (args.type or "").split(",") if x] or None)
    text = write_vcf(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(out['records'])} of {len(v['records'])} records)")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_vcf_csv(args) -> int:
    from .bio.vcf import parse_vcf, records_to_rows
    from .report import to_csv
    v = parse_vcf(Path(args.file).read_text())
    text = to_csv(records_to_rows(v, sample=args.sample))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0



def _cmd_fastq_stats(args) -> int:
    from .bio.fastq import parse_fastq, stats
    recs = parse_fastq(Path(args.file).read_text())
    return _emit({"file": args.file, **stats(recs, offset=args.offset)})


def _cmd_fastq_filter(args) -> int:
    from .bio.fastq import parse_fastq, write_fastq, filter_reads
    recs = parse_fastq(Path(args.file).read_text())
    out = filter_reads(recs, min_mean_phred=args.min_mean_phred,
                       min_len=args.min_len, max_len=args.max_len,
                       max_n_frac=args.max_n_frac, offset=args.offset)
    text = write_fastq(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(out)} of {len(recs)} reads)")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_fastq_trim(args) -> int:
    from .bio.fastq import parse_fastq, write_fastq, trim_reads
    recs = parse_fastq(Path(args.file).read_text())
    out = trim_reads(recs, window=args.window, min_phred=args.min_phred,
                     min_len=args.min_len, offset=args.offset)
    text = write_fastq(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(out)} of {len(recs)} reads kept after trim)")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_fastq_to_fasta(args) -> int:
    from .bio.fastq import parse_fastq, to_fasta
    recs = parse_fastq(Path(args.file).read_text())
    text = to_fasta(recs)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0



def _cmd_gff_stats(args) -> int:
    from .bio.gff import parse_gff, stats
    g = parse_gff(Path(args.file).read_text())
    return _emit({"file": args.file, **stats(g)})


def _cmd_gff_query(args) -> int:
    from .bio.gff import parse_gff, query_region
    g = parse_gff(Path(args.file).read_text())
    types = [x for x in (args.type or "").split(",") if x] or None
    hits = query_region(g, args.chrom, args.start, args.end, types=types)
    return _emit({"file": args.file,
                  "region": {"seqid": args.chrom, "start": args.start, "end": args.end},
                  "hits": len(hits),
                  "records": [{"seqid": r["seqid"], "type": r["type"],
                               "start": r["start"], "end": r["end"],
                               "strand": r["strand"],
                               "attributes": r["attributes"]} for r in hits]})


def _cmd_gff_filter(args) -> int:
    from .bio.gff import parse_gff, write_gff, filter_records
    g = parse_gff(Path(args.file).read_text())
    out = filter_records(
        g,
        types=[x for x in (args.type or "").split(",") if x] or None,
        seqids=[x for x in (args.seqid or "").split(",") if x] or None,
        keep_children=not args.no_children)
    text = write_gff(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(out['records'])} of {len(g['records'])} records)")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_gff_csv(args) -> int:
    from .bio.gff import parse_gff, records_to_rows
    from .report import to_csv
    g = parse_gff(Path(args.file).read_text())
    text = to_csv(records_to_rows(g))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0



def _cmd_bed_stats(args) -> int:
    from .bio.bed import parse_bed, stats
    b = parse_bed(Path(args.file).read_text())
    return _emit({"file": args.file, **stats(b)})


def _cmd_bed_merge(args) -> int:
    from .bio.bed import parse_bed, write_bed, merge_intervals
    b = parse_bed(Path(args.file).read_text())
    merged = merge_intervals(b["records"])
    text = write_bed({"header": b["header"], "records": merged})
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(merged)} merged of {len(b['records'])} intervals)")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_bed_filter(args) -> int:
    from .bio.bed import parse_bed, write_bed, filter_records
    b = parse_bed(Path(args.file).read_text())
    out = filter_records(
        b,
        chroms=[x for x in (args.chrom or "").split(",") if x] or None,
        min_width=args.min_width, min_score=args.min_score)
    text = write_bed(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(out['records'])} of {len(b['records'])} records)")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_bed_to_gff(args) -> int:
    from .bio.bed import parse_bed, to_gff
    from .bio.gff import write_gff
    b = parse_bed(Path(args.file).read_text())
    records = to_gff(b["records"], source=args.source,
                     feature_type=args.feature_type)
    text = write_gff({"directives": ["##gff-version 3"], "comments": [],
                      "format": "gff3", "records": records})
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0



def _cmd_sam_stats(args) -> int:
    from .bio.sam import parse_sam, stats
    s = parse_sam(Path(args.file).read_text())
    return _emit({"file": args.file, **stats(s)})


def _cmd_sam_filter(args) -> int:
    from .bio.sam import parse_sam, write_sam, filter_records
    s = parse_sam(Path(args.file).read_text())
    out = filter_records(
        s, mapped_only=args.mapped_only, min_mapq=args.min_mapq,
        rnames=[x for x in (args.rname or "").split(",") if x] or None,
        primary_only=args.primary_only)
    text = write_sam(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(out['records'])} of {len(s['records'])} alignments)")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_sam_to_bed(args) -> int:
    from .bio.sam import parse_sam, to_bed
    from .bio.bed import write_bed
    s = parse_sam(Path(args.file).read_text())
    records = to_bed(s)
    text = write_bed({"header": [], "records": records})
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(records)} mapped reads)")
        return 0
    sys.stdout.write(text)
    return 0



def _cmd_phylo_stats(args) -> int:
    from .bio.newick import parse_newick, stats
    t = parse_newick(Path(args.file).read_text())
    return _emit({"file": args.file, **stats(t)})


def _cmd_phylo_mrca(args) -> int:
    from .bio.newick import parse_newick, mrca, preorder
    t = parse_newick(Path(args.file).read_text())
    names = [x for x in args.leaves.split(",") if x]
    node = mrca(t, names)
    desc = len(preorder(node)) - 1
    return _emit({"file": args.file, "query": names,
                  "mrca": {"name": node["name"], "length": node["length"],
                           "subtree_nodes": desc}})


def _cmd_phylo_distance(args) -> int:
    from .bio.newick import parse_newick, distance
    t = parse_newick(Path(args.file).read_text())
    return _emit({"file": args.file, "a": args.a, "b": args.b,
                  "distance": distance(t, args.a, args.b)})


def _cmd_phylo_prune(args) -> int:
    from .bio.newick import parse_newick, write_newick, prune
    t = parse_newick(Path(args.file).read_text())
    out = prune(t, [x for x in args.drop.split(",") if x])
    text = write_newick(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0



def _load_alignment(path):
    """Auto-detect Stockholm (header) vs A3M and return equal-width records
    plus the raw parse for Stockholm markup."""
    from .bio.stockholm import parse_stockholm, parse_a3m, a3m_match_states
    text = Path(path).read_text()
    if text.startswith("# STOCKHOLM"):
        aln = parse_stockholm(text)
        return ([{"id": n, "sequence": s} for n, s in aln["seqs"]], aln)
    return a3m_match_states(parse_a3m(text)), None


def _cmd_msa_stats(args) -> int:
    from .bio.stockholm import stats
    records, _ = _load_alignment(args.file)
    return _emit({"file": args.file, **stats(records)})


def _cmd_msa_consensus(args) -> int:
    from .bio.stockholm import consensus
    records, _ = _load_alignment(args.file)
    return _emit({"file": args.file, "threshold": args.threshold,
                  "consensus": consensus(records, args.threshold)})


def _cmd_msa_pid(args) -> int:
    from .bio.stockholm import pairwise_identity
    records, _ = _load_alignment(args.file)
    by_id = {r["id"]: r["sequence"] for r in records}
    if args.a not in by_id or args.b not in by_id:
        raise SystemExit(f"unknown id: {args.a!r} or {args.b!r}")
    return _emit({"file": args.file, "a": args.a, "b": args.b,
                  "identity": pairwise_identity(by_id[args.a], by_id[args.b])})


def _cmd_msa_filter(args) -> int:
    from .bio.stockholm import write_a3m, filter_columns, filter_sequences
    records, _ = _load_alignment(args.file)
    if args.min_occupancy is not None:
        records = filter_columns(records, args.min_occupancy)
    if args.min_coverage is not None:
        records = filter_sequences(records, args.min_coverage)
    text = write_a3m(records)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_msa_a2m(args) -> int:
    from .bio.stockholm import parse_a3m, write_a3m, a3m_match_states
    records = a3m_match_states(parse_a3m(Path(args.file).read_text()))
    text = write_a3m(records)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0



def _cmd_sam_pileup(args) -> int:
    from .bio.sam import parse_sam
    from .bio.pileup import pileup, to_mpileup, variant_sites
    sam = parse_sam(Path(args.file).read_text())
    rows = pileup(sam, min_mapq=args.min_mapq, min_baseq=args.min_baseq,
                  rname=args.rname)
    if args.format == "mpileup":
        sys.stdout.write(to_mpileup(rows))
        return 0
    return _emit({"file": args.file, "positions": rows,
                  "variant_sites": variant_sites(rows)})



def _load_structure(path):
    from .bio.pdb import parse_pdb, parse_mmcif
    text = Path(path).read_text()
    if text.lstrip().startswith(("data_", "#")):
        return parse_mmcif(text)
    return parse_pdb(text)


def _cmd_pdb_stats(args) -> int:
    from .bio.pdb import stats
    return _emit({"file": args.file, **stats(_load_structure(args.file))})


def _cmd_pdb_chains(args) -> int:
    from .bio.pdb import chains, residues
    s = _load_structure(args.file)
    out = {"file": args.file, "chains": chains(s)}
    if args.residues:
        out["residues"] = residues(s, chain=args.chain)
    return _emit(out)


def _cmd_pdb_contacts(args) -> int:
    from .bio.pdb import contacts
    s = _load_structure(args.file)
    return _emit({"file": args.file, "cutoff": args.cutoff,
                  "contacts": contacts(s, args.cutoff, chain_a=args.chain_a,
                                       chain_b=args.chain_b)})


def _cmd_pdb_select(args) -> int:
    from .bio.pdb import select, write_pdb
    s = _load_structure(args.file)
    atoms = select(s, chain=args.chain, resname=args.resname,
                   names=(args.names.split(",") if args.names else None),
                   record=args.record,
                   model=(None if args.all_models else 1),
                   min_bfactor=args.min_bfactor)
    text = write_pdb({"format": "pdb", "header": {}, "atoms": atoms})
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(text)
    return 0



def _cmd_protein_props(args) -> int:
    from .bio.proteinprops import protein_summary
    if args.sequence:
        seqs = [("cli", args.sequence)]
    else:
        from .bio.fasta import parse_fasta
        seqs = [(r["id"], r["sequence"])
                for r in parse_fasta(Path(args.file).read_text())]
    return _emit({"proteins": [{"id": rid, **protein_summary(s)}
                               for rid, s in seqs]})



def _cmd_primer_tm(args) -> int:
    from .bio.primer import tm_nn, gc_percent
    return _emit({"sequence": args.sequence.upper(),
                  "tm": round(tm_nn(args.sequence, primer_nm=args.primer_nm,
                                    na_mm=args.na_mm), 3),
                  "gc_percent": round(gc_percent(args.sequence), 2),
                  "primer_nm": args.primer_nm, "na_mm": args.na_mm})


def _cmd_primer_check(args) -> int:
    from .bio.primer import (gc_percent, max_homopolymer, hairpin_max_stem,
                             self_dimer_max_run)
    seq = args.sequence
    return _emit({"sequence": seq.upper(),
                  "length": len(seq),
                  "gc_percent": round(gc_percent(seq), 2),
                  "max_homopolymer": max_homopolymer(seq),
                  "hairpin_max_stem": hairpin_max_stem(seq),
                  "self_dimer": self_dimer_max_run(seq),
                  "note": "hairpin/dimer are max-contiguous-complement "
                          "heuristics, not folding thermodynamics"})


def _cmd_primer_pick(args) -> int:
    from .bio.fasta import parse_fasta
    from .bio.primer import pick_primers
    try:
        start_s, end_s = args.region.split(":")
        region = (int(start_s), int(end_s))
    except ValueError:
        raise SystemExit("--region must be START:END (0-based half-open)")
    template = parse_fasta(Path(args.file).read_text())[0]["sequence"]
    pairs = pick_primers(template, region, n=args.n,
                         max_product=args.max_product,
                         primer_nm=args.primer_nm, na_mm=args.na_mm)
    out = [{"product_size": p["product_size"], "score": p["score"],
            "forward": {k: (round(v, 3) if isinstance(v, float) else v)
                        for k, v in p["forward"].items()},
            "reverse": {k: (round(v, 3) if isinstance(v, float) else v)
                        for k, v in p["reverse"].items()}}
           for p in pairs]
    return _emit({"region": region, "pairs": out, "count": len(out)})



def _load_motif(args):
    from .bio.motif import read_jaspar, from_iupac, from_alignment
    from .bio.fasta import parse_fasta
    if args.iupac:
        return from_iupac(args.iupac)
    if args.jaspar:
        return read_jaspar(Path(args.jaspar).read_text())[0]
    return from_alignment([r["sequence"]
                           for r in parse_fasta(Path(args.sites).read_text())])


def _motif_source_args(p):
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sites", default=None,
                     help="FASTA of aligned binding sites")
    src.add_argument("--iupac", default=None, help="IUPAC consensus string")
    src.add_argument("--jaspar", default=None, help="JASPAR matrix file")


def _cmd_motif_scan(args) -> int:
    from .bio.motif import scan
    from .bio.fasta import parse_fasta
    motif = _load_motif(args)
    seqs = ([args.sequence] if args.sequence
            else [r["sequence"]
                  for r in parse_fasta(Path(args.fasta).read_text())])
    out = []
    for s in seqs:
        kw = {"both_strands": not args.forward_only}
        if args.threshold is not None:
            kw["threshold"] = args.threshold
            kw["threshold_fraction"] = None
        else:
            kw["threshold_fraction"] = args.fraction
        out.append({"hits": scan(s, motif, **kw)})
    return _emit({"motif": motif["name"], "length": motif["length"],
                  "results": out})


def _cmd_motif_info(args) -> int:
    from .bio.motif import iupac_consensus, threshold_score
    motif = _load_motif(args)
    return _emit({"name": motif["name"], "length": motif["length"],
                  "consensus": iupac_consensus(motif),
                  "min_score": round(motif["min_score"], 4),
                  "max_score": round(motif["max_score"], 4),
                  "threshold_80pct": round(threshold_score(motif, 0.8), 4),
                  "pwm": motif["pwm"]})


def _cmd_motif_jaspar_convert(args) -> int:
    from .bio.motif import write_jaspar
    motif = _load_motif(args)
    sys.stdout.write(write_jaspar([motif]))
    return 0



def _cmd_digest_run(args) -> int:
    from .bio.restriction import digest, gel_bands
    if args.sequence:
        seq = args.sequence
    else:
        from .bio.fasta import parse_fasta
        seq = parse_fasta(Path(args.fasta).read_text())[0]["sequence"]
    enzymes = [e.strip() for e in args.enzymes.split(",") if e.strip()]
    d = digest(seq, enzymes, circular=args.circular)
    out = {"enzymes": enzymes, "circular": d["circular"],
           "length": d["length"], "n_sites": d["n_sites"],
           "fragments": d["fragments"], "gel": gel_bands(d["fragments"])}
    if args.cuts:
        out["cuts"] = d["cuts"]
    return _emit(out)


def _cmd_digest_list(args) -> int:
    from .bio.restriction import list_enzymes
    names = list_enzymes()
    if args.match:
        names = [n for n in names if args.match.lower() in n.lower()]
    return _emit({"count": len(names), "enzymes": names})


def _cmd_digest_info(args) -> int:
    from .bio.restriction import enzyme_info
    return _emit(enzyme_info(args.enzyme))



def _cmd_align_run(args) -> int:
    from .bio.align import nw_align, sw_align
    if args.a and args.b:
        a, b = args.a, args.b
    else:
        from .bio.fasta import parse_fasta
        recs = parse_fasta(Path(args.fasta).read_text())
        if len(recs) < 2:
            raise SystemExit("FASTA must contain at least 2 records")
        a, b = recs[0]["sequence"], recs[1]["sequence"]
    fn = sw_align if args.mode == "local" else nw_align
    r = fn(a, b, match=args.match, mismatch=args.mismatch,
           gap_open=args.gap_open, gap_extend=args.gap_extend,
           matrix=args.matrix)
    return _emit(r)



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

    aln = sub.add_parser("align", help="pairwise alignment (NW/SW, affine gaps)")
    alnsub = aln.add_subparsers(dest="sub", required=True)
    ar = alnsub.add_parser("run", help="align two sequences")
    asrc = ar.add_mutually_exclusive_group(required=True)
    asrc.add_argument("--a", default=None, help="first sequence (with --b)")
    asrc.add_argument("--fasta", default=None, help="FASTA with 2 records")
    ar.add_argument("--b", default=None)
    ar.add_argument("--mode", choices=["global", "local"], default="global")
    ar.add_argument("--matrix", choices=["BLOSUM62"], default=None)
    ar.add_argument("--match", type=float, default=2.0)
    ar.add_argument("--mismatch", type=float, default=-1.0)
    ar.add_argument("--gap-open", type=float, default=-5.0)
    ar.add_argument("--gap-extend", type=float, default=-1.0)
    ar.set_defaults(func=_cmd_align_run)

    dg = sub.add_parser("digest", help="restriction digest toolkit")
    dgsub = dg.add_subparsers(dest="sub", required=True)
    dr = dgsub.add_parser("run", help="digest a sequence, list fragments + gel")
    dsrc = dr.add_mutually_exclusive_group(required=True)
    dsrc.add_argument("--sequence", default=None)
    dsrc.add_argument("--fasta", default=None)
    dr.add_argument("--enzymes", required=True, help="comma-separated names")
    dr.add_argument("--circular", action="store_true")
    dr.add_argument("--cuts", action="store_true", help="include per-cut detail")
    dr.set_defaults(func=_cmd_digest_run)
    dl = dgsub.add_parser("list", help="list vendored enzymes")
    dl.add_argument("--match", default=None)
    dl.set_defaults(func=_cmd_digest_list)
    di = dgsub.add_parser("info", help="enzyme cut details")
    di.add_argument("enzyme")
    di.set_defaults(func=_cmd_digest_info)

    mot = sub.add_parser("motif", help="PWM motif toolkit")
    motsub = mot.add_subparsers(dest="sub", required=True)
    msc = motsub.add_parser("scan", help="scan sequences for motif hits")
    _motif_source_args(msc)
    tgt = msc.add_mutually_exclusive_group(required=True)
    tgt.add_argument("--sequence", default=None)
    tgt.add_argument("--fasta", default=None)
    msc.add_argument("--threshold", type=float, default=None)
    msc.add_argument("--fraction", type=float, default=0.8)
    msc.add_argument("--forward-only", action="store_true")
    msc.set_defaults(func=_cmd_motif_scan)
    minfo = motsub.add_parser("info", help="motif summary + PWM")
    _motif_source_args(minfo)
    minfo.set_defaults(func=_cmd_motif_info)
    mcv = motsub.add_parser("to-jaspar", help="emit JASPAR matrix")
    _motif_source_args(mcv)
    mcv.set_defaults(func=_cmd_motif_jaspar_convert)

    prm = sub.add_parser("primer", help="PCR primer toolkit")
    prmsub = prm.add_subparsers(dest="sub", required=True)
    ptm = prmsub.add_parser("tm", help="SantaLucia NN melting temperature")
    ptm.add_argument("sequence")
    ptm.add_argument("--primer-nm", type=float, default=25.0)
    ptm.add_argument("--na-mm", type=float, default=50.0)
    ptm.set_defaults(func=_cmd_primer_tm)
    pck = prmsub.add_parser("check", help="GC/homopolymer/hairpin/dimer heuristics")
    pck.add_argument("sequence")
    pck.set_defaults(func=_cmd_primer_check)
    ppk = prmsub.add_parser("pick", help="pick primer pairs around a region")
    ppk.add_argument("file", help="template DNA FASTA (first record used)")
    ppk.add_argument("--region", required=True, help="START:END 0-based half-open")
    ppk.add_argument("--n", type=int, default=3)
    ppk.add_argument("--max-product", type=int, default=1000)
    ppk.add_argument("--primer-nm", type=float, default=25.0)
    ppk.add_argument("--na-mm", type=float, default=50.0)
    ppk.set_defaults(func=_cmd_primer_pick)

    prot = sub.add_parser("protein", help="protein property tools")
    protsub = prot.add_subparsers(dest="sub", required=True)
    ppr = protsub.add_parser("props", help="ProtParam-style properties")
    ppr.add_argument("file", nargs="?", default=None, help="protein FASTA")
    ppr.add_argument("--sequence", default=None, help="raw amino-acid string")
    ppr.set_defaults(func=_cmd_protein_props)

    pdbp = sub.add_parser("pdb", help="PDB/mmCIF structure toolkit")
    pdbsub = pdbp.add_subparsers(dest="sub", required=True)
    pst = pdbsub.add_parser("stats", help="structure summary")
    pst.add_argument("file")
    pst.set_defaults(func=_cmd_pdb_stats)
    pch = pdbsub.add_parser("chains", help="list chains (optionally residues)")
    pch.add_argument("file")
    pch.add_argument("--residues", action="store_true")
    pch.add_argument("--chain", default=None)
    pch.set_defaults(func=_cmd_pdb_chains)
    pco = pdbsub.add_parser("contacts", help="atom pairs within cutoff")
    pco.add_argument("file")
    pco.add_argument("--cutoff", type=float, required=True)
    pco.add_argument("--chain-a", default=None)
    pco.add_argument("--chain-b", default=None)
    pco.set_defaults(func=_cmd_pdb_contacts)
    pse = pdbsub.add_parser("select", help="filter atoms, write PDB")
    pse.add_argument("file")
    pse.add_argument("--chain", default=None)
    pse.add_argument("--resname", default=None)
    pse.add_argument("--names", default=None, help="comma-separated atom names")
    pse.add_argument("--record", choices=["ATOM", "HETATM"], default=None)
    pse.add_argument("--all-models", action="store_true")
    pse.add_argument("--min-bfactor", type=float, default=None)
    pse.add_argument("--out", default=None)
    pse.set_defaults(func=_cmd_pdb_select)

    msa = sub.add_parser("msa", help="Stockholm/A3M alignment toolkit")
    msasub = msa.add_subparsers(dest="sub", required=True)
    mstat = msasub.add_parser("stats", help="alignment summary (auto-detect format)")
    mstat.add_argument("file")
    mstat.set_defaults(func=_cmd_msa_stats)
    mcon = msasub.add_parser("consensus", help="majority-residue consensus")
    mcon.add_argument("file")
    mcon.add_argument("--threshold", type=float, default=0.5)
    mcon.set_defaults(func=_cmd_msa_consensus)
    mpid = msasub.add_parser("pid", help="pairwise identity between two seqs")
    mpid.add_argument("file")
    mpid.add_argument("--a", required=True)
    mpid.add_argument("--b", required=True)
    mpid.set_defaults(func=_cmd_msa_pid)
    mfil = msasub.add_parser("filter", help="drop sparse columns/sequences")
    mfil.add_argument("file")
    mfil.add_argument("--min-occupancy", type=float, default=None)
    mfil.add_argument("--min-coverage", type=float, default=None)
    mfil.add_argument("--out", default=None)
    mfil.set_defaults(func=_cmd_msa_filter)
    ma2m = msasub.add_parser("a2m", help="A3M -> match-state alignment")
    ma2m.add_argument("file")
    ma2m.add_argument("--out", default=None)
    ma2m.set_defaults(func=_cmd_msa_a2m)

    ph = sub.add_parser("phylo", help="Newick tree toolkit")
    phsub = ph.add_subparsers(dest="sub", required=True)
    ps = phsub.add_parser("stats", help="tree shape/length summary")
    ps.add_argument("file")
    ps.set_defaults(func=_cmd_phylo_stats)
    pm = phsub.add_parser("mrca", help="most recent common ancestor of leaves")
    pm.add_argument("file")
    pm.add_argument("--leaves", required=True, help="comma-separated leaf names")
    pm.set_defaults(func=_cmd_phylo_mrca)
    pd = phsub.add_parser("distance", help="path length between two leaves")
    pd.add_argument("file")
    pd.add_argument("--a", required=True)
    pd.add_argument("--b", required=True)
    pd.set_defaults(func=_cmd_phylo_distance)
    pp = phsub.add_parser("prune", help="remove leaves, collapsing lone-child nodes")
    pp.add_argument("file")
    pp.add_argument("--drop", required=True, help="comma-separated leaf names")
    pp.add_argument("--out", default=None)
    pp.set_defaults(func=_cmd_phylo_prune)

    sm = sub.add_parser("sam", help="SAM alignment toolkit (text SAM)")
    smsub = sm.add_subparsers(dest="sub", required=True)
    ss = smsub.add_parser("stats", help="mapping summary (rates, MAPQ, per-ref)")
    ss.add_argument("file")
    ss.set_defaults(func=_cmd_sam_stats)
    sf = smsub.add_parser("filter", help="filter alignments (mapped/mapq/ref/primary)")
    sf.add_argument("file")
    sf.add_argument("--mapped-only", action="store_true")
    sf.add_argument("--min-mapq", type=int, default=None)
    sf.add_argument("--rname", default=None)
    sf.add_argument("--primary-only", action="store_true")
    sf.add_argument("--out", default=None)
    sf.set_defaults(func=_cmd_sam_filter)
    sp = smsub.add_parser("pileup", help="mpileup-style per-position base counts")
    sp.add_argument("file")
    sp.add_argument("--min-mapq", type=int, default=0)
    sp.add_argument("--min-baseq", type=int, default=0)
    sp.add_argument("--rname", default=None)
    sp.add_argument("--format", choices=["json", "mpileup"], default="json")
    sp.set_defaults(func=_cmd_sam_pileup)
    sb = smsub.add_parser("to-bed", help="mapped reads to BED6 (coordinate math done)")
    sb.add_argument("file")
    sb.add_argument("--out", default=None)
    sb.set_defaults(func=_cmd_sam_to_bed)

    bd = sub.add_parser("bed", help="BED interval toolkit (0-based half-open)")
    bdsub = bd.add_subparsers(dest="sub", required=True)
    bs = bdsub.add_parser("stats", help="interval count/width/coverage summary")
    bs.add_argument("file")
    bs.set_defaults(func=_cmd_bed_stats)
    bm = bdsub.add_parser("merge", help="merge overlapping intervals per chrom")
    bm.add_argument("file")
    bm.add_argument("--out", default=None)
    bm.set_defaults(func=_cmd_bed_merge)
    bf = bdsub.add_parser("filter", help="filter by chrom/width/score")
    bf.add_argument("file")
    bf.add_argument("--chrom", default=None)
    bf.add_argument("--min-width", type=int, default=None)
    bf.add_argument("--min-score", type=float, default=None)
    bf.add_argument("--out", default=None)
    bf.set_defaults(func=_cmd_bed_filter)
    bg = bdsub.add_parser("to-gff", help="convert to GFF3 (coordinate math done)")
    bg.add_argument("file")
    bg.add_argument("--source", default="bed")
    bg.add_argument("--feature-type", default="region")
    bg.add_argument("--out", default=None)
    bg.set_defaults(func=_cmd_bed_to_gff)

    gf = sub.add_parser("gff", help="GFF3/GTF annotation toolkit")
    gfsub = gf.add_subparsers(dest="sub", required=True)
    gst = gfsub.add_parser("stats", help="feature/seqid/strand summary")
    gst.add_argument("file")
    gst.set_defaults(func=_cmd_gff_stats)
    gq = gfsub.add_parser("query", help="features overlapping a region (1-based closed)")
    gq.add_argument("file")
    gq.add_argument("--chrom", required=True)
    gq.add_argument("--start", type=int, required=True)
    gq.add_argument("--end", type=int, required=True)
    gq.add_argument("--type", default=None, help="comma-separated feature types")
    gq.set_defaults(func=_cmd_gff_query)
    gz = gfsub.add_parser("filter", help="filter by type/seqid (children kept by default)")
    gz.add_argument("file")
    gz.add_argument("--type", default=None)
    gz.add_argument("--seqid", default=None)
    gz.add_argument("--no-children", action="store_true")
    gz.add_argument("--out", default=None)
    gz.set_defaults(func=_cmd_gff_filter)
    gx = gfsub.add_parser("csv", help="flatten features to CSV")
    gx.add_argument("file")
    gx.add_argument("--out", default=None)
    gx.set_defaults(func=_cmd_gff_csv)

    q = sub.add_parser("fastq", help="FASTQ toolkit (stats, filter, trim, to-fasta)")
    qsub = q.add_subparsers(dest="sub", required=True)
    qs = qsub.add_parser("stats", help="FastQC-style read/quality summary")
    qs.add_argument("file")
    qs.add_argument("--offset", type=int, default=None, choices=[33, 64],
                    help="Phred offset; default auto (33 unless forced)")
    qs.set_defaults(func=_cmd_fastq_stats)
    qf = qsub.add_parser("filter", help="keep reads passing quality/length/N gates")
    qf.add_argument("file")
    qf.add_argument("--min-mean-phred", type=float, default=None)
    qf.add_argument("--min-len", type=int, default=None)
    qf.add_argument("--max-len", type=int, default=None)
    qf.add_argument("--max-n-frac", type=float, default=None)
    qf.add_argument("--offset", type=int, default=33, choices=[33, 64])
    qf.add_argument("--out", default=None)
    qf.set_defaults(func=_cmd_fastq_filter)
    qt = qsub.add_parser("trim", help="sliding-window 3' quality trim")
    qt.add_argument("file")
    qt.add_argument("--window", type=int, default=4)
    qt.add_argument("--min-phred", type=float, default=15.0)
    qt.add_argument("--min-len", type=int, default=36)
    qt.add_argument("--offset", type=int, default=33, choices=[33, 64])
    qt.add_argument("--out", default=None)
    qt.set_defaults(func=_cmd_fastq_trim)
    qa = qsub.add_parser("to-fasta", help="convert reads to FASTA")
    qa.add_argument("file")
    qa.add_argument("--out", default=None)
    qa.set_defaults(func=_cmd_fastq_to_fasta)

    vc = sub.add_parser("vcf", help="VCF toolkit (stats, filter, csv)")
    vcsub = vc.add_subparsers(dest="sub", required=True)
    vst = vcsub.add_parser("stats", help="variant classes, Ti/Tv, genotype counts")
    vst.add_argument("file")
    vst.set_defaults(func=_cmd_vcf_stats)
    vf = vcsub.add_parser("filter", help="filter records (PASS, qual, chrom, type)")
    vf.add_argument("file")
    vf.add_argument("--pass-only", action="store_true")
    vf.add_argument("--min-qual", type=float, default=None)
    vf.add_argument("--chrom", default=None, help="comma-separated chromosomes")
    vf.add_argument("--type", default=None,
                    help="comma-separated snp,mnp,insertion,deletion,indel,symbolic,breakend")
    vf.add_argument("--out", default=None)
    vf.set_defaults(func=_cmd_vcf_filter)
    vx = vcsub.add_parser("csv", help="flatten records to CSV")
    vx.add_argument("file")
    vx.add_argument("--sample", default=None, help="include this sample's FORMAT columns")
    vx.add_argument("--out", default=None)
    vx.set_defaults(func=_cmd_vcf_csv)

    r = sub.add_parser("report", help="lab reports, notebooks and evidence bundles")
    rsub = r.add_subparsers(dest="sub", required=True)
    rs = rsub.add_parser("splice", help="render a deepsplice assessment as a report")
    rs.add_argument("gene")
    rs.add_argument("notation")
    rs.add_argument("--transcript", default=None)
    rs.add_argument("--offline", action="store_true")
    rs.add_argument("--format", default="html", choices=["html", "md", "json"],
                    help="json emits a sha256-checksummed evidence bundle")
    rs.add_argument("--out", default=None, help="write to a file instead of stdout")
    rs.set_defaults(func=_cmd_report_splice)
    rn = rsub.add_parser("notebook", help="generate an executable .ipynb for an assessment")
    rn.add_argument("gene")
    rn.add_argument("notation")
    rn.add_argument("--transcript", default=None)
    rn.add_argument("--offline", action="store_true")
    rn.add_argument("--out", default=None, help="write the .ipynb to a file")
    rn.set_defaults(func=_cmd_report_notebook)
    rv = rsub.add_parser("validate-notebook", help="structurally validate an .ipynb file")
    rv.add_argument("file")
    rv.set_defaults(func=_cmd_report_validate_notebook)

    v = sub.add_parser("version", help="print version")
    v.set_defaults(func=_cmd_version)
    m = sub.add_parser("modules", help="list the 89 registered modules")
    m.set_defaults(func=_cmd_modules)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
