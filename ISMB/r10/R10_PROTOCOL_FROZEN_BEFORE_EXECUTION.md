# R10 fixed-code cross-study and within-study transfer protocol

Created for this R10 execution, before inspecting the R10 summary. This is a frozen analysis plan *for this run*, not prospective registration: the research team previously studied the public yeast assay, and the data source is already known. It must not be described as a blinded prospective experiment.

## Primary evaluation
- Source: the 74 GPCA/MAPPIT yeast assay-anchor panels encoded in the previously delivered `Paper3_Round3_Independent_20261111` public-derived masks. They originated in a pinned external published GitHub table but native raw-table byte access is NOT established for this run. This is a cross-species, cross-study RETROSPECTIVE transfer of the R9 algorithm, not unknown-edge generalization.
- Preserve all 74 panels, including all zero-positive panels; do not filter by winner existence. Treat each assay-anchor observation as a separate label cost, and cluster inference by anchor.
- Five *structural* Top-10 actions (AA, CN, RA, Jaccard, degree product) on the same fixed masked candidate sets. This is NOT historical NBFNet neural tail recovery.
- Primary endpoint: strict unique **action-class** winner certificates, not number of model-pair orderings. Main cap: 10 distinct informative labels per panel. R9 `adaptive_empirical` code and hyperparameters are fixed unchanged, compared pairwise to `random_informative`. A certificate must be exact under all unrestricted missing binary labels; zero false certificate is mandatory.
- Strong comparisons: R9 structural static baselines `coverage`,`disagreement`,`dopt`,`fair_contrast` and R9 other adaptive `adaptive_sparse`,`adaptive_half`; plus a new one-step exact-certificate expectation greedy comparator (declared here before this execution, not a formal reimplementation of published Active Testing). The new comparator is not treated as an author's validated innovation.
- Acquisition randomness: 100 fixed seeds (0--99), same per panel across methods. Budgets 0,3,5,8,10,15,20,30 as secondary trajectory. One fixed nomination tie order is available for yeast, so no new tie-robust claim can be made. Positive panel subgroup and assay stratification are descriptive.
- Cluster bootstrap: 5000 resamples of yeast anchor IDs for within-panel-seed averaged paired contrasts at cap=10; descriptive 95% percentile interval. Correlated repeats are not independent biological replicates.
- Falsification: if R9 adaptive_empirical fails to outperform strongest static and new greedy at cap=10 on this outside dataset, METHOD_GAIN_HOLD; if improvement rests on a few panels, still HOLD. Do not change method after seeing outcomes.

## Secondary within-study assay holdout
- Reuse pinned human HuRI structural graph and `PPI_prediction_validation_result_20210624.xls`, but use `score_assay1` as target label (R9 used `score_assay2/3` target labels). Eligible pairs are the same R8 qualification predicates: v1 measured, non-self, not already in HuRI source graph, both nodes in graph, at least 11 candidates per bait. This is NOT a new independent study; score_assay1 measured-status was previously used for eligibility.
- Same models, fixed tie seed 0, 100 acquisition seeds, cap=10, same primary pairwise contrast. Treat different assays/source graphs as non-commensurate evidence; do not pool them into a pseudo-independent mega-sample.

## Scientific boundaries
- Source graph for yeast masks was derived in the same study using YeRI edges; training-target separation and unseen-edge generalization are NOT established, and the earlier YeRI STOP is preserved.
- The R9 strategies were explored on the original human labels and cannot be called pre-registered novelty; reuse on yeast is a post hoc frozen-code stress test, not independent prospective validation.
- This analysis does not train neural models, restore missing historical neural scores, authenticate AA/G1A native chain, or fix pretarget independence.
- Claims of beating Active Testing SOTA, formal causal mechanisms, large Q1/top-conference readiness, or unconditional zero false positives are disallowed.
