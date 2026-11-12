# Paper3 / DecisionTransport - public reproducibility repository

The public source release is located in [`ISMB/`](ISMB/README.md). It reproduces a **bounded structural-score R8-R10 smoke test**, **not** the complete historical Paper3 experiments.

To reproduce in a fresh environment:

```bash
git clone https://github.com/zhurunze44-hash/ISMB.git
cd ISMB/ISMB
python -m pip install -r requirements.txt
python tools/verify_release.py
python tools/prepare_inputs.py --download
python tools/run_smoke.py
```

The fixed public inputs are checked against both SHA256 and Git blob identities. Public CI is defined in [`.github/workflows/reproduction-smoke.yml`](.github/workflows/reproduction-smoke.yml).

**Scientific scope:** public structural R8-R10 smoke calculations are covered. Original NBF/HuRI neural and BioPlex/HCT116, 1,029 matched baits and the original 880 historical comparisons are **not** fully publicly regenerable from this release. Yeast 74 derived masks lack raw-to-candidate lineage. Pretarget independent evaluation and independent method gains remain HOLD; YeRI unseen-edge generalization is STOP. See [`ISMB/PUBLICATION_HOLD.md`](ISMB/PUBLICATION_HOLD.md).

The `ISMB/LICENSE` covers only authorized original source code, not third-party research data or model assets.
