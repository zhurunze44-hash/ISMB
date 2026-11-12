# DecisionTransport / Paper3 — reproducibility release REVIEW CANDIDATE

**STATUS: AUTHOR-AUTHORIZED PUBLIC v1 (structural R8–R10 smoke scope).** Original analysis code is MIT-licensed. This release is **not** a declaration that the complete ISMB/ECCB 2027 Paper3 has been end-to-end publicly reproduced (neural / BioPlex / 1,029-bait native producers remain Layer-2 HOLD).

## What an independent reader can recompute

The **public, retrospective structural-score** human Y2H experiment from R8: fixed raw measurements, 71 panels including 30 zero-HC panels, 2,083 unique candidate-label keys, five classical structural scores, exact strict model/action winners, information-bounded certificates. The R9 exploratory adaptive acquisition analysis and R10 within-study human assay1 also use public upstream inputs. The R10 yeast **derived-mask** calculation can be repeated, but the complete mapping from its 74 masks to original pair/candidate IDs cannot currently be reconstructed; consequently its native row-level lineage remains HOLD.

### Offline or online setup

```sh
python -m pip install -r requirements.txt
# A: public GitHub download (requires Internet):
python tools/prepare_inputs.py --download
# or B: supply independently obtained pinned upstream files from a folder:
python tools/prepare_inputs.py --from-dir /path/to/pinned/public/files
python tools/run_smoke.py
```

The input directory must contain `HuRI.csv` and `PPI_prediction_validation_result_20210624.xls`. Despite the `.xls` extension, the second file is TSV. Both SHA256 **and** Git blob SHA1 are checked and unexpected bytes fail closed.

The smoke run (R8 two deterministic seeds, R9 one, R10 one) compares each recomputed row against archived frozen expected rows. It is intended for fast outsider checks, *not* as the entire computational study. The originals contain R8 6 shared tie orders ×100 acquisition seeds, R9 100+20-seed sensitivity analyses and R10 100-seed transfers; full experiment entrypoints are provided in `r8`, `r9` and `r10` code. To replay a large run, use copies of these directories and provide sufficient CPU time rather than overwriting evidence.

### Scope boundaries

- Original checkpoint NBFNet neural replay: prior **AUTHOR-SERVER NBF-ONLY PASS**, **NOT** publicly reproduced from this candidate, because full model/source graph/checkpoint producer assets and release rights have not been completed.
- Original Phase3 AA/G1A: **HOLD**. Matching retrospective calculations cannot certify pretarget use. G1A uses target HC.
- Original HCT116, HuRI direction, 44 constructs, 880 incomplete historical model comparisons, and 1,029 matched bait results: source production chain not fully public; older frozen derived analyses cannot be promoted to end-to-end public reproductions.
- Yeast 74 masks: **G5B HOLD** because candidate/pair identity lineage is missing. Replaying mask-level results is *not* an independent rebuild from the source TSV.
- Method increment and independent pretarget evaluation: **HOLD**. YeRI unseen-edge generalization: **STOP**.
- Intended public repository: `https://github.com/zhurunze44-hash/Paper3-DecisionTransport-repro` (fill abstract only after anonymous clone verification succeeds).

## Files

`r8/`, `r9/`, `r10/`: frozen analytic code selected for reviewer inspection. `r10/input`: derived masks (not raw-to-mask lineage). `expected/`: compact frozen seed-level reference outputs to check deterministic executions. `provenance/public_input_manifest.json`: immutable external source identities. `tools/`: integrity-checked public input preparation and smoke verification.

## License and publication scope

- Original author-controlled analysis code: **MIT** (`LICENSE`). See `NOTICE` for upstream/third-party limits.
- First public push includes R8/R9/R10 structural analysis scripts, pinned-input fetch/verify tools, expected smoke outputs, derived yeast masks, docs, and CI.
- **Not included:** author-server RETURN packages, neural checkpoints, secrets, or redistributed raw HuRI/yeast TSV files.
- Neural / BioPlex HCT116 / 1,029-bait native producers: **Layer-2 HOLD** (claims retained with restricted reproducibility wording; NBF-only PASS is not extended to AA/G1A).
- After the public GitHub URL exists, run an anonymous clean-clone verification before filling ISMB `Availability and Implementation`.

Upstream `spxuw/PPI-Prediction-Project` carries an MIT LICENSE at the pinned commit; separate data redistribution terms must still be checked by end users. See `provenance` and `PUBLICATION_HOLD.md`.
