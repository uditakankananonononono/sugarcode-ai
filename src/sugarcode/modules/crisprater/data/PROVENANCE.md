# CRISPRater model provenance

`model.json` records the published ten-feature linear model and discrete class
thresholds from Labuhn M et al., "Refined sgRNA efficacy prediction improves
large- and small-scale CRISPR-Cas9 applications", *Nucleic Acids Research*
46(3):1375-1385 (2018), DOI
[10.1093/nar/gkx1268](https://doi.org/10.1093/nar/gkx1268), PMCID
[PMC5814880](https://pmc.ncbi.nlm.nih.gov/articles/PMC5814880/).

The machine-readable coefficients were cross-checked against
`crisprVerse/crisprScore` `R/getCrispraterScores.R`, live-verified at commit
`cbd6f9f60dc7fb50d14b90485b9561d582caf21e` on 2026-09-21. The immutable raw
source was 3,169 bytes, SHA-256
`82cf531f2deade8f7b3a106c4d85ca857fc9546e12b1b17fb07da48dbd5aa3f8`:

<https://raw.githubusercontent.com/crisprVerse/crisprScore/cbd6f9f60dc7fb50d14b90485b9561d582caf21e/R/getCrispraterScores.R>

The primary paper defines low as score <0.56, medium as 0.56-0.74 inclusive,
and high as >0.74. It states that the model was fit to 426 sgRNAs and is best
used as a discrete exclusion tool.

## Implementation note and limits

The upstream R port uses accidental unqualified matrix indexing in four OR
features (`mat[3]`, etc.), which mixes rows for batch inputs. This implementation
uses the intended row-local, one-based positions named in that source and
therefore gives batch-invariant results.

CRISPRater does not model PAM choice, genome-wide specificity, chromatin,
cell type, delivery, or guide secondary structure. Those fields are Missing,
not inferred. A score is a model output, not a measured editing probability.
