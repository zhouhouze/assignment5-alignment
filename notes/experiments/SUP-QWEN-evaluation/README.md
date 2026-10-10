# Qwen 模型评估与数据飞轮计划

日期：2026-10-10。版本：proposal-v1。**P0 approval = PENDING；只完成计划归档，不授权后续执行。**
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

本轮没有生成新模型输出，没有清洗正式数据、训练、Judge 下载/运行，也没有改变官方测试、评分代码或历史 raw。当前只提出协议，下一轮先批准 P0，再单独批准 P1。

## 本轮文档验收

新增22份规划/模板，更新5份索引/进度文档；仅Markdown。新文档本地相对链接全部存在；P0–P10各有完整10项Gate字段；baseline239项SHA再次通过；Git diff whitespace和常见credential模式扫描通过。没有代码变更，因此本轮没有新训练单元测试结果。历史43 passed仅按原日志引用。Git归档仍需以实际push成功及远端commit核对为准。
