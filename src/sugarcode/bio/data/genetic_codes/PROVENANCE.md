# Genetic code tables - provenance

Source: NCBI genetic codes (https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi),
as vendored inside Biopython 1.88 `Bio.Data.CodonTable.unambiguous_dna_by_id`.
Extracted PROGRAMMATICALLY on 2026-09-24 - the JSON was written by code reading the
Biopython tables, never retyped by hand.

Tables included (NCBI transl_table ids):
- 1:  The Standard Code
- 2:  The Vertebrate Mitochondrial Code
- 4:  The Mold, Protozoan, and Coelenterate Mitochondrial Code and the
      Mycoplasma/Spiroplasma Code
- 11: The Bacterial, Archaeal and Plant Plastid Code

Per table: forward (64-minus-stop codon -> amino acid map), stops, starts
(NCBI "Starts" row: codons annotated as valid initiation sites; table 11
includes the alternative GTG/TTG/CTG/ATT/ATC/ATA starts used by bio.orf's
--starts table mode).
