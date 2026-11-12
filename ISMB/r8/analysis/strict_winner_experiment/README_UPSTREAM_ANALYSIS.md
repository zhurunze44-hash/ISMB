# Reproduce the corrected public human Y2H strict-winner audit

This package executes a retrospective label-disclosure experiment on complete,
source-only classical structural-model scores. It does not reconstruct Paper3's
missing historical neural ranking tails, train a neural model, or run a new
biological experiment.

## Native inputs

The `input/` directory contains exact pinned bytes from
`spxuw/PPI-Prediction-Project`, commit
`5e2f7beb596987de7b97a0cf48900915a64aad99`:

- `Interactomes/HuRI.csv`, Git blob
  `46fec1d9554d07f165312313f1e5f9b6156e8aa3`.
- `Experimental validation/PPI_prediction_validation_result_20210624.xls`, Git blob
  `7fb2a36b96b87e47cf8178544286d9db3c0e7e3e`. Despite its extension, this is TSV text.

Input Git blob hashes are rechecked at every execution. The producer rejects
duplicates, unknown measurement labels, source-graph overlap, and unscoreable
candidates according to the pinned qualification contract. Measurement absence
is never converted to a measured negative. Eligibility depends on measurement
presence, not the positive outcome; all qualified zero-HC panels remain included.

## Run

Python 3, NumPy and SciPy (with `scipy.optimize.milp`) are required.

```bash
python3 reanalyze_strict_winners.py --tie-seeds 0,1,2,3,4,5 --acquisition-seeds 100
python3 summarize_results.py
```

The default execution recomputes all structural scores, runs 84 exhaustive
completion checks, solves the exact offline minimum-certificate problems, and
executes balanced acquisition policies. Its output replaces the `results/`
directory's named tables. Store any prior run separately if it must be retained.

## Policy terminology and budgets

`disagreement` is static total-disagreement priority. `dopt` is greedy ridge
D-optimal design. `fair_contrast` is greedy concave contrast coverage with a
square-root objective. The raw legacy-compatible label `coverage` means static
nomination-count priority, not maximum-coverage greedy. `random_informative` is
uniform random sampling from the same structurally informative pool as every
other method.

Every method sees fixed Top-10 designs on the same measured panel. Candidates
nominated by all five models or by none have zero coefficients in all pairwise
contrasts and are omitted from every acquisition pool. Budgets 0, 3, 5, 8, 10,
15, 20 and 30 are caps per panel; actual cost is the lesser of the cap and the
number of informative candidates. One label is charged once per distinct
`(assay, bait, prey)` measurement and shared by all five models. The selected
panel roster contains no repeated measurement keys. Global allocation across
panels is not optimized in this experiment.

All current policies are static and outcome-blind. No unpublished target
positive count enters policy selection. No published Active Testing or MODEL
SELECTOR algorithm is implemented, and superiority over those methods is not
claimed.

## Exact certificates

For a pair of actions, let `d_i` be their difference in candidate nomination
(`-1`, `0` or `+1`) and let `S` be the revealed candidate labels. Then the exact
lower bound for their HC-count contrast is

\[
L(S)=-q+\sum_{i\in S}\{d_i z_i-\min(d_i,0)\},
\quad q=\#\{i:d_i=-1\}.
\]

The upper bound follows by replacing each unknown contribution by its maximum.
One action is a strict winner precisely when its lower contrast against every
competitor is strictly positive. Because the contrasts are integers, the
covering requirements are `sum_i c_ij x_i >= q_j + 1` for every competitor.
The offline oracle minimizes `sum_i x_i` with these constraints using the actual
complete outcomes. Its input is not available to any policy; it reports intrinsic
certificate size rather than a deployable acquisition rule.

Identical Top-10 sets form one action class. A strict action winner is counted
only if at least two distinct action classes exist. Strict model identity,
strict action class, guaranteed co-winner and exactly known tied best set are
different result columns. The code checks every reported winner or exact
best-set certificate against the complete outcomes, and complete informative
label revelation must always recover the exact best set.

## Result files

- `SUMMARY.csv`: mean/range over 100 computational acquisition seeds, separately
  for each of six frozen shared candidate tie orders.
- `COMPLETE_TRUTH.csv`: complete-label model/action endpoints, source-score tie
  bounds, and exact offline minimum-certificate witnesses.
- `PANEL_MEANS.csv`: complete panel roster with per-policy endpoint averages.
- `STOPPING_COSTS.csv`: cost until correct strict certification; tied cases use
  `-1` and remain in the main coverage denominator.
- `SEED_TOTALS.csv`: each acquisition seed's aggregate results.
- `NATIVE_COMPLETE_SCORE_PANELS.json`: primary-order full candidate identities,
  source scores, recorded labels and Top-10 designs.
- `PAIRED_BAIT_BOOTSTRAP.csv`: descriptive paired 39-bait resampling comparisons;
  these are not independent biological replications.
- `SCIENCE_SUMMARY.json`, `RECEIPT.json`, `EXPERIMENT_REPORT.md`: audited scope and
  numerical interpretation.

The independent scientific verifier in the surrounding delivery checks native
score reconstruction, row/model permutation invariance and exact finite
completion endpoints. Its receipt is separate from this producer's tests.
