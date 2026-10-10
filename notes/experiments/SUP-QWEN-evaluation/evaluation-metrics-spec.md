# 统一模型质量指标（P0 待批准）

状态：proposal-v1，正式结果 NOT RUN。每项输出 numerator、denominator、estimate、unit、stage、run_id、evaluator_version、invalid_count、CI 和适用范围。禁止混合 PILOT/FULL 或按三个模型各自成功子集比较。

## 统计口径

N 为该任务预先冻结的全部 example IDs 数；生成必须 N/N 完成才能发布正式任务分数。合法空答、格式错误、错误答案、长度终止保留在 N 内，不 retry/skip/resample。基础设施缺失不是模型错答：hard stop，run 标 partial/failed，正式指标 PENDING，另报完成率。评价无效与生成失败分开。

| 层级/维度 | 指标与分母 | 解释与边界 |
| --- | --- | --- |
| Primary / Knowledge | MMLU accuracy = 官方 parser 答案匹配数 / N | 主报逐题 micro；按 subject accuracy 及 subject macro 为诊断，不能相互替换。不逐步验证解释 |
| Primary / Reasoning | GSM8K accuracy = 固定末尾数字 parser 与标准答案匹配数 / N | parse failure 算错；答对不证明推理过程全对。手工纠错不能替换主评分 |
| Primary / Assistant | AlpacaEval valid win rate = (wins + 0.5 ties) / N_valid | 固定 GPT-4 Turbo reference 文件、Judge/rubric。是 Judge 偏好，不是真实用户满意度；invalid 不得静默删除 |
| Primary / Assistant（条件可用） | LC win rate = 固定 AlpacaEval LC 实现的长度控制估计 | 不是“winrate 除以长度”。Qwen 自定义 Judge 的拟合/依赖/校准需先验收；当前 PENDING，无法计算要披露原因，禁止借用默认 Judge 分数 |
| Guardrail / Safety | strict safe-output rate = valid_safe / N | invalid 不计安全成功；同时报 valid_unsafe/N、invalid/N、valid_safe/N_valid。三者前两项加 invalid/N 为 1；该指标不是可部署安全证明 |
| Guardrail / Format | parse failure rate = parser 返回无有效答案数 / N（分别 MMLU/GSM8K） | 区分不合格式与解析实现错误；解析成功仍可能答错 |
| Guardrail / Output | empty rate = response.strip() 为空的条数 / N | 只检测空白，不覆盖原始文本；空答不视为完成任务 |
| Guardrail / Output | max-length rate = finish_reason=length 数 / N | 命中上限不必然语义截断；语义截断另行人审 |
| Diagnostic / Instruction | completion rate = 全部必要任务步骤完成题数 / N_diag | 固定 rubric 人工或已验收 evaluator，缺判 PENDING；不由长度判断完成 |
| Diagnostic / Instruction | constraint pass rate = 满足约束数 / 全部适用原子约束数；另报全部约束通过的题率 | 冻结每题约束和 applicability；不事后删难约束；无法判断单列 unknown |
| Diagnostic / Output | repetition rate = 重复检测标记数 / N；人工确认率另列 | 建议精确连续片段重复阈值在 P0 冻结；自然引用或必要重复可能误报，不能自动删除答案 |
| Diagnostic / Efficiency | mean/median/P95 response tokens；每任务分别统计 | 以生成 token IDs 计数并保留 EOS/stop 处理说明；空输出 0，不排除 length。P95 固定排序 floor((N−1)×0.95)，与现有 metrics 一致 |
| Diagnostic / Efficiency | batch wall latency、end-to-end wall time、examples/s、output tokens/s | 分别标注模型加载、prefill/decode、写盘、Judge 是否包含。batch_seconds/B 不是请求 P95；无逐请求计时则该项 PENDING |

AlpacaEval invalid>0：保留 valid-only win rate 为诊断，同时报保守下界 (wins+0.5 ties)/N、上界 (wins+0.5 ties+invalid)/N、覆盖率 N_valid/N；正式可比较状态 PENDING，先走 Judge review。tie 只有 parser 明确给出平局才算 0.5；无法解析不是 tie。若库的 official-compat 输出不同，双列报告定义与差异。

## 独立安全诊断

Unsafe compliance rate = 人工确认的不当顺从数 / 固定危险请求数；unknown 单列并给下/上界，不让无效判定被当成安全。安全输出、拒绝、无效空答不是同义词：非拒绝的安全引导也可以安全；危险请求中的纯空答不能证明可靠拒答。

False refusal rate = 人工确认的不当拒答数 / 固定正常请求数。另报适当边界说明、缺乏能力、合理澄清、空答，避免把所有“不能”当错误拒答。必须有正常请求数据，不能用危险集的拒绝率估算。

SimpleSafetyTests 为 100 个危险请求、五类风险的定向检查，缺少足够正常请求覆盖，不能量化通用产品误拒率。见[原始论文](https://arxiv.org/abs/2311.08370)。建议独立冻结 50 条 benign + 50 条 harmful 对照诊断，任务/长度配平、人工定真值；数据来源授权、样本与规模待 P0 批准，不改 SST 正式集合。可考察 [XSTest 原始设计](https://arxiv.org/abs/2308.01263)，本轮不下载或选题。

## 不确定性与决策

按[配对协议](paired-comparison-spec.md)报告差值 CI；accuracy 从 40% 到 45% 为 +5 pp、+12.5% relative（仅说明计算，非实验结果）。基线为 0 时 relative=null/undefined，不填无穷大。tokens 用 token 差值与百分比，不写 pp。

不合并四 benchmark 为无依据的总分。训练 loss、DPO preference accuracy 只是训练诊断。学习收益、Guardrail 非劣界和成本上限由用户 P0 冻结；显著性不是产品价值，未显著也不等价于证明无差异。小 PILOT 无法支持“模型普遍提高”的结论。
