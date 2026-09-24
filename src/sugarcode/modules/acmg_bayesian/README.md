# ACMG Bayesian

Bayesian ACMG/AMP sequence-variant classification from Tavtigian et al. 2018
(Genet Med 20:1054-1060, DOI 10.1038/gim.2017.210, PMID 29300386, free text
PMC6336098), with an optional live ClinVar / PubMed context layer.

## Model

- Odds of pathogenicity: very strong 350, exponent X = 2, so
  OP = 350^(1/2^k): strong 18.708, moderate 4.3253, supporting 2.0797.
  Benign criteria use the reciprocal odds. Prior 0.10.
- Evidence is carried as integer points (supporting 1, moderate 2, strong 4,
  very strong 8; benign negative), OP = 350^(points/8), so there is no
  floating-point drift.
- Bands at prior 0.10: Pathogenic >= 10 points (posterior > 0.99), Likely
  pathogenic 6-9, VUS 0-5, Likely benign -1 to -6, Benign <= -7. Six points
  is 350^0.75 = 80.9, which the paper treats as the "exact odds required to
  convert a Prior_P of 0.10 to a Post_P of 0.90" and prints as 0.900 for all
  five ACMG likely-pathogenic rules; a hard float cutoff would wrongly call
  those VUS.
- BA1 is a stand-alone benign override outside the math (the paper excludes it
  from the Bayesian model). The label is Benign; the posterior of the other
  evidence is still reported, and pathogenic evidence next to BA1 is flagged.
- Strength changes (e.g. PM2 at supporting) are accepted and recorded.
  Unknown codes or strengths are rejected visibly.
- A caller-chosen prior is allowed; labels then use the paper's posterior bands
  and the result says the paper calibrated at 0.10.

The posterior is a probability that the variant is pathogenic, not penetrance
or a person's disease risk. Research and clinician decision support only.

## Fidelity

`tests/test_acmg_bayesian.py` reproduces every combining-rule row of the
paper's Table 2 and the mixed-evidence rows of Table 3 (combined odds and
posterior within one unit of the printed last digit), including all five
likely-pathogenic rules at 0.900.

## Optional ClinVar / PubMed lookup

```python
from sugarcode.modules.acmg_bayesian import bayesian_acmg, evaluate_variant

bayesian_acmg(["PS1", "PM1"])["classification"]   # 'Likely pathogenic'

report = evaluate_variant("BRCA1", "NM_007294.4:c.68_69delAG",
                          criteria=["PVS1", "PS3", "PM2"])
```

ClinVar and PubMed results sit beside the score and are never turned into ACMG
codes (that would double-count evidence). HGVS is normalized to ClinVar style
(`c.68_69delAG` -> `c.68_69del`); only records whose title carries the exact
variant are summarized, and unrelated hits from ClinVar's text search are kept
but not counted. Conflicts stay `Conflicting`, absent data stays `Missing`.
`offline=True` uses only the local cache. `NCBI_API_KEY` (free) raises the
NCBI rate limit; nothing paid is needed.
