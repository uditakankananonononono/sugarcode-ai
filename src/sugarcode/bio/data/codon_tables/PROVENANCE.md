# Codon usage tables - provenance

Source: Edinburgh Genome Foundry, `codon-usage-tables` (python_codon_tables package),
fetched 2026-09-21 from:
  https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/codon-usage-tables/master/python_codon_tables/codon_usage_data/tables/<table>.csv

Files vendored verbatim (CSV, relative frequency per amino acid, RNA codons):
- e_coli_316407.csv   (E. coli K12, taxid 316407)
- h_sapiens_9606.csv  (H. sapiens, taxid 9606)
- s_cerevisiae_4932.csv (S. cerevisiae, taxid 4932)

Cross-validation against the previous in-memory "Kazusa-style" tables:
- E. coli: top synonymous codon agreement 21/21 amino acids.
- H. sapiens: 20/21 identical; the one difference is Arg, where the published
  table has an exact AGA/AGG tie (0.21 each) while the memory-built table broke
  the tie toward AGA (12.2 vs 12.0 per-thousand). Immaterial to optimization;
  memory-built tables are kept only as named legacy fallbacks.
