# PGx Guidelines

Deterministic pharmacogenomic decision support for explicitly supplied star-allele
diplotypes. The first supported pairs are CYP2C19-clopidogrel and CYP2D6-codeine.

The rules cite CPIC publications by PMID and DOI and can retrieve each record from
PubMed live. NCBI calls are cached, throttled, retried, atomic, and offline-safe.
Unknown alleles, unsupported gene-drug pairs, and unavailable literature remain literal
`Missing` values. The module does not infer haplotypes from raw variants.

This is not prescribing software. Drug interactions (phenoconversion), indication,
organ function, assay coverage, age, regulatory restrictions, and contraindications
still require clinician/pharmacist review.
