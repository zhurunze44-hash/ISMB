# Paper3 / DecisionTransport 公开复现包

**当前状态：已在 GitHub 公开有限范围的 R8-R10 结构评分复现代码；整篇论文端到端公开复现仍为 HOLD。**

真实地址：https://github.com/zhurunze44-hash/ISMB/tree/main/ISMB

本仓库不包含原神经 checkpoint、作者机私有回传 ZIP 或未经授权重新分发的第三方原始数据。R8 公共人类 Y2H、R9 自适应和 R10 的限定种子计算，可以从经过双哈希校验的公开输入重新执行；74 个酵母派生 mask 缺少源数据到候选身份的完整映射。

```bash
git clone https://github.com/zhurunze44-hash/ISMB.git
cd ISMB/ISMB
python -m pip install -r requirements.txt
python tools/verify_release.py
python tools/prepare_inputs.py --download
python tools/run_smoke.py
```

本仓库中的 `CODE_AND_EXPECTED_SHA256.json` 列出 ISMB 目录下除清单自身外的发布文件，校验器先于数据下载运行。GitHub Actions 工作流位于仓库根目录 `.github/workflows/reproduction-smoke.yml`。

原 NBFNet 作者机已有 NBF-only PASS，不代表公众端到端原生复现 PASS；AA/G1A 回顾性分析及预揭盲独立性仍为 HOLD，酵母未见边泛化为 STOP。官方论文中的“Availability and Implementation”应只声称本仓库确实可公开重算的范围，并由人类作者依投稿规则核对。