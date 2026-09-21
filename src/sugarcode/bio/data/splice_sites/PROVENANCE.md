# Splice-site PWM provenance

Donor/acceptor position weight matrices learned from **real human splice
junctions**, harvested 2026-09-21 from NCBI RefSeqGene (NG_) GenBank records
via E-utilities (`esearch nuccore "<GENE>[gene] AND refseqgene[filter]"`,
`efetch rettype=gb`), parsed with `scripts/gb_parse.py`, extracted with
`scripts/harvest_splice.py`.

## Method
- For every annotated mRNA feature (join of exons) in each record, donor
  (9 nt: 3 exonic + 6 intronic) and acceptor (15 nt: 14 intronic + 1 exonic)
  windows were extracted in transcript orientation for every intron.
- Canonical filter: donor positions +1/+2 = GT, acceptor -2/-1 = AG.
- Result: 1,260 junctions total; 1,251 GT donors (99.3%), 1,221 AG acceptors;
  1,215 GT-AG junctions retained. PWMs built from **329 unique donor and 594
  unique acceptor windows** (pseudocount 0.5).
- Cross-validation: learned donor consensus `AAG|GTAAGT` and acceptor
  consensus `(T)11CAG|G` match the published mammalian consensus
  (MAG|GTRAGT / (Y)nNYAG|G). GC donors (7) and AT-AC introns (2) observed
  and excluded from the PWM, as documented in junctions.tsv.

## Records used (accession resolved live)
BRCA1 NG_005905.2, BRCA2 NG_017006.2, TP53 NG_017013.2, MLH1 NG_007109.2,
MSH2 NG_007110.2, MSH6 NG_007111.1, PMS2 NG_008466.1, CFTR NG_016465.4,
PAH NG_008690.2, APC NG_016323.1, ATM NG_054724.1, RB1 NG_009009.1,
NF1 NG_009018.1, LDLR NG_009060.1, HBB NG_059281.1, SCN1A NG_011906.1,
MECP2 NG_007107.3, CHEK2 NG_008150.2, PALB2 NG_007406.1, MUTYH NG_008189.1,
GJB2 NG_008358.1, F8 NG_011403.2, DMD NG_012232.1, MYH7 NG_007884.1,
PKD1+TSC2 NG_008617.1 (adjacent genes share one record), TSC1 NG_034227.1,
VHL NG_008212.3.
PTEN (NG_033079.1) and KCNQ1 (NG_016178.2) yielded no mRNA features in the
current record annotation and contribute nothing.

## Caveats
- Windows come from annotated transcripts of 28 genes: broad coverage of
  canonical U2 splicing, not a genome-wide set. Cryptic/noncanonical sites
  and minor-spliceosome (AT-AC) introns are intentionally out of scope.
- RefSeqGene records annotate specific transcript versions (e.g. BRCA1
  NM_007294.3); cDNA numbering for variant mapping uses the CDS annotated
  on the same record (NP_009225.1, 5,592 bp CDS = 1,863 aa + stop).
