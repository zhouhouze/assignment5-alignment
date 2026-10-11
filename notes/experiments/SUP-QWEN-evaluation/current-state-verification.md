# 当前实验状态核验

> 历史Gate记录，保留当时状态。2026-10-11实际Full已16,266/16,266并验收；最新结果、授权/费用和精确启动命令见[p1b-full-baseline-report.md](p1b-full-baseline-report.md)及其session-evidence/launch-*.json，不能把下方旧NOT RUN视为当前状态。

核验日期：2026-10-10；核验起点 local HEAD / GitHub branch HEAD 均为 `185364dbfe1fafef325b1d6fa0a4694399881d94`，Supplement 工作树干净。Main 工作树有既有未提交内容，本轮未触碰。此次核验只使用本地文件与 GitHub 分支引用；没有进行新的云端/GPU 检查。

## 已完成与未完成

| 阶段 | 已有证据 | 当前结论 |
| --- | --- | --- |
| Base SMOKE | 20261003-smoke-03：4 个 raw，各任务 1 条 | 完成 |
| Base PILOT | 20261003-pilot-03：80 个 raw，各任务 20 条；metrics-v1、offline-recomputation | 完成；不是 Full |
| Base FULL | 无 Full run | NOT RUN |
| SFT 数据 | 三份原始文件及验收记录；未创建有效数据派生视图 | 下载/审计完成，训练准入 PENDING |
| SFT 实现/训练 | Dataset、batching adapters 仍为 NotImplemented；尚无完成的训练循环与模型 checkpoint | NOT RUN |
| DPO | loss adapter 仍为 NotImplemented；HH 四个文件存在 | 数据转换/训练 NOT RUN |
| Qwen 72B Judge | 模板与 tokenizer 兼容准备记录；无 Judge run | NOT RUN；不是端到端验收通过 |
| 人审 | Base review packet 27 条 | PENDING；AI 注释不能代替人审 |

## 复查结果

- 重新计算 baseline/SHA256SUMS 全部 **239/239** 项 SHA256：通过；逐个 JSON 解析确认 4 条 SMOKE、80 条 PILOT。历史产物未重写。
- 读取 PILOT metrics：MMLU **15/20 = 75%**，GSM8K **17/20 = 85%**；两者 parse failure 均 0。AlpacaEval **4/20** length termination，Judge 分数 NOT RUN；Safety Judge 分数 NOT RUN。这些都不能填进 Full scorecard。
- 平均输出 tokens：MMLU 19.15、GSM8K 181.2、AlpacaEval 289.05、Safety 133.5。该批 80 条空回答为 0。
- 三份 SFT 文件重新逐行计数、检查空字段并计算 SHA：train 210348（1 空 prompt、21 空 response）；test 23110（2 空 response）；sample_train 1000（0 空字段）。哈希与[验收记录](../SUP-QWEN-02-sft/data-acceptance.md)一致。只读核验，没有写过滤结果。
- 全量扫描三份 SFT JSON 的键仅为 prompt、response；逐条来源不可识别。现有 train/test 精确重合为 0 是历史审计结论，不代表语义去重或污染检查已通过。
- HH 四个 gzip 可读取首条 JSON，键为 chosen/rejected；本轮仅确认存在和文件哈希，**没有宣称全量 schema/单轮筛选通过**。
- 实际 benchmark 库存只读计数：MMLU test 14042、GSM8K test 1319、AlpacaEval 805、SimpleSafetyTests 100。

## 测试证据边界

[历史 CPU 测试日志](../../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261003/tests-cloud.txt)：43 passed in 4.33s。本轮没有重跑训练测试，也没有把历史结果标成新测试。
[官方接口历史测试](../../../artifacts/pa5-supplement-qwen/preflight/20261002/tests-official-rerun.txt)：4 passed、3 failed（SFT Dataset、batching、DPO loss 的 NotImplemented）。因此不能说 Supplement 训练实现已完成。当前 adapters 只读核对仍然未实现。

## 可追溯来源

- [Baseline evidence](../../../artifacts/pa5-supplement-qwen/baseline/)、[PILOT report](../SUP-QWEN-01-baseline/pilot-report.md)。
- [SFT acceptance](../SUP-QWEN-02-sft/data-acceptance.md)、[已有 AI 样本审计](../SUP-QWEN-02-sft/data-audit.md)。
- [2026-10-10 云端同步记录](../SUP-QWEN-01-baseline/archive-sync-status.md)属于前一 Gate 的核验，不代替未来租用硬件的实时 preflight。

PILOT 运行代码 commit 为 `f5f4050de424a2b371da83e792fa5a4a81279084`；实验归档提交与运行代码提交分开追溯。后续计划文件不会改变以上历史状态。

## P0冻结复核追加（2026-10-10，起点439f17b）

本轮local与origin HEAD均439f17b2f152676175b2ad2e38f2c93302a75b7e，工作树起点clean。再次校验Baseline239项SHA、原27条review全部pending；未改旧raw/metrics。固定tokenizer/config八文件SHA通过，读取全部四任务16266条输入计算ID与prompt inventory，零超长（各任务最大prompt tokens 1186/330/624/164）。这些是CPU输入检查，不是新generation。

实际运行tests/test_metrics.py和tests/test_supplement_metrics_edges.py：20 passed in 0.01s。Full runner源码仍明确只支持SMOKE/PILOT且select非PILOT只取1题；不能把历史“可申请下一Gate”理解成Full代码已ready。协议与blocker详见[evaluation-protocol-v1.md](evaluation-protocol-v1.md)、[readiness](p1-full-baseline-readiness.md)。无新SFT/DPO/Judge/人审结果。
