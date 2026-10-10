# 数据路由与训练准入政策

状态：proposal-v1；所有候选默认quarantine，training_admission=PENDING。error标签可多选；primary_route恰好一个，secondary_route可选；任一失败须记录决定与理由，不能因难判断而悄悄丢失。

| 失败类型 | 推荐主去向 | 原因/必要条件 |
| --- | --- | --- |
| Capability / Knowledge | 独立来源SFT candidate | 缺可靠任务示范；核实正确性/知识来源，不直接复制holdout |
| Reasoning / Arithmetic | SFT candidate + regression | 新题示范需步骤与数值双重核验；可靠工具核算，不能用流畅AI答案当真值 |
| Instruction following / Incomplete | SFT candidate | 新任务完整示范和可判约束；如两答都正确但一答完成更好也可另构DPO |
| Formatting | SFT或regression | 先分辨协议不清/解析bug；格式训练要独立题，不为评分器投机 |
| Safety / Unsafe compliance | 专项人工安全review（先隔离） | S3未裁决禁止训练准入；之后可构授权安全示范/偏好或仅回归 |
| False refusal | 机制复核后SFT或DPO | 不懂允许范围可SFT；知道任务但偏好拒绝可DPO；先确认请求确实正常 |
| Hallucination | 验证来源的SFT / regression | 需要事实核查或适当不确定表达；不能把未经核实“修正版”训练 |
| Over-verbosity / Clarity | DPO candidate | 两答基本正确且安全，偏好简洁有用；不能只机械选短 |
| Repetition | evaluator/生成配置排查后DPO或SFT | 先区别重复输出bug、length循环与学习行为；未确定前pending |
| Truncation | regression / 配置诊断 | 先核对固定token cap；扩大上限是独立诊断，不伪称能力训练收益 |
| Parser Error | Evaluator fix | 用不泄漏测试答案的解析fixture回归；所有模型raw统一重算，保留旧指标 |
| Judge Error | Judge audit / evaluator fix | 人工裁决与rubric修订另版本，不把错误Judge标签当偏好训练真值 |
| Evaluation Ambiguity | Evaluation/regression待裁决 | 先修清题意/参考，旧正式评分不得被无声改写 |
| 可接受差异/无充分证据/来源不许可 | No action或pending review | 不为凑训练规模制造标签，记录保留/拒收理由 |

**来源优先于错误路由**：任何正式holdout样本一律evaluation/regression/evaluator audit，不进SFT/DPO；表中训练去向仅指可从独立获准来源构造的新样本。同一故障可产生成对独立训练候选与保留的原始评估case，通过parent_issue_id关联而不是复制测试题。

## 训练准入检查顺序

1. 来源授权/隐私：license、consent、source URI/revision、用途、保留期限、PII/秘密处理；无证据则拒收。
2. 血缘：parent_error_id、原始与修订SHA、作者/修改记录、错误假设、标签版本；AI生成部分显式标识。
3. 去重：规范化hash仅用于匹配，不覆盖raw；prompt/pair精确去重+近重复/语义候选人工核查。按来源/问题簇分组，防同题改写跨split。
4. 隔离：benchmark/test firewall、train/validation/test分组清单及SHA；已冻结test不可借评估回流。污染未决即暂停。
5. 质量：SFT示范事实/推理/代码/安全/完整性验证；DPO同prompt两答可比较、chosen依据明确、长度不是唯一理由。高风险必须人审。
6. 版本化：候选集与accepted集分开；manifest列来源/排除/去重/审阅/分布/sha/bytes/生成代码；不能覆盖上一轮数据。
7. 审批：用户确认目标假设、准入样本、guardrail和成本，记录approval_ref/date/scope；没有批准不进入训练。新数据实验从smoke/pilot开始，不自动再训Full。

记录字段：candidate_id、parent_issue_id、source_is_holdout、source_rights_status、privacy_status、dedup_group、split、labels、severity、primary_route、secondary_route、routing_reason、quality_evidence、ai_initial_analysis、human_review_status、human_notes、admission_status、approval_ref、dataset_version。

Gate关闭需每个case有route或pending原因；pending不算已解决。外部大产物登记存储持久性和恢复方法；公开仓库只存不含敏感原文的授权资产。
