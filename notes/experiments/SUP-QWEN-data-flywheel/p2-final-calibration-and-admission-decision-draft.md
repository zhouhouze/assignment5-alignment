# P2 精简收尾：AI-first 人工校准与训练数据准入决策草案

**Status: DRAFT / AWAITING HUMAN CALIBRATION AND USER DATA-ADMISSION DECISION.**  
路线：CS336 Spring 2026 PA5 Supplement / Qwen Adapted Reproduction；`directly_comparable_to_official=false`。截至 2026-10-30，本文件是只读证据整理和 AI 风险建议，**不是人工签收结果**。不修改 Raw、Derived-v1、冻结 Policy v1、人审历史 sidecar，也不批准训练。

## 当前真实进度

- P2-A.1/P2-A.2 数据身份、派生血缘与独立校验 PASS；Derived-v1 train=210326、validation=23108、sample_train=1000。
- P2-B.1 CPU 字段近重复与 Benchmark 候选审计执行 PASS，**污染清除声明不成立**。Train/Validation 原始精确 Prompt/Pair overlap=0；近重复候选尚有未解决的同源材料问题；AlpacaEval370 与 Train 原始行181453存在完整问题和回答的 exact match。
- AI 初审覆盖43/43：Train20历史 Codex 初析、Validation20 GPT-6 一次性分析、拒答定向3 GPT-6 一次性分析；方法不同且未经校准，不能作为统一 Judge 评分或总体缺陷率。
- **正式人工标注0/43**；历史课堂讨论3条Train已给B但未签署，不反写人审。P2 Data Admission=NOT APPROVED。
- 原本批准的20+20精简人审与后来的“AI主审+少量人类校准”方案的正式覆盖口径仍需用户明确选定；不要静默改写冻结的 SFT Data Acceptance Policy v1。

## 5个建议的人类校准锚点

这些是**原始Prompt/Response支持的AI提案**；`human_review_status=pending`，最终标签、严重度与备注都由真实审核人决定。英文引用短摘是证据导航，不能替代全文或专业查证。

| 样本 | 任务与原文事实 | AI提案（未确认） | 推荐人审重点 |
| --- | --- | --- | --- |
| Validation derived 8209（Raw8210） | 用户要求“Design and conduct a controlled science experiment”；回答编列在50–250°C下不同材料伸长的**具体测量结果表**，无开展实验的证据 | `Hallucination` / `Poor Instruction Following` 候选，S2候选 | 是否将未经执行的实验数据包装成真实观测；需要标明“模拟”才可作为模拟示例 |
| Validation derived 9236（Raw9238） | 用户明确要求3000词科幻故事；回复约814个空白分词（按Python whitespace口径） | `Poor Instruction Following` / `Incomplete Response` 候选，S2候选 | 明确字数约束没有满足，不因情节完整就误判为达标 |
| Validation derived12624（Raw12626） | 来源文本说“Ran with a friend who wasn’t feeling very well, so I slowed down for her”；回复说作者通过放慢速度表示体贴 | `Acceptable` 候选，无严重度 | 校准一个正确、简明、有来源支持的负对照，避免Judge只寻找错误 |
| Train定向原始118767 | 正常Java Lotka–Volterra模拟请求；回答“I can't write a complete program as I don't have a user interface.”，后续代码含 `java.util.scanner`、`main(string[] args)`、`system.out`，且缺图形输出 | `Incorrect Refusal` / `Code Error` / `Incomplete Response` 候选，S2候选 | 许可任务的不恰当拒绝 + 可见编译问题（实际编译NOT RUN） |
| Train原始36510（Derived36504） | 源材料允许果酱替换巧克力酱；回答额外建议等量替换、可可粉及调整甜度，源材料未给相应配方依据 | `Poor Instruction Following` 候选，S1候选；课堂已讨论B，但非正式人审 | “Answer according to”下来源事实和外部推断的边界；额外建议不是必然事实错误 |

若使用本5例，`human_calibration_completed`仅在真实人逐项独立确认、给出reviewer身份和审核记录后才增加。5例为**建议的探索性校准**，不能声称代表整个20+20人审抽样，也不能从5例计算整体缺陷率、可靠的Judge agreement或可接受训练比例。高风险分歧应按固定Taxonomy规则另行处置或保持unknown。

## 污染风险决策包（不是已批准裁决）

| 风险 | 已观察到的证据 | 建议处置及边界 |
| --- | --- | --- |
| Train原始14 ↔ Validation原始9092 | 同一Oscar Pistorius新闻材料，5-gram Jaccard≈0.815873；训练释义任务 vs 验证翻译任务 | **需审查同源材料是否导致任务/答案泄漏**；样本级尚未证明同题同答；由于其他候选未全部语义复核，整体Train/Validation近重复风险不可以宣称清零。 |
| Train原始181453 ↔ AlpacaEval370 | Prompt与Benchmark instruction完全相同，Response与GPT-4 reference完全相同 | **确认完整字段级重叠，不推定来源复制**。正式Benchmark holdout training_admission=PROHIBITED；后续正式SFT应先决定是否提交**版本化数据调整**排除/隔离该训练行，或提出经批准的另一套不暴露确认集。不得静默改Derived-v1或删除原Benchmark并用较好子集代替固定主指标。 |
| Train原始151747 ↔ Validation原始16549 | 短名言被长回答包含，containment=1但Jaccard≈0.015 | 目前仅有短引用重合，低特异性，**没有足够依据判定整篇或任务泄漏**；保留审计证据，非重大阻塞的初步候选。 |
| MMLU短正确选项、GSM8K/SST零命中 | MMLU共126次短选项命中，未命中MMLU题干；GSM8K/SST在本轮词面方法无命中 | MMLU仅低信息量匹配；零命中不代表语义污染不存在，保留方法盲区及评价限制。 |

## 推荐的P2关闭口径

**当前应是 `P2_AUDIT_EVIDENCE=READY_FOR_HUMAN_DECISION`，而非 `P2_DATA_ADMISSION=PASS`。**

要使既有Gate的训练数据准入标准得到满足，至少仍需：

1. 真实人对选定5例完成独立校准并记录同意/修订/unknown，明确新的少量人审是否被用户批准替代原20+20人工规模；未审的38例保持pending（部分另含AI初析）。
2. 对同源长材料/AlpacaEval完整问答重叠形成用户可接受的**实质风险处置**；已观察到的benchmark题答进入train的情形不能仅靠备注就变成“没有污染”。
3. 决定是否采用版本化数据修订方案；如需删除/重新拆分记录，必须另批规则与Derived新版本，原始与Derived-v1仍不可变。
4. 简洁报告覆盖/局限/未核实的上游来源比例、正式人审状态，并由用户对Data Admission作出明确准入或HOLD决定。

即使最后结论是 **HOLD / NOT APPROVED**，也可以说P2审计和风险识别已经完成，不能称训练准入PASS。可以并行使用**课程合成fixtures**学习P3 CPU packing，但未经准入的Derived-v1不能进入正式模型训练。

## 证据引用

- [AI初审总报告](p2-ai-first-compact-review-report.md)；[Validation逐条AI证据](../../../artifacts/pa5-supplement-qwen/sft/20261030-p2-ai-first/validation-ai-initial.jsonl)
- [Train、Validation、定向拒答原文包](../../../artifacts/pa5-supplement-qwen/sft/20261029-p2-review-packet/README.md)
- [P2-B.1污染候选报告](p2-b1-contamination-audit-report.md)；[代表性原始候选](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2b1/representative-candidates.jsonl)
- [冻结质量准入策略](sft-data-quality-plan.md)；[错误分类](../SUP-QWEN-evaluation/error-taxonomy.md)
