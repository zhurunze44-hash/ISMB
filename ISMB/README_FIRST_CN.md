**作者已授权公开 v1（MIT；结构评分 R8–R10 范围）。整篇神经原生公开复现仍 HOLD。**

# Paper3 公开复现审稿包（待作者审查，尚未公开发布）

这是一个**可执行的最小公开数据复算候选仓库**，不是 Paper3 整篇研究的 GLOBAL PASS。当前连接的 GitHub 账户尚无 Paper3 仓库。不得把该包或链接占位文字当作已经公开提交的可审查代码。

运行：`python -m pip install -r requirements.txt`，然后 `python tools/prepare_inputs.py --download`（联网）或 `--from-dir <已核验的原始公共输入目录>`（离线），最后 `python tools/run_smoke.py`。

R8/R9/R10 的公开结构评分分析可重放；R10 酵母 74-mask 缺逐候选原始身份，仅有派生重算；原 NBF/HCT116/历史尾部等不能由这里端到端复算。明确禁止将 NBF 原生作者机 PASS 外推为对公众的完整可复现。

必须先经作者核查数据许可与身份、源码版权、版本、公开仓库、公开链接、README、完整复算清单，再考虑发布。正式论文正文与摘要需要人类作者完成。详见 README.md 和 PUBLICATION_HOLD.md。
