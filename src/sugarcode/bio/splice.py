"""Real human splice-site PWMs learned from RefSeqGene records.

Data: 1,170 GT-AG splice junctions extracted live from NCBI RefSeqGene
records for 29 clinically relevant genes (title-verified accessions) (see data/splice_sites/PROVENANCE.md).
Donor window: 9 nt (3 exonic + 6 intronic). Acceptor window: 15 nt
(14 intronic + 1 exonic). Learned consensus: AAG|GTAAGT and (T)nCAG|G,
matching the published mammalian consensus.
"""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

from .pwm import log_odds_matrix

DATA = Path(__file__).parent / "data" / "splice_sites"


class SpliceDataMissing(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load(name: str) -> list[dict[str, float]]:
    p = DATA / name
    if not p.exists():
        raise SpliceDataMissing(f"missing vendored splice data: {p}")
    payload = json.loads(p.read_text())
    return payload["pwm"]


def donor_pwm() -> list[dict[str, float]]:
    return _load("donor_pwm.json")


def acceptor_pwm() -> list[dict[str, float]]:
    return _load("acceptor_pwm.json")


def donor_lod() -> list[dict[str, float]]:
    return log_odds_matrix(donor_pwm())


def acceptor_lod() -> list[dict[str, float]]:
    return log_odds_matrix(acceptor_pwm())


def u12_atac_donor_lod() -> list[dict[str, float]]:
    """AT-AC (U12 minor spliceosome) donor log-odds: learned from 139 human
    gold U12 AT-AC introns (intronIC training index, see PROVENANCE)."""
    return log_odds_matrix(_load("u12_atac_donor_pwm.json"))


def u12_atac_acceptor_lod() -> list[dict[str, float]]:
    """AT-AC (U12) acceptor log-odds from 139 human gold introns. Column 14
    (first exonic base) is a uniform placeholder - the export has no
    downstream flank (PROVENANCE)."""
    return log_odds_matrix(_load("u12_atac_acceptor_pwm.json"))


def u12_gtag_donor_lod() -> list[dict[str, float]]:
    """GT-AG U12 (minor spliceosome) donor log-odds: 361 human gold U12
    GT-AG introns (intronIC training index, PROVENANCE). Consensus
    RTATCCTTT - distinct from the U2 GT-AG consensus."""
    return log_odds_matrix(_load("u12_gtag_donor_pwm.json"))


def u12_gtag_acceptor_lod() -> list[dict[str, float]]:
    """GT-AG U12 acceptor log-odds: 361 human gold introns. U12 acceptors
    lack the U2 polypyrimidine tract. Column 14 is a uniform placeholder."""
    return log_odds_matrix(_load("u12_gtag_acceptor_pwm.json"))


def n_sites() -> dict[str, int]:
    return {"donor": json.loads((DATA / "donor_pwm.json").read_text())["n_sites"],
            "acceptor": json.loads((DATA / "acceptor_pwm.json").read_text())["n_sites"]}


# --- live splice assessment (drop 25): RefSeqGene junction maps -------------

from . import entrez as _entrez
from .genbank import parse_genbank as _parse_gb, revcomp as _rc, transcript_exons as _texons


def refseqgene_accession(gene: str) -> str | None:
    """Title-verified accession from the vendored harvest metadata."""
    meta = DATA / "harvest_meta.json"
    if not meta.exists():
        raise SpliceDataMissing(f"missing {meta}")
    m = json.loads(meta.read_text())
    for g in m["genes"]:
        if g["gene"] == gene.upper():
            return g["accession"]
    # map-only extensions (drop 35): title-verified RefSeqGene records for
    # junction MAPS only - deliberately NOT in the PWM training set, so the
    # matrices and every golden calibrated on them are untouched
    for g in m.get("map_only_genes", []):
        if g["gene"] == gene.upper():
            return g["accession"]
    return None


def junction_map(gene: str, offline: bool = False) -> dict:
    """Canonical-transcript splice junction map for a gene from its
    RefSeqGene record: donor/acceptor windows keyed by cDNA junction
    position, plus the full record sequence for context scans.

    Canonical = CDS with the most spans; internal CDS span boundaries ARE
    the splice junctions (UTR trimming differs only at terminal exons).
    """
    acc = refseqgene_accession(gene)
    if not acc:
        return {"status": "no RefSeqGene junction map for this gene", "gene": gene}
    txt = _entrez._get("efetch.fcgi", {"db": "nuccore", "id": acc,
                                       "rettype": "gb", "retmode": "text"},
                       offline=offline).decode()
    gb = _parse_gb(txt); seq = gb["sequence"]
    cds = max((f for f in gb["features"] if f["key"] == "CDS" and len(f["spans"]) >= 2),
              key=lambda c: len(c["spans"]), default=None)
    if not cds:
        return {"status": "no multi-exon CDS in record", "gene": gene, "accession": acc}
    strand = cds["strand"]
    spans = _texons(cds)

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

    donors, acceptors = {}, {}
    for (a, b), (c, d) in zip(spans, spans[1:]):
        if strand == 1:
            donors[cdna_of(b)] = seq[b-3:b+6]
            acceptors[cdna_of(c)] = seq[c-15:c]
        else:
            donors[cdna_of(a)] = _rc(seq[a-7:a+2])
            acceptors[cdna_of(d)] = _rc(seq[d-1:d+14])
    exons = []
    n = 0
    for a, b in spans:
        ln = b - a + 1
        exons.append({"cdna_start": n + 1, "cdna_end": n + ln, "length": ln})
        n += ln
    return {"status": "ok", "gene": gene, "accession": acc,
            "donors": {k: v for k, v in donors.items() if k is not None},
            "acceptors": {k: v for k, v in acceptors.items() if k is not None},
            "sequence": seq, "cdna_of": cdna_of, "strand": strand,
            "cds_spans": spans, "exons": exons,
            "source": f"NCBI RefSeqGene {acc} ({'cache' if offline else 'live'})"}


def gc_donor_lod() -> list[dict[str, float]]:
    """GC-AG donor log-odds: the GT donor matrix with the +2 column T<->C
    swapped. GC donors are ~0.6% of junctions (7 observed in our harvest), too
    few for an independent matrix; published analyses (Burset et al. 2000)
    show the GC-donor consensus mirrors the GT consensus with C at +2.
    Cross-checked: our 5 observed GC-donor windows score 0.83-1.00 under this
    matrix vs 0.36-0.61 under the GT matrix. Approximation, labeled as such.
    """
    pwm = donor_pwm()
    swapped = [dict(col) for col in pwm]
    c = pwm[4]
    swapped[4] = {"A": c["C"], "C": c["T"], "G": c["G"], "T": c["A"]}
    return log_odds_matrix(swapped)


def utr_junction_map(gene: str, offline: bool = False) -> dict:
    """5'-UTR-aware junction map (drop 33): junction windows keyed by c.
    number INCLUDING negative (5'-UTR) positions, built from the canonical
    transcript's mRNA exons with c.1 anchored at the paired CDS start.

    Motivation: the CDS-only map (junction_map) cannot see UTR introns -
    GJB2's CDS is a single exon, but its 5' UTR carries one intron, the
    site of c.-23+1G>A / c.-22-2A>C. Canonical CDS = most spans (as
    junction_map); its mRNA is picked by maximal genomic overlap with the
    CDS (span-tuple equality fails on UTR-trimmed terminal exons - the
    drop-26 lesson). 3'-UTR introns (c.*N numbering) are NOT keyed yet:
    boundaries landing past the CDS end are skipped and named in the
    source note.
    """
    acc = refseqgene_accession(gene)
    if not acc:
        return {"status": "no RefSeqGene junction map for this gene", "gene": gene}
    txt = _entrez._get("efetch.fcgi", {"db": "nuccore", "id": acc,
                                       "rettype": "gb", "retmode": "text"},
                       offline=offline).decode()
    gb = _parse_gb(txt); seq = gb["sequence"]
    cds = max((f for f in gb["features"] if f["key"] == "CDS"),
              key=lambda c: sum(b - a for a, b in c["spans"]), default=None)
    if not cds:
        return {"status": "no CDS in record", "gene": gene, "accession": acc}
    strand = cds["strand"]
    cds_spans = _texons(cds)
    cds_start = cds_spans[0][0] if strand == 1 else cds_spans[0][1]
    cds_end = cds_spans[-1][1] if strand == 1 else cds_spans[-1][0]

    def overlap(f):
        return sum(max(0, min(b, cb) - max(a, ca) + 1)
                   for a, b in f["spans"] for ca, cb in cds["spans"])

    mrnas = [f for f in gb["features"] if f["key"] == "mRNA"]
    mrna = max(mrnas, key=overlap, default=None)
    if not mrna or overlap(mrna) == 0:
        return {"status": "no mRNA overlapping the CDS", "gene": gene, "accession": acc}
    tx = mrna["qualifiers"].get("transcript_id", "")
    exons = _texons(mrna)

    # c. numbering is EXONIC: walk exons in transcription order and number
    # each base by its walked index relative to the CDS-start base (genomic
    # distance would wrongly count introns - first pass here fixes that).
    cds_len = sum(b - a + 1 for a, b in cds_spans)
    utr_len = 0
    walked = 0
    for a, b in exons:
        ln = b - a + 1
        edge_start = a if strand == 1 else b   # first base, tx orientation
        edge_end = b if strand == 1 else a     # last base, tx orientation
        before = ((strand == 1 and edge_end < cds_start) or
                  (strand == -1 and edge_end > cds_start))
        if before:
            utr_len += ln
        elif ((strand == 1 and edge_start < cds_start <= edge_end) or
              (strand == -1 and edge_end > cds_start >= edge_start)):
            utr_len += abs(cds_start - edge_start)  # partial: UTR part only
        walked += ln

    def cnum(w):
        """c. number of the base at walked exonic index w (0-based)."""
        if w < utr_len:
            return -(utr_len - w)
        if w >= utr_len + cds_len:
            return None                          # 3' UTR: c.*N unsupported
        return w - utr_len + 1

    donors, acceptors, exon_rows = {}, {}, []
    walked = 0
    for i, (a, b) in enumerate(exons):
        ln = b - a + 1
        exon_rows.append({"cdna_start": cnum(walked),
                          "cdna_end": cnum(walked + ln - 1), "length": ln})
        if i + 1 < len(exons):
            na, nb = exons[i + 1]
            d_key = cnum(walked + ln - 1)
            a_key = cnum(walked + ln)
            if d_key is not None:
                donors[d_key] = (seq[b-3:b+6] if strand == 1
                                 else _rc(seq[a-7:a+2]))
            if a_key is not None:
                acceptors[a_key] = (seq[na-15:na] if strand == 1
                                    else _rc(seq[nb-1:nb+14]))
        walked += ln
    skipped_3utr = sum(1 for e in exon_rows
                       if e["cdna_start"] is None or e["cdna_end"] is None)
    src = (f"NCBI RefSeqGene {acc} ({'cache' if offline else 'live'}), "
           f"mRNA {tx} exons with c.1 at the paired CDS start")
    if skipped_3utr:
        src += f"; {skipped_3utr} 3'-UTR exon(s) unnumbered (c.*N unsupported)"
    return {"status": "ok", "gene": gene, "accession": acc, "transcript": tx,
            "donors": {k: v for k, v in donors.items() if k is not None},
            "acceptors": {k: v for k, v in acceptors.items() if k is not None},
            "sequence": seq, "strand": strand, "exons": exon_rows,
            "source": src}


# --- transcript-isoform junction maps (drop 27): cDNA-record alignment ------

def _segment_cdna(cdna: str, gseq: str, anchor: int = 30) -> list[list[int]] | None:
    """Segment a cDNA into genomic exon intervals by exact-match anchoring.

    Walks the cDNA; each 30-nt anchor is found in the genomic sequence at or
    after the previous exon's end (monotonic), then extended exactly. Runs
    separated by SMALL equal gaps on both axes are version mismatches inside
    one exon and are merged; large genomic gaps are introns. Returns
    [[cdna_start0, genomic_start0, length], ...] or None when coverage < 90%.
    """
    spans: list[list[int]] = []
    cpos, gcur, n = 0, 0, len(cdna)
    while cpos < n:
        g = gseq.find(cdna[cpos:cpos + anchor], gcur)
        if g < 0:
            cpos += 1          # unaligned cDNA base (record-version mismatch)
            continue
        ln = 0
        while cpos + ln < n and g + ln < len(gseq) and cdna[cpos + ln] == gseq[g + ln]:
            ln += 1
        spans.append([cpos, g, ln])
        cpos += ln
        gcur = g + ln
    if not spans or sum(s[2] for s in spans) < 0.9 * n:
        return None
    merged = [spans[0]]
    for s in spans[1:]:
        prev = merged[-1]
        c_gap = s[0] - (prev[0] + prev[2])
        g_gap = s[1] - (prev[1] + prev[2])
        if 0 < c_gap <= 10 and c_gap == g_gap:
            prev[2] = s[0] + s[2] - prev[0]      # same exon, version mismatch
        else:
            merged.append(s)
    return merged


def _refine_junctions(cds_seq: str, target: str, seg: list[list[int]],
                      donor_lod_m, acceptor_lod_m) -> list[list[int]]:
    """Resolve splice-boundary ambiguity left by exact-match extension.

    Extension overshoots a few nt when exonic and intronic sequences agree
    across the boundary (segments showed +1..3 nt drift vs annotation on
    SCN1A). The cDNA boundary p between segments i and i+1 is re-chosen over
    every position consistent with BOTH exact matches; candidates are ranked
    by terminal-dinucleotide class (canonical GT/GC/AT donor + AG/AC
    acceptor beats non-canonical) then by GT-AG PWM fit. This is how
    aligners snap splice boundaries; the shared-exon cross-check in
    cdna_junction_map verifies the result against the record annotation.
    """
    def cls_rank(d, a):
        dr = {"GT": 3, "GC": 2, "AT": 1}.get(d[3:5], 0)
        ar = {"AG": 3, "AC": 1}.get(a[12:14], 0)
        return min(dr, ar)

    def pwm_fit(d, a):
        from .pwm import normalized_score
        return normalized_score(d, donor_lod_m) + normalized_score(a, acceptor_lod_m)

    out = [list(s) for s in seg]
    for i in range(len(out) - 1):
        si0, gi0, sil = out[i]
        sj0, gj0, sjl = out[i + 1]
        si_end = si0 + sil                      # cDNA pos after exon i (exclusive)
        candidates = []
        for p in range(max(si0, sj0 - 40), min(si_end + 40, sj0 + sjl) + 1):
            ge = gi0 + (p - si0)                # genomic end of exon i (exclusive)
            gs = gj0 + (p - sj0)                # genomic start of exon i+1
            if gs <= ge or gs - ge > 2_000_000:
                continue
            if p > si_end and cds_seq[si_end:p] != target[gi0 + sil:ge]:
                continue
            if p < si_end and cds_seq[p:si_end] != target[ge:gi0 + sil]:
                continue
            if p < sj0 and cds_seq[p:sj0] != target[gs:gj0]:
                continue
            if p > sj0 and cds_seq[sj0:p] != target[gj0:gs]:
                continue
            d = target[ge - 3:ge + 6]
            a = target[gs - 14:gs + 1]
            if len(d) != 9 or len(a) != 15:
                continue
            candidates.append((cls_rank(d, a), pwm_fit(d, a), p, ge, gs))
        if not candidates:
            continue                            # leave segment as-is; cross-check will catch
        candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
        _, _, p, ge, gs = candidates[0]
        out[i][2] = p - si0                     # exon i now ends at p
        out[i + 1][0] = p                       # exon i+1 starts at p
        out[i + 1][1] = gj0 + (p - sj0)
        out[i + 1][2] = (sj0 + sjl) - p
    return out


def cdna_junction_map(gene: str, transcript: str, offline: bool = False) -> dict:
    """Junction map for a SPECIFIC transcript, even one the RefSeqGene record
    does not annotate: the CDS region of the transcript's own cDNA record is
    aligned to the gene's RefSeqGene genomic sequence by exact-match exon
    segmentation, so cDNA coordinates match ClinVar citations on THAT
    transcript (c.1 = first CDS base).

    Motivation (drop 26/27): SCN1A ClinVar cites NM_001165963, whose 33-nt
    alternative coding exon is absent from NG_011906.1's NM_006920.4
    annotation. Whole-cDNA alignment fails: RefSeq UTR leaders are curated
    and do not match the genomic record (NM_001165963.2's first 479 nt are
    absent from NG_011906.1), so segmentation anchors on the CDS only;
    coding exons align verbatim (all 26 NM_006920 exons are verbatim in both
    records). Fails loudly when the CDS does not align.
    """
    acc = refseqgene_accession(gene)
    if not acc:
        return {"status": "no RefSeqGene junction map for this gene", "gene": gene}
    gtxt = _entrez._get("efetch.fcgi", {"db": "nuccore", "id": acc,
                                        "rettype": "gb", "retmode": "text"},
                        offline=offline).decode()
    gseq = _parse_gb(gtxt)["sequence"]
    ctxt = _entrez._get("efetch.fcgi", {"db": "nuccore", "id": transcript,
                                        "rettype": "gb", "retmode": "text"},
                        offline=offline).decode()
    cgb = _parse_gb(ctxt)
    cdna = cgb["sequence"]
    cds_feats = [f for f in cgb["features"] if f["key"] == "CDS"]
    if not cds_feats:
        return {"status": f"no CDS feature in {transcript}", "gene": gene}
    cdsf = cds_feats[0]
    cds_a, cds_b = cdsf["spans"][0][0], cdsf["spans"][-1][1]   # cDNA 1-based
    cds_seq = cdna[cds_a - 1:cds_b]

    strand, target = 1, gseq
    seg = _segment_cdna(cds_seq, gseq)
    if seg is None:
        strand, target = -1, _rc(gseq)
        seg = _segment_cdna(cds_seq, target)
    if seg is None:
        return {"status": f"CDS of {transcript} does not align to {acc} (<90% coverage)",
                "gene": gene}
    if seg[0][0] > 3:
        return {"status": f"CDS start of {transcript} does not align to {acc} "
                          f"(first aligned base at CDS offset {seg[0][0]}) - refusing "
                          "to guess c. numbering", "gene": gene}
    cov = sum(s[2] for s in seg) / len(cds_seq)
    seg = _refine_junctions(cds_seq, target, seg, donor_lod(), acceptor_lod())

    # cross-check against the record's annotated mRNA: boundaries the
    # transcript SHARES with the annotation must match exactly; boundaries
    # falling inside our exon interiors are alternative splice events in the
    # annotation's transcript (or vice versa), not errors. SCN1A proof case:
    # NG_011906.1 annotates NM_006920's exon 11 donor at 34938, which sits
    # INSIDE NM_001165963's exon 11 (alternative 3' donor 33 nt downstream
    # at 34971; both are real GT sites, verified on the sequence).
    ggb = _parse_gb(gtxt)
    alt_boundaries = []
    mrna_exons = []
    for f in ggb["features"]:
        if f["key"] == "mRNA":
            mrna_exons = _texons(f)
            break
    ex_spans_chk = []
    for c0, t0, ln in seg:
        a = t0 + 1 if strand == 1 else len(gseq) - (t0 + ln) + 1
        b = t0 + ln if strand == 1 else len(gseq) - t0
        ex_spans_chk.append((a, b))
    if mrna_exons:
        my_bounds = {(k, v) for (a, b) in ex_spans_chk[:-1] for k, v in [("end", b)]}
        my_bounds |= {(k, v) for (a, b) in ex_spans_chk[1:] for k, v in [("start", a)]}
        ann_bounds = [("end", b) for (a, b) in mrna_exons[:-1]] + \
                     [("start", a) for (a, b) in mrna_exons[1:]]
        for kind, pos in ann_bounds:
            if any(a < pos < b for (a, b) in ex_spans_chk):
                alt_boundaries.append({"annotated": f"{kind}@{pos}",
                                       "note": "inside an aligned exon - alternative "
                                               "splice boundary (not an error)"})
            elif (kind, pos) not in my_bounds and any(
                    a - 50 <= pos <= b + 50 for (a, b) in ex_spans_chk):
                alt_boundaries.append({"annotated": f"{kind}@{pos}",
                                       "note": "near an aligned boundary - alternative "
                                               "splice-site usage"})
    # dinucleotide sanity on the final junction set (built below) happens
    # after construction; alt boundaries are reported, never fatal.

    def gpos(t0):  # target(plus-oriented) 0-based -> genomic 1-based
        return t0 + 1 if strand == 1 else len(gseq) - t0

    donors, acceptors = {}, {}
    exons_g = []   # plus-strand genomic spans of CDS exon fragments
    for c0, t0, ln in seg:
        if strand == 1:
            exons_g.append((t0 + 1, t0 + ln))
        else:
            exons_g.append((len(gseq) - (t0 + ln) + 1, len(gseq) - t0))
    for i in range(len(seg) - 1):
        key_d = seg[i][0] + seg[i][2]               # c. of exon-end coding base
        key_a = seg[i + 1][0] + 1                   # c. of next exon's first coding base
        a, b = exons_g[i]
        c, d = exons_g[i + 1]
        if strand == 1:
            donors[key_d] = gseq[b - 3:b + 6]
            acceptors[key_a] = gseq[c - 15:c]
        else:
            donors[key_d] = _rc(gseq[a - 7:a + 2])
            acceptors[key_a] = _rc(gseq[d - 1:d + 14])

    if donors:
        good_d = sum(1 for v in donors.values() if v[3:5] in ("GT", "GC", "AT"))
        good_a = sum(1 for v in acceptors.values() if v[12:14] in ("AG", "AC"))
        if good_d / len(donors) < 0.9 or (acceptors and good_a / len(acceptors) < 0.9):
            return {"status": f"aligned junctions fail dinucleotide sanity "
                              f"({good_d}/{len(donors)} donors GT/GC/AT, "
                              f"{good_a}/{len(acceptors)} acceptors AG/AC) - "
                              "refusing to guess", "gene": gene}

    exons = []
    n = 0
    for (a, b) in exons_g:
        ln = b - a + 1
        exons.append({"cdna_start": n + 1, "cdna_end": n + ln, "length": ln})
        n += ln
    out_extra = {"alternative_splice_boundaries": alt_boundaries} if alt_boundaries else {}
    return {"status": "ok", "gene": gene, "accession": acc, "transcript": transcript,
            **out_extra,
            "donors": donors, "acceptors": acceptors,
            "sequence": gseq, "strand": strand, "cds_spans": exons_g, "exons": exons,
            "coverage": round(cov, 4),
            "source": (f"NCBI {transcript} CDS aligned to RefSeqGene {acc} "
                       f"({'cache' if offline else 'live'}; exact-match CDS segmentation)")}
