# Cursor + 作者服务器最终发布前检查（人工授权后运行）

**禁止自动推送。** 只有作者核实源码版权、数据许可、个人/服务器路径、联系信息与全部科研主张之后才开始公开发布。

1. 在作者控制的 GitHub 账户下创建独立公共仓库（建议名称 `Paper3-DecisionTransport-repro`，仅供选择，未实际创建）。
2. 把本 `candidate_repository` 复制到新建仓库；先运行 `python tools/prepare_inputs.py --download`（验证固定 Git 公开输入）与 `python tools/run_smoke.py`。也可用独立获取的本地输入 `--from-dir`。
3. 按论文逐项列出 `table/figure -> command -> inputs -> expected output`，补齐目前无法从公开模型/实验原始资产生成的主结果；不能靠作者派生缓存替代原始生产者。
4. 原 checkpoint、训练图、词表、NBF 推理入口、来源数据许可、AA/G1A 历史生产者若无法公开，必须明确相应主张及访问路径；原 HCT116 AA 仍 HOLD。
5. 酵母 74-mask 缺逐候选身份链。没有补齐就删除任何声称完全公开重建该部分的表述，仅保留 derived-mask 重算。
6. 由作者确认软件 LICENSE（当前尚未授权，禁止随意补一个 MIT）、README、公开代码仓库所有者、版本标签、完整安装与构建日志。
7. 在**真实外部干净 clone** 中运行上述程序，保存环境版本、核心表数值和所有数据哈希、Git commit。
8. 确认公开仓库 URL 可以在无登录情况下访问，并将真实地址填写在由人类作者撰写的 ISMB 摘要 `Availability and Implementation`；联系邮箱由通讯作者确定。
9. 保留 G4/G6/G7 HOLD、G8 STOP，不再声称全面 PASS。任何正式发布由作者进行，不由本验收包自动执行。
