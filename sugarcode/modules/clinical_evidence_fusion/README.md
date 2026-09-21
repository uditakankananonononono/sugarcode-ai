# Clinical Evidence Fusion

A module-local clinical genomics component that combines current NCBI ClinVar records,
focused PubMed retrieval, and the published Bayesian calibration of ACMG/AMP evidence.
It is intentionally separate from SugarCode's shared connectors.

## Why this is medically cautious

- The Bayesian number is explicitly **probability of variant pathogenicity**, not disease
  penetrance or an individual's disease risk.
- ClinVar labels are displayed beside the model, not translated back into ACMG criteria,
  which would double-count underlying evidence.
- Conflicts remain `Conflicting`; absent values remain literal `Missing` values.
- A VUS is marked non-actionable and is never promoted because a gene is disease-associated.
- PubMed results are marked unscreened. Search relevance is not treated as study quality.
- Every ClinVar record includes the stable NCBI variation URL and review status.

## Published model

Tavtigian et al., *Genetics in Medicine* (2018), "Modeling the ACMG/AMP variant
classification guidelines as a Bayesian classification framework",
DOI `10.1038/gim.2017.210`, PMID `29300386`. The implementation uses the published
likelihood-ratio series (supporting 2.08, moderate 4.3, strong 18.7, very strong 350)
and the 0.10 prior, while allowing an explicit caller-selected prior.

## Example

```python
from sugarcode.modules.clinical_evidence_fusion import evaluate_variant

report = evaluate_variant(
    "BRCA1", "NM_007294.4:c.68_69delAG",
    criteria=[
        {"code": "PVS1", "provenance": "validated loss-of-function annotation"},
        {"code": "PM2", "provenance": "population database review 2026-09-21"},
    ],
    phenotype="hereditary breast ovarian cancer",
)
```

Set `offline=True` to forbid network access. Cached responses use SHA-256 request keys;
offline responses expose cache age. `NCBI_API_KEY` enables the NCBI API-key rate tier.
