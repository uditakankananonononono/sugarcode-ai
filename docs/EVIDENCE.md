# SugarCode AI - consolidated evidence report
(regenerated from hermetic fixtures by scripts/evidence_report.py; no network)

- fixtures: 31  unique pathogenic: 2720  unique benign: 86
- canonical U2 (GT/GC donor, AG acceptor): 2414/2414 called loss
- canonical AT-AC (U12 matrices, drop 27): 16/16 called loss
- benign specificity: 85/86
- GC-donor golden: 30 cases {'vus': 10, 'pathogenic': 20} - benign searched, ZERO found
- VUS sweep: 2196 scored, 179 strong-loss (prioritization signal, NOT pathogenicity evidence)
- conflicting sweep: 977 scored, 106 strong-loss (one computational opinion, not a tiebreaker)
- exonic sweeps: donor -3..-1 1117 cases, acceptor +1 216 cases
- cryptic recall on VUS: 0 true cryptic creations in 179 strong-loss VUS and 0 in 1016 controls (honest null)
- ESRseq exonic-terminal enrichment: pathogenic mean -0.040 vs benign -0.002 - ESE hypothesis NOT supported (honest null)
