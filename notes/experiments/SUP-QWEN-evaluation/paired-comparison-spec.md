# 逐样本配对比较规范

状态：schema proposal-v1；尚未产生 SFT/DPO paired records。本页定义结构，不创建虚构结果 JSONL。

## 主键与字段

主键为 (dataset_revision/hash, split, task, example_id, comparison_protocol, prompt_condition)。官方主链的 prompt_version 不是一个共享值：要保存 base/sft/dpo 各自版本；2×2 使用独立组A/B/C/D，不覆盖主链。

| 字段组 | 字段和规则 |
| --- | --- |
| 输入身份 | example_id、task、dataset_hash、split、question/instruction、ground_truth、reference_output_hash、prompt_version（按模型映射）、protocol_id |
| 原始输出引用 | base_response、sft_response、dpo_response；分别保留 formatted_prompt、prompt_sha256、response_token_count、finish_reason、run_id、raw_path、raw_sha256 |
| 模型身份 | 每模型 model_revision/checkpoint_sha256、tokenizer_revision、generation_config_hash、code_commit |
| 派生结果 | base_score、sft_score、dpo_score（按指标字典）；base_error_labels、sft_error_labels、dpo_error_labels；evaluator_version/hash、parser_result、parse_status |
| Judge | judge_result，含每模型 judge_raw_ref、judge_revision、rubric_hash、reference_sha、order、parsed_label、invalid、reason |
| 审阅与数据血缘 | ai_initial_analysis、human_review_status=pending、human_notes=null、reviewer_id=null、reviewed_at=null、routing_decision、source_is_holdout=true/false |
| 缺失 | value=null + status=NOT RUN/PENDING/invalid + reason；不要写0冒充未运行分数 |

所有原文从 immutable raw 引用/复制并校验相等；新增注释是派生文件。人工标签由真实reviewer填，并保留AI初审独立版本。

## 转移矩阵

对每任务构建 Base→SFT 和 SFT→DPO 的 Correct→Correct、Correct→Wrong、Wrong→Correct、Wrong→Wrong 四格计数，均以同一 N 为分母。净准确率提升 = (Wrong→Correct − Correct→Wrong)/N；同时列修复率与回归率，不用净值掩盖退化。Judge尚未判定不作为Wrong。

从标签分析知识、推理、算术、漏答、误拒、幻觉的新增/消失。多标签的发生率分母N，标签计数之和允许>N；顶层主因另列互斥统计。区分 ParserError 修复、真实回答改善、评分器变更、只变长、正确但格式改善。示例：GSM PILOT 906 给出分项4与6却没求总数10，末尾数字提取6是当前规则行为，不自动认定 parser bug。

## Bootstrap 与多 seed

建议冻结 seed=0、10000次 paired bootstrap、95% percentile CI：每次按题ID有放回抽样，将对应模型/Prompt/Judge分数一起取出，重新计算差值和统计量。MMLU按subject分层抽样、固定各层样本量；SST按风险分层；其他按题抽。按任务分别计算，固定N与micro权重。

重复Judge判定与同一道题的多个模型输出不是独立样本。重复运行先形成题内估计，再按题cluster重采样。LC为拟合指标，若给CI应每次重新拟合同版LC模型，不能对显示的总分简单bootstrap。N_valid不一致先完成invalid审计，不挑共同“好解析”子集声称Full提升。

这些CI主要描述题目抽样不确定性，不覆盖训练seed/Judge偏差/污染。全固定benchmark的分数本身精确，外推总体才有抽样解释。PILOT CI只供诊断。多训练seed建议3个作为另批资源扩展；greedy生成改seed并不产生有意义的独立采样证据。多指标/子组探索标exploratory，不只挑显著项。

## 人工对照包

建议每次迁移分四格各随机抽最多10题，再补安全/误拒/截断/解析争议；不足如实记录，去重并保存每层概率、seed、入选原因。盲化模型名且随机左右顺序，保留GT、raw和评分来源；先独立判断再展示AI初审可减少锚定。输出仍为human pending，AI不能签署结论。高风险与争议由第二reviewer裁决，缺人手则保留限制。
