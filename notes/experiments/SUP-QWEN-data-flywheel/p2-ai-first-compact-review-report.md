# P2 AI-first 精简质量初审 — 2026-10-30

**Status: AI INITIAL TRIAGE COMPLETED; HUMAN CALIBRATION PENDING; DATA ADMISSION NOT APPROVED.**
适用 Qwen Adapted Supplement，`directly_comparable_to_official=false`。本记录是用户2026-10-30批准的“AI 主审 + 少量人工校准”策略的**第一轮探索性初审**，不是课程72B Judge推理，也不是经人工校准的正式模型质量分数；用户没有批准更改 Raw/Derived/冻结 Policy v1。

## 目标与范围

利用现有 20 Train 随机 + 20 Validation 随机 + 3 定向拒答的审核包，在不重跑GPU、不扩大人审系统的前提下先识别明确的任务违例、待核实事实和可用于校准的代表性样本。

- Train：复用 `artifacts/pa5-supplement-qwen/sft/20261029-p2-review-packet/after-independent-review/ai-initial-analysis-train-20.jsonl` 的 **20/20** 条 Codex 历史初析；没有再生成第二套标签、没重写其独立分析。
- Validation：读取固定 `artifacts/pa5-supplement-qwen/sft/20261029-p2-review-packet/validation-20.jsonl` 的 **20/20** 条，并在 `artifacts/pa5-supplement-qwen/sft/20261030-p2-ai-first/validation-ai-initial.jsonl` 新增 GPT-6 一次性初析。
- 定向拒答：读取固定 `artifacts/pa5-supplement-qwen/sft/20261029-p2-review-packet/diagnostic-refusal-3.jsonl` 的 **3/3** 条；机器初析见 `artifacts/pa5-supplement-qwen/sft/20261030-p2-ai-first/diagnostic-ai-initial.jsonl`。它们不是概率抽样。
- 输入抽样与血缘沿用2026-10-29 `manifest.json`：Train原为Raw 210348框seed0，Validation是Derived 23108框seed0无放回（每条20/23108）；两组不能混淆。
- 不修改 `train-20.jsonl`、`validation-20.jsonl`、Raw、Derived、mapping、审计候选或历史人工包。全部新初析的human字段仍为null/pending。

## 方法与证据等级

使用项目 [Error Taxonomy v1](../SUP-QWEN-evaluation/error-taxonomy.md) 与 [SFT Data Acceptance Policy v1](sft-data-quality-plan.md) 的质量标签。对每条阅读原始Prompt、Response；区分 **APPARENT_TASK_VIOLATION（由原文可见的任务约束问题）**、**NEEDS_FACT_CHECK（需外部信息核实）**、**NO_CLEAR_ERROR_OBSERVED（本轮未发现明确错误）**。JSONL保留来源行ID、引用片段、中文证据分析、provisional标签/严重度和待人审字段。

此轮AI是聊天环境中的 **GPT-6 一次性阅读**，无固定解码日志、没有重复调用、没有独立来源查证、没有真实编译/物理实验、没有 Judge 与人类真值一致性统计。**不能称为已部署/已校准的LLM-as-a-Judge；不能把AI自信程度写成可信概率。** 词数为Python式空白分词口径的直接机械计数（不代表排版页数）。

## Validation 20 条 AI 初审

| 类型 | 本轮记录数 | 可支持的解释 |
| --- | ---: | --- |
| 明确的任务/约束问题（APPARENT_TASK_VIOLATION） | 8 | 能直接指出违反任务或缺少交付的原文证据，标签/严重度仍待校准 |
| 有未经验证的事实或泛化问题（NEEDS_FACT_CHECK） | 7 | 目前不能认定为错误事实；需要外部权威材料或专家证据 |
| 暂未发现明确错误（NO_CLEAR_ERROR_OBSERVED） | 5 | 不等于已经证明所有事实正确或质量合格 |
| **合计** | **20** | 仅20条探索性样本，不能报告全量训练/验证缺陷率 |

明显需要关注的真实样本（示例，并非全部结果）：

- **Validation 3108**：≥500词已满足，实测约 839 空白分词，但未提供要求的图片，末句断在“Rather than avoiding”。来源证据见新AI JSONL。
- **Validation 9236**：要求3000词故事，实际约 814 词，任务约束未达成。
- **Validation 8209**：没有物理实验执行凭据，却呈现多个材料在不同温度的测量结果；重点是**虚构实验完成状态**，不是已核实的科学数据。
- **Validation 13782**：要求五页APA与≥5学术来源，但文本仅约 858 词，无完整参考文献表且结尾中断；文中引文真实性未核。
- **Validation 16754**：要求与历史气温比较，回答未提供跨年数据；属于任务不完整，具体温度说法另需气象事实核验。
- **Validation 4580 / 17452 / 20263**：仓储员工、宗教建筑、大学校史等具体事实待来源核查，**不是已确认事实错误**。

定向拒答3条：`train-raw-108444`（婴儿巧克力：保护性拒答候选）、`train-raw-118767`（正常Java请求：错误拒答/代码问题候选）、`train-raw-11717`（抢劫策划：合理拒答候选）；仍需用不同任务语境校准，不纳入随机统计。

**限制：** Train 20 与 Validation 20 分属不同抽样框和不同初析来源；不能将上表比率外推为全量真实错误率，更不能对比成模型性能指标。正式“Acceptable”和所有其他AI标签均属于provisional；未发现错误并不证明无错误。

## 最小人工校准方案（尚未执行）

不再要求学习者逐条读43条长英文文本。建议对AI证据卡做 **5例起步校准（提案）**，由人先看任务、关键英文原句和中文证据说明；必要时展开全文并复查英文原文：Validation8209（伪实验结果）、9236（硬约束）、12624（正确提取负对照）、定向118767（错误拒答+Java代码）、Train36509（来源忠实性；之前课堂B判断为教学记录，未签署/非盲审）。如事实争议涉及专业领域，交给具有相应技能的人员判断，不能用普通PM取代专家。

另外，P2-B.1 的长新闻共享簇和 AlpacaEval 完整问答候选仍待**独立风险处置**，短选项/公共引文不自动删数。要进入正式P2 Data Admission必须先处理这些重大未决风险并披露语义近重复方法盲区。

## 未解决事项 / 准入边界

- `AI_initial_coverage=43/43`（20 Codex 历史描述 + 20 GPT-6 Validation结构化初析 + 3 GPT-6定向初析，**不是一个经过一致性校准的统一Judge**）。
- `human_formal_review_coverage=0/43`；聊天中已有3个案例B判断与AI讨论，不属于签名、盲审或正式人审。
- `human_agreement=NOT ESTIMABLE`、`formal_quality_rate=NOT ESTIMATED`、`Qwen72B_Judge=NOT RUN`。
- `P2_Data_Admission=PENDING/NOT APPROVED`；冻结Policy未修改，质量/风险样本未删，Derived-v1 SHA不变。
- 具体缩减人审覆盖、争议裁决与准入原则仍需作为**单独的协议修订/授权判断**。用户同意AI-first并不自动把既有人工准入要求取消。

## 下一步

结束重复的数据审计开发。课程可**直接进入P3的CPU学习与接口审阅**，但在Data Admission通过和P3具体实现权限明确前不进行真实SFT训练、不将未经准入的Derived用于正式训练，也不启动GPU。P3首个组件只研究 `get_packed_sft_dataset` 和 `tests/test_data.py`，随后按官方窄测试推进。

证据：本报告、两个AI JSONL、既有 `20261029-p2-review-packet` 和 P2-A/P2-B.1 报告。运行方式：GPT-6聊天中一次性阅读并生成初析，无生产Judge/CLI/计费调用；无GPU、无训练、无真实模型推理。源分支执行依据：`c11b394fcfe7d17ad70a2c1bcface5334b4095b8`。
