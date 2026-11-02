# P2-D · Data Admission HOLD 决策与最小收尾清单

**日期：2026-11-02；仓库分支：`learning/pa5-supplement`；实验：CS336 PA5 Supplement Qwen adapted reproduction。**

**Decision captured：用户在对话中选择 B = HOLD 并做有限收尾。** 这是一项明确的**不放行正式训练**的决策；用户未给独立的判断理由，以下根据冻结标准列出的支持依据是助理分析，不冒充用户理由。当前 `P2_DATA_ADMISSION=HOLD / NOT APPROVED`、`P2_D_HUMAN_SIGNOFF=PENDING`。本文件**不构成人工审核电子签名、不修改冻结 Policy v1、不授权 P3 / GPU / 模型训练**。

## 与冻结 P2 Gate 对照

| 要求 | 目前可核实的事实 | 结论 |
| --- | --- | --- |
| 可追溯、可复算的训练视图 | P2-C Derived-v2 Train 210325；Validation 23108；Sample Train 1000。独立验证与压缩包恢复均 PASS；其余保留行逐字节不变 | 工程 PASS |
| Benchmark 隔离 | AlpacaEval370 完整 Prompt/Response 重叠 Raw train181453 已由 v2 排除，对应 v2 中余0 | **单一已确认案例已处理**，不能推断其他语义污染全清 |
| Train / Validation 隔离 | v1 机审精确 Prompt/Pair overlap=0；共享长新闻材料候选（Raw train14 / Raw validation9092）仍在 v2，任务分别为释义/翻译 | 局部同源材料独立性风险未裁决；不得宣称无泄漏 |
| 质量抽样与校准 | 20 Train + 20 Validation + 3 定向的 AI 初析已覆盖。原20+20正式人审规模改为 AI-first + 少量人工校准的口径尚未形成对冻结 Policy 的独立正式执行补充 | 尚未完成正式人工覆盖要求 |
| 重大争议处置 | Java Train 原始118767（课堂编号#118766）：AI建议S2；用户提议S3但未给具体依据 | `severity_final=UNRESOLVED`；需真实审核/必要领域复核 |

**注意：** P2-B.1 3732字段命中与3559 validation相关unique record pairs等统计是在 **Derived-v1** 上运行的历史候选审计，不能未经重新运行称为v2最新总量。校验器的PASS只适用它实际检查过的规则，语义污染未被全面检查。

## 用户已提交的5例校准反馈（未正式签署）

| 样本 | AI建议 | 用户反馈 | 当前处理 |
| --- | --- | --- | --- |
| Validation derived8209 | 未执行实验却展示测量结果，S2候选 | 认可 | 反馈已记录于对话；正式人审仍pending |
| Validation derived9236 | 3000词要求未满足，S2候选 | 认可 | 同上 |
| Validation derived12624 | Acceptable | 认可 | 同上 |
| Train raw118767 / classroom #118766 | 错误拒答、代码不完整，S2候选 | 要求改为S3，未提供理由 | **保留分歧**：AI S2 / 用户提议 S3 / 裁决 UNKNOWN；不能伪造伤害依据 |
| Train raw36510 / classroom #36509 | 来源忠实性不足，S1候选 | 认可 | 反馈已记录于对话；正式人审仍pending |

正式审核的 `reviewer_id`、`reviewed_at` 和独立样本审核sidecar未签署；不将课堂聊天视为盲审或专家裁决，不称5/5正式人审完成，不计算可靠Judge agreement。

## 污染候选的有限处置建议（没有删除授权）

1. **已处理 / 已验证**：AlpacaEval370双字段 exact 对应训练行已在Derived-v2排除；源 v1/Raw 保持不变。
2. **仍有风险 / 只复核代表**：Oscar Pistorius共享新闻材料 Train Raw14 ↔ Validation Raw9092；确认同源内容但指令不同，不直接判同题同答。为 P2-D 只做一次现成原文对照判断：是否有具体答案泄漏或验证任务可在训练中照搬完成；如无法判定，则标为 validation-independence `UNRESOLVED`，无需扫描全部3593条n-gram候选。
3. **低特异性 / 记录限制**：长文包含短名言候选 #2737，以及MMLU短选项命中，不能据此自动剔除；GSM8K/SST有限方法零命中不等于语义清零。
4. **版本边界**：P2-C仅授权并执行一条排除；未经批准不增加排除规则、不生成Derived-v3、不触碰既有Benchmark。

## 唯一 P2-D 剩余执行包（不开发新系统）

- **人工校准补充**：以既有5例的原文、英文关键句、中文分析和用户反馈为材料，建立**独立、追加式、待签署的**校准摘要。对 Java 的 S3 诉求记录为无理由争议，按 Taxonomy 保持 UNKNOWN；如实际裁决需给出情境/潜在伤害证据，不能猜测。
- **代表性污染裁决**：仅对现有 Oscar Pistorius 双原文做有限任务/答案对照；明确“有具体泄漏证据”或“目前仅同源材料/不能确认”，并说明为何不能外推整个验证集。
- **覆盖与正式决策**：将“原20+20人审拟缩为AI-first+5校准”作为待单独签收的执行附录，披露未审样本数量、非概率定向样本和不确定性；由用户明确签署执行口径、逐例人工结论和后续是否重开 Admission。禁止以 AI 初析代替真实人工。
- **停止条件**：未满足约定人审和重大风险处置要求时维持 `HOLD`；P2审核材料可以收尾归档，绝不宣布 `P2_DATA_ADMISSION=PASS`；不启用 Derived-v2 正式 SFT。允许另获授权后用课程fixture学习P3 CPU逻辑，但本决策未授予P3实现/训练权限。

## 已有证据入口

- [P2-C 真实执行报告](../SUP-QWEN-02-sft/p2-c-derived-v2-report.md)
- [P2-AI-first 初审](p2-ai-first-compact-review-report.md)
- [P2-B.1 污染候选](p2-b1-contamination-audit-report.md)
- [原准入草案](p2-final-calibration-and-admission-decision-draft.md)
- [冻结 SFT Data Acceptance Policy v1](sft-data-quality-plan.md)
- [冻结 P2 Gate](../SUP-QWEN-evaluation/execution-gates.md)

本备忘录只记录已给出的 HOLD 决策、证据和待办，不写正式质量裁决、不修改任何数据文件。
