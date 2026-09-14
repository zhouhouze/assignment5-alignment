# O1 Prompt Baselines 历史实验数据归档复现计划

日期：2026-09-14。实验 ID：`20260914-190540`。

## 目标

保留 2026-07-16 的历史正式结果，不使用新结果覆盖旧结论。按历史配置重新运行三种 prompt，恢复逐题 raw JSONL、manifest、metrics、logs、human-review packet 和 checksum。

复现结论分为三层：配置复现、汇总结果复现和逐题复现。旧 AutoDL raw JSONL 已不可用，因此逐题复现只能标记为不可验证。

## 固定配置

- 生成代码：`a75ef3db48e3bbf293def0441f0229f6d1371254`
- 模型：`allenai/OLMo-2-0425-1B`
- 本次模型 revision：`a1847dff35000b4271fa70afc5db10fd29fedbdf`
- 数据：GSM8K test，1,319 条，SHA-256 `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`
- Prompt：`question_only`、`r1_zero`、`r1_zero_three_shot_gsm8k`
- seed 0；temperature 1.0；top-p 1.0；max tokens 512；batch size 4；GPU memory utilization 0.75
- `question_only` 不使用 `</answer>` stop；两个 R1 prompt 使用 `stop=["</answer>"]` 并保留停止字符串
- Grader：`question_only_reward_fn` 和 `r1_zero_reward_fn`

## 执行 Gate

1. 环境、代码、数据、prompt、grader 和模型缓存核验。
2. 三种 prompt 各 1 条真实 GPU smoke。
3. 三种 prompt 各 20 条 pilot；检查记录数、ID、重新评分和终止原因。
4. 顺序运行 `3 × 1319` full；每批写入 partial，完整校验后原子重命名。
5. 从 raw JSONL 重新计算类别、准确率、格式率、长度、空回答和 finish reason。
6. 与 2026-07-16 历史汇总比较。
7. Category 2 和 Category 3 各固定抽取 12 条，等待人工复核。
8. 生成完整归档、SHA-256、本地副本和独立 Git commit。

## 可靠性规则

空回答、错误答案、格式错误和达到长度上限均属于合法模型结果，必须保存并评分，不 retry、skip 或 resample。generation exception、OOM、返回数量不符、写入失败、JSONL 损坏或 ID 不连续属于基础设施错误，必须 hard stop。

## 输出范围

规范化 raw JSONL 将字段分为输入与实验控制信息、原始模型 response 与 finish reason、evaluator 派生的 parsed answer/reward/category。历史生成脚本没有保存 token IDs，因此本次保留 `response_token_ids=null` 并在完整性报告中记录，避免通过重新分词伪造原始 token ID。

人工复核包只提供原文、ground truth、parsed answer 和 grader 结果；自动分类不能作为人工复核结论。
