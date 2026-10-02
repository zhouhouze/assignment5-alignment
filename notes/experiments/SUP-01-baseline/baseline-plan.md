# SUP-01：Zero-shot baseline执行计划（未执行）

日期2026-10-02。目标是建立Base Llama3.1 8B在知识、数学、assistant quality、安全四个维度的基线，不复用Main PA5结果或grader。

## 准入

Gate A blocker解决；模型与tokenizer固定为SUP-00记录revision；数据与prompt hash核对。2026-10-02两个parser已实现，4项官方test_metrics通过，详见parser-report.md；完整baseline runner尚未实现。8B加载使用Transformers或vLLM，无Trainer。模型访问、小文件检查先于大权重下载；70B此阶段不下载、不启动。

## 分阶段执行

1. Parser：逐个读取docstring/tests，明确输入/输出、歧义/空答/负数/小数/千分位等规则，不通过测试前不开全量。无数字返回None，MMLU无法识别A/B/C/D返回None；不利用gold猜答案。
2. Runner：独立Supplement入口与配置；任务格式化→Base system wrapper→greedy生成→解析→raw持久化→指标。读取官方prompt文件，不手抄，不自动套Instruct chat template。
3. CPU dry run：核对样本ID、总数、task/system prompt hash、数据划分与最终manifest；不加载模型。
4. 8B smoke：每benchmark 1条，确认tokenizer、BF16、停止词、数量和持久化；再每组20条pilot（MMLU按subject分层），检查输出长度与显存。
5. Freeze generation config，再独立完整运行MMLU test14042、GSM8K test1319、AlpacaEval805、Safety100，共16266条；不同时跑第二个实验。
6. 从raw离线重算MMLU/GSM8K指标，生成AlpacaEval兼容JSON数组与Safety兼容导出。生成阶段完成不等于完整Baseline Review通过。
7. 另获资源/批准后，用固定70B judge进行AlpacaEval与Safety标注，复算指标并抽人工样本。正式四列表完成后停在Baseline Review Gate，不自动进入SFT。

## 配置

- 模型：meta-llama/Meta-Llama-3.1-8B，revision/tokenizer revision `d04e592bb4f6aa9cfee91e2e20afa771667e1d4b`（访问尚未通过）。
- temperature=0.0，top_p=1.0，n=1；seed=0作为运行记录，greedy也不保证跨环境逐token完全相同。
- Base stop=["# Query:"]，include_stop_str_in_output=False；保留finish_reason和stop_reason。
- 规划起点（不是官方指定值）：max_tokens=512，max_model_len=4096，gpu_memory_utilization=0.75，提交batch=4。先以tokenizer核对所有prompt是否容纳，发现过长不静默截断；pilot决定配置后冻结，完整baseline不得边跑边改上限。
- Post-SFT/DPO尽量固定任务模板、数据、parser、生成上限和judge；按官方要求外层改为Alpaca模板，其停止规则需在阶段开始前固定并记录。清楚披露prompt confounder，必要时额外做同模板控制评估，单列结果。

## 指标与人工复核

| Benchmark | 输入/解析 | 指标 | 人工包 |
| --- | --- | --- | --- |
| MMLU | test57科，task→system，解析A/B/C/D | overall micro accuracy、per-subject accuracy、parse failure计数/率 | seed0分层抽10个错误，含parse failure |
| GSM8K | task为question+Answer，解析输出最后一个数字；gold从数据answer末尾标准答案段提取 | accuracy、parse failure计数/率 | seed0抽10错题，区分数学错与解析错 |
| AlpacaEval | instruction→system；导出instruction/output/generator/dataset的JSON数组 | 固定70B vs固定GPT4-Turbo reference的winrate/LC winrate | 至少10个输给reference的例子，检查长度偏差和judge分歧 |
| Safety | instruction→system；兼容字段prompts_final/output | safe-output proportion、judge_invalid_count及分母 | 至少10个unsafe；再抽safe检查漏报；不足10则全取并说明 |

parse failure计入整体错误，不从accuracy分母删除。通用指标：样本数、empty/length count、finish_reason分布、response token分布、生成耗时、examples/s、tokens/s、启动/加载耗时分开记录。批处理不把整批latency伪称逐请求延迟：记录batch_id/batch_latency和计时口径；没有逐请求实测时latency=null。

人工包保留原文、gold、parser/judge输出、选择seed和样本ID；human_label/notes默认null。模型或Codex的分析只标“自动辅助分析”，不能当人工结论。Baseline所有人工复核完成后才报告human reviewed。

## 原始产物

每次run：`artifacts/pa5-supplement/baseline/<benchmark>/<run_id>/` 下保存manifest.json、environment.json、raw.jsonl（不可覆盖）、scored-<evaluator-version>.jsonl、metrics.json、run.log、SHA256SUMS。未来SFT/DPO分别使用`sft/{train,checkpoints,eval}`、`dpo/{train,checkpoints,eval}`，不写Main产物路径。

raw公共字段：run_id、example_id、benchmark、split、question/instruction、formatted_prompt、response（完整原文）、response_token_count、finish_reason、stop_reason、batch_id、latency、generation_status、模型与采样参数。MMLU增加subject/options/gold_answer/parsed_answer/correct/parse_failure；GSM8K增加gold原文与提取值；judge单独存原始输入/输出、解析标签、invalid标志、版本/hash和response关联ID。

manifest固定code commit及dirty状态、model/tokenizer revision、每份dataset/prompt/evaluator hash、judge revision和模板hash、GPU/驱动/Python/依赖版本、seed、generation params、计时口径；模型尚未访问到的字段必须标unverified，不能假装锁定已经落盘。

合法empty/malformed/wrong/length输出保留评分，不retry/skip/resample。generation exception、OOM、count/ID mismatch、写入失败或损坏JSONL hard stop，保留partial与失败日志；恢复必须明确run ID、已完成ID和重复检测策略。指标必须从已校验raw重算。

## Review交付

完成后创建baseline-results.md、evaluator-analysis.md、error-analysis.md；当前仅有计划，不创建带虚假分数的结果报告。

| Model | MMLU | GSM8K | AlpacaEval winrate / LC | Safety |
| --- | --- | --- | --- | --- |
| Base（尚未生成/评估） | pending | pending | pending judge | pending judge |

Safety helper现有解析将非true输出当safe，需要保留官方可复算分数，同时单列有效True/False与invalid审计；invalid>0先排查，不用默认safe完成Gate。两者不能混报。AlpacaEval待检查ranking解析失败/平局处理，不能跳过后只报告胜率。
