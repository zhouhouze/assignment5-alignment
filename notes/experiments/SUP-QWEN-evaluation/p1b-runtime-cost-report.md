# P1B-1 Runtime / Cost / Persistence Report

2026-10-11；仅本轮P1B-1。授权4小时累计、总预算¥20，不是每任务独立额度。执行commit47ae79f；数据证据：[runtime-cost-summary](../../../artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/analysis/runtime-cost-summary.json)。

## Actual runtime

| Task | China start → end | Attempt wall | Model load | Sampled peak |
| --- | --- | ---: | ---: | ---: |
| mmlu | 11:46:25 → 12:16:38 | 1813.82s | 87.21s | 24,761MiB |
| gsm8k | 12:18:13 → 12:42:49 | 1475.54s | 50.90s | 24,761MiB |
| alpaca_eval | 12:43:19 → 13:05:01 | 1302.20s | 53.90s | 24,763MiB |
| simple_safety_tests | 13:05:37 → 13:07:53 | 135.41s | 66.70s | 24,761MiB |

四attempt总计4726.96s（78.78分钟），包含模型加载/推理/进程内写入。纯unique batch生成汇总4199.73s，不是request latency。准备、备份、评分、恢复、报告/归档另计在整体窗口内；保守计时起点11:37，报告汇总时为95.95分钟，截止2026-10-11T05:12:56.776295+00:00。最终Git同步后累计总时长见执行session的sync-receipt.json及最终回复，不能把本表单卡attempt时间当全部工作时间。

四任务都使用同一绝对generation deadline=13:59:25（GNU timeout+guard）；距14:29:25到期保留30分钟收尾。没有重新分配4小时，没有resume/重试，也没有第二实验。GPU peak=24,763MiB，250ms采样可能漏短峰；结束时15MiB/0%且无compute/owned runner。结束云盘可用136,936,398,848 bytes、12,547,951 inodes。

## Cost

- 当前控制台已核实：初始¥6.32+两次¥3.16续租=**¥12.64**，租期10:29:25→14:29:25；整个4小时已付租期保守计入本轮预算。
- GPU费率¥3.16/h。报告汇总时本轮耗时折算约¥5.05，只是运行效率参考，**不是额外账单**，不与¥12.64相加。
- 已付租期口径预算余量¥7.36；控制台没有隐藏磁盘/带宽费用，明细未显示其他费用；没有新增付费服务。最终结算账单未知，不伪称已拿到final invoice。
- 用户自行完成续租；未由Codex购买/续费/开启自动续费。自动续费OFF，仍以14:29:25实际到期为界。当前累计时间/已付租期费用满足授权上限；到期后磁盘费用未知，不能声称后续零费用。

## Persistence / Backup

账户现场观察：到期保留磁盘ON、到期删除磁盘OFF。此前用户说明关机后保留实例；未做关机/释放试验。系统盘存在、无独立云盘。关机保留、到期保留和主动释放/删除是不同动作；保留期限、到期费用、释放后恢复保证UNKNOWN，不假设释放可恢复。

60秒周期，transfer timeout180s，guard ACK age180s/poll5s/grace30s；backup对象fsync/SHA成功后才ack。全部四任务final quiescent/deferred=[]，原Runner/独立复算/恢复SHA通过。guard只管理本任务，结束进程不等于平台停止计费。未关闭、释放实例或删除磁盘；独立Mac证据已验收，不依赖释放后的云盘恢复。

完整tar约26.08MiB，加上Git报告/小证据即可用于最小迁移；完整还原运行环境另按uv.lock、固定模型/tokenizer revision下载，不需要迁移15GB权重。模型缓存不是不可替代的实验证据。Mac CAS/restore/tar在同一磁盘，不属于异地多副本。

## Scope / Stop

四真实Full任务完成；Judge NOT RUN、LC NOT VALIDATED、人审PENDING、SFT/DPO NOT RUN。Git同步完成后停止，下一Gate仅建议P2/P3，不自动执行。
