# Qwen 模型评估与数据飞轮计划

日期：2026-10-10。当前协议：**SUP-QWEN-EVAL-v1 / FROZEN；P1A CPU 工程验收通过，P1B 资源/预算/执行授权待确认，真实 Full NOT RUN。**

P1B-0.5最新状态：[增量备份验收](p1b-incremental-backup-acceptance.md)——Mac/Linux各24项通过、真实SSH及既有16266条CPU Mock恢复通过；[费用检查单](p1b-resource-cost-checklist.md)。周期备份机制已验证，真实Full仍未启动，预算/时长/执行批准待定。

P1B-0历史预检：[现场预检](p1b-resource-preflight.md)——SSH恢复；源码/GPU/权重/容量及历史备份恢复通过，持久化保留规则/预算/执行批准待确认，真实Full未启动。

工程入口：[P1A readiness](p1a-readiness-report.md) → [实现](p1a-runner-implementation.md) → [可靠性测试](p1a-reliability-tests.md) → [P1B 命令](p1b-execution-commands.md)。下方 P0 记录为当时的历史状态。

唯一入口：[evaluation-protocol-v1.md](evaluation-protocol-v1.md) → [decision log](evaluation-decision-log.md) → [P1 readiness](p1-full-baseline-readiness.md)。产品质量数值阈值可保持未决，不阻塞P0技术完成。
`directly_comparable_to_official=false`。本计划基于 Spring 2026 Supplement，不将 Qwen 改编结果称为官方 Llama 结果。

## 当前证据与目标

[当前状态核验](current-state-verification.md)区分已经完成的 Base SMOKE/PILOT 和尚未开始的 FULL/SFT/DPO/Judge。目标是回答：训练是否改善能力、指令遵循与偏好，代价是什么，以及哪些错误值得转化为下一轮独立训练数据。

主链路：Base → Full evaluation → SFT → Post-SFT → DPO → Post-DPO → 配对分析 → 人工复核 → 下一轮数据准入。归档成功、计算正确、模型质量改善、人工确认是四件不同的事。

## 阅读顺序

1. [统一指标](evaluation-metrics-spec.md)、[评估协议](evaluation-protocol.md)。
2. [Prompt 2×2 对照](prompt-control-experiment.md)、[逐题配对结构](paired-comparison-spec.md)。
3. [SFT 数据质量计划](../SUP-QWEN-data-flywheel/sft-data-quality-plan.md)、[SFT 训练设计](../SUP-QWEN-02-sft/sft-training-experiment.md)。
4. [HH 偏好审计](../SUP-QWEN-data-flywheel/dpo-preference-data-audit-plan.md)、[DPO 训练设计](../SUP-QWEN-03-dpo/dpo-training-and-evaluation-plan.md)。
5. [Judge 可靠性](judge-reliability-plan.md)、[错误分类](error-taxonomy.md)。
6. [数据飞轮](../SUP-QWEN-data-flywheel/data-flywheel-design.md)、[路由与准入](../SUP-QWEN-data-flywheel/data-routing-policy.md)。
7. [P0–P10 执行门槛](execution-gates.md)、[待决事项](open-decisions.md)。
8. [正式计分板模板](../SUP-QWEN-final/model-evaluation-scorecard.md)、[横向比较模板](../SUP-QWEN-final/base-sft-dpo-comparison.md)、[产品行为模板](../SUP-QWEN-final/product-behavior-analysis.md)、[下一轮建议模板](../SUP-QWEN-final/next-iteration-recommendations.md)。

## 来源与版本优先级

首先依据本仓库 [2026 Supplement handout](../../../cs336_spring2026_assignment5_supplement_safety_rlhf.pdf) §3–6，然后是 [Dataset tests](../../../tests/test_data.py)、[DPO tests](../../../tests/test_dpo.py)、[adapters/docstrings](../../../tests/adapters.py)、CHANGELOG 和现有运行证据。不是 2025 作业。

所有后续运行遵守[归档规范](../archive-policy.md)：执行代码 commit、manifest、immutable raw、版本化评分、metrics、review、checksum、持久存储登记。规划文件的实际归档提交由 Git 历史定位，不在文件内伪造自己的 commit。

本轮没有生成新模型输出，没有清洗正式数据、训练、Judge 下载/运行，也没有改变官方测试、评分代码或历史 raw。本轮冻结协议但不修改runner/parser/数据。下一轮建议先批准P1 CPU Full runner与恢复/IO验收，之后才启动获批的GPU Full。

## 上轮规划归档（439f17b）

新增22份规划/模板，更新5份索引/进度文档；仅Markdown。新文档本地相对链接全部存在；P0–P10各有完整10项Gate字段；baseline239项SHA再次通过；Git diff whitespace和常见credential模式扫描通过。没有代码变更，因此本轮没有新训练单元测试结果。历史43 passed仅按原日志引用。Git归档仍需以实际push成功及远端commit核对为准。

## P0冻结验收（历史状态）

没有复制/重建22份规划。本轮新增唯一协议、决策日志、P1 readiness三份必需文档，更新已有规则/索引。60个benchmark文件与历史manifest一致，全部16266条Base prompt在CPU渲染/分词，零超长；7B tokenizer/config 8项SHA通过；Baseline239项SHA通过；原27条review仍pending。

实际CPU parser测试20 passed，未运行模型generation、训练或Judge。纠正文档P95和empty定义与既有runner的差异，不改历史指标。P1阻塞：Full路径未实现，恢复与大规模IO未验收，现场设备/存储/预算/执行授权待落实。当前协议、code hash、ID/prompt inventory与decision log可由本轮归档commit追溯。
