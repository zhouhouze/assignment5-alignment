# SFT Data Acceptance Policy v1 / 数据质量审计计划

状态：**SFT Data Acceptance Policy v1 = FROZEN / 用户已批准处理策略；实际过滤 execution_status=NOT RUN，P2执行仍待单独批准。** 本轮不写派生训练数据。固定 mirror revision 见[协议](../SUP-QWEN-evaluation/evaluation-protocol.md)；镜像与2026 Modal字节等价性未证明，不能改称官方原件。

## 版本化准入

Raw immutable → schema validation → invalid row exclusion → derived view → manifest → 人工准入。

1. 对原始文件计算 bytes/SHA、逐行检查JSON对象和prompt/response字符串。损坏JSON、缺键、非字符串等超出当前已知空字段范围时hard stop，不随意扩展剔除规则。
2. 已批准只剔除 prompt 或 response 的空字符串、纯空白字符串：采用Python字符串strip()==空串检测，**不trim保存非空原文**。严格空串与非空但strip后空分别计数；reason区分empty_prompt/whitespace_only_prompt/empty_response/whitespace_only_response。非字符串/缺键属schema异常hard stop，不伪装空字段。
3. 以原始文件SHA+split+1-based物理行号为source_row_id。保存excluded_rows manifest的row_id/reason，双字段异常只剔除一条，按ID集合去重计数。
4. 预计train210348→210326、validation23110→23108，sample1000保持1000；实际计数必须重新计算。数量或哈希不同先调查，不能硬编码为预期。
5. 派生文件另命名derived-v1；manifest记录规则文本/hash、执行commit、源SHA、逐行mapping、排除清单SHA、派生SHA/bytes/count、生成时间、审批记录。原始test在此充当SFT validation，不是下游benchmark test。
6. 复算train/validation精确prompt/pair overlap；sample_train是train子集，不能当validation。近重复/benchmark污染另作审计，不自动删除已知四个重复prompt或其他低质量/风格异常记录。若泄漏，暂停准入，提出新的版本化变更审批。

原始SHA：

| 文件 | SHA256 |
| --- | --- |
| train | 3b72228a7976079a5c5a30249fd3289179ad01006cbb67d15c7c366d4fd25913 |
| test | ce84dd834a7bbfc622cb3b50dc6c233e7dd91e002fd84f7cf86f70762a2c9ed9 |
| sample_train | b26bbe382793889ccb397e7c8afdf64ad3e52f0109d191e66c424587fba596df |

## 质量审计抽样提案

先复用已有20条随机+3条定向AI审计作为已知风险线索，人审仍pending。P2新样本建议：100条seed=0随机train用于总体粗估；50条train分层诊断；20条validation独立检查。预算不足先批准20+20小样本，不宣称总体缺陷率已精确估计。

分层维度：source（可辨识才用）、任务类型（问答/代码/写作/数学等）、prompt/response长度分位、拒答候选、最长1%和空字段边界。保存抽样框、seed、算法、入选概率、重叠/去重规则。随机组与定向组分别报告；不能把富集高风险样本的错误比例当全量质量率。字符与token长度分别定义，tokenizer固定revision。

三份原始JSON只有prompt/response，**UltraChat与SafetyTunedLlamas实际逐条来源比例当前不可识别**。可审查上游来源metadata/映射；不以“I cannot”前缀或拒答内容反推来源。若找不到可验证mapping，source_dataset=mirror/unknown_origin，source_proportion=PENDING（不可识别原因）。不把1525个历史regex候选当SafetyTunedLlamas数量。

## 审计记录规范

字段：sample_id、source_dataset、source_file_sha256、source_row_id、split、sampling_stratum、selection_probability、prompt、response、task_type、quality_labels、severity、ai_initial_analysis、human_review_status、human_notes、reviewer_id、reviewed_at、rubric_version。

标签：Factual Error、Reasoning Error、Code Error、Incomplete Response、Hallucination、Incorrect Refusal、Unsafe Compliance、Poor Instruction Following、Format Issue、Acceptable；定义映射见[错误分类](../SUP-QWEN-evaluation/error-taxonomy.md)。允许多标签；Acceptable不能与已确认错误同用。

AI给出的task_type/quality_labels/severity均为provisional，解释只能放ai_initial_analysis；human_review_status=pending、human_notes=null，直到真实人工提交。建议10%双人盲审+所有S3/争议；agreement按共同已审样本分母，未审不能当一致。

高风险/质量问题只做标记及后续数据建议，不在本轮或P2未经授权自动全量清洗。准入判据：源和派生可复算、split隔离可证明、空字段规则获批且实际重新扫描/派生验收完成、抽样覆盖/人审覆盖已披露、重大风险有处置结论。未完成部分保留PENDING。

输出：[报告模板](sft-data-quality-report.md)、exclusions、derived manifest、review packet、审计统计/限制。完整数据不入Git，仅在已批准阶段写派生视图。
