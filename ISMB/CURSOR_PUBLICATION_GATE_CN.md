# Paper3 GitHub 发布后验收清单（用于 Cursor / 独立审稿人）

公开仓库：https://github.com/zhurunze44-hash/ISMB（代码位于 `ISMB/` 子目录）。已发布并不表示完整 Paper3 公开复现完成。

1. 无登录、无作者机文件的外部计算机执行 `git clone https://github.com/zhurunze44-hash/ISMB.git`，进入 `ISMB/ISMB`。
2. 运行 `python tools/verify_release.py` 检查所有列入清单的代码与参考文件完整性。
3. 运行 `python -m pip install -r requirements.txt`、`python tools/prepare_inputs.py --download`、`python tools/run_smoke.py`。保存 Python、依赖版本、源码 commit、两个公共输入的 SHA256 与 Git blob 校验、逐表输出和执行日志。
4. 检查仓库根目录 GitHub Actions `Paper3 public structural reproducibility smoke` 是否 PASS；若 FAIL，不得声称无缓存匿名复现通过。
5. 逐张论文图表核对其上游原生生产者是否可公开取得。未经发布的 checkpoint、BioPlex/HCT116、历史神经模型及 1,029-bait 结果只能保留限定来源的主张。
6. 酵母 74-mask 至原始候选身份的 G5B HOLD 不得被派生重算覆盖；G4/G6/G7 HOLD 和 YeRI G8 STOP 均必须保持。
7. 论文公开代码链接应指向真实仓库与固定 commit，并准确描述只支持 R8-R10 限定结构复算的范围。

不得上传新的私有 RETURN、原始模型 checkpoint、口令或未经批准的第三方数据。未经证据支持，不得将整篇论文写为 GLOBAL_PASS。