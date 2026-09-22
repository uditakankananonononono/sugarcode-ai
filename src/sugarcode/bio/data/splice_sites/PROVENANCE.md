# Splice-site PWM provenance

Donor/acceptor position weight matrices learned from **real human splice
junctions**, harvested from NCBI RefSeqGene (NG_) GenBank records via
E-utilities, parsed with `scripts/gb_parse.py`, extracted with
`scripts/harvest_splice.py`. First harvest 2026-09-21; **corrected re-harvest
2026-09-22** after the accession picker was caught taking wrong-locus records
(see below).

## Method
- Record resolution: `esearch nuccore "<GENE>[gene] AND refseqgene[filter]"`
  then the NG_ accession whose esummary **title names the gene** (the raw
  gene query also returns neighboring loci).
- For every annotated mRNA feature (join of exons) in each record, donor
  (9 nt: 3 exonic + 6 intronic) and acceptor (15 nt: 14 intronic + 1 exonic)
  windows were extracted in transcript orientation for every intron.
- Canonical filter: donor +1/+2 = GT, acceptor -2/-1 = AG.
- Result: 1,213 junctions total; 1,204 GT donors (99.3%), 1,176 AG acceptors;
  1,170 GT-AG junctions retained. PWMs built from **366 unique donor and 710
  unique acceptor windows** (pseudocount 0.5).
- Cross-validation: learned donor consensus `AAG|GTAAGT` and acceptor
  consensus `(T)11CAG|G` match the published mammalian consensus
  (MAG|GTRAGT / (Y)nNYAG|G). GC donors (7) and AT-AC introns (2) observed
  and excluded from the PWM, as documented in junctions.tsv.

## Wrong-record catch (2026-09-22)
The first harvest picked the first NG_ hit per gene query. Title verification
caught six mislabeled records: BRCA2 had ZAR1L NG_017006.2 (now NG_012772.3),
PTEN NG_033079.1 (now NG_007466.2), APC NG_016323.1 (now NG_008481.4),
ATM NG_054724.1 (now NG_009830.1), TSC1 NG_034227.1 (now NG_012386.1),
TSC2 had PKD1's shared record NG_008617.1 (now NG_005895.1). All junctions
were still real human splice sites, but gene labels were wrong for six rows;
the corrected PWMs differ slightly (1,170 vs 1,215 GT-AG sites) and the
BRCA1/CFTR goldens were re-verified against them.

## Records used (title-verified)
BRCA1 NG_005905.2, BRCA2 NG_012772.3, TP53 NG_017013.2, MLH1 NG_007109.2,
MSH2 NG_007110.2, MSH6 NG_007111.1, PMS2 NG_008466.1, CFTR NG_016465.4,
PAH NG_008690.2, PTEN NG_007466.2, APC NG_008481.4, ATM NG_009830.1,
RB1 NG_009009.1, NF1 NG_009018.1, LDLR NG_009060.1, HBB NG_059281.1,
SCN1A NG_011906.1, MECP2 NG_007107.3, CHEK2 NG_008150.2, PALB2 NG_007406.1,
MUTYH NG_008189.1, KCNQ1 NG_016178.2 (no mRNA features in current record),
GJB2 NG_008358.1, F8 NG_011403.2, DMD NG_012232.1, MYH7 NG_007884.1,
PKD1 NG_008617.1, TSC1 NG_012386.1, TSC2 NG_005895.1, VHL NG_008212.3.

## Caveats
- Windows come from annotated transcripts of 29 genes: broad coverage of
  canonical U2 splicing, not a genome-wide set. Cryptic/noncanonical sites
  and minor-spliceosome (AT-AC) introns are intentionally out of scope.
- RefSeqGene records annotate specific transcript versions (e.g. BRCA1
  NM_007294.3); cDNA numbering for variant mapping uses the CDS annotated
  on the same record (NP_009225.1, 5,592 bp CDS = 1,863 aa + stop).

## U12 (minor spliceosome) matrices (drop 27)
Source: Larue & Roy (2023, NAR gkad797) intronIC v3 training index,
`training_index/training_data_index.tsv.gz` (github.com/glarue/intronIC,
mirroring FigShare DOI 10.6084/m9.figshare.20483655; license GPL-3.0+ -
only the splice-site sequence facts are vendored here). Human
(species_full=homo_sapiens, label=u12) gold U12 introns: 361 GT-AG + 139
AT-AC (2 GC-AG excluded). Donor window = last 3 nt of `up_flank` + first
6 nt of the intron; acceptor = last 14 INTRONIC nt. The export carries no
downstream exon flank, so acceptor column index 14 (first exonic base) is
a uniform 0.25 column - labeled, not guessed. Learned consensuses match
the literature: U12 donor RTATCCTTT (both subtypes), AT-AC acceptor
(T)nCCTTRCAC. Harvest: scripts/harvest_u12.py (2026-09-22).
