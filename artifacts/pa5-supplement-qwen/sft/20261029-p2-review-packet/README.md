# P2 精简人审包（待学习者独立审核）

首次阅读只打开 `train-20.jsonl`、`validation-20.jsonl` 和单列的 `diagnostic-refusal-3.jsonl`。每条保留完整 Prompt/Response、Raw 源指纹和行号、Derived-v1 行号；所有人工字段为空，`human_review_status=pending`。**不要先打开** `after-independent-review/ai-initial-analysis-train-20.jsonl`；完成独立判断后再把历史 AI 意见作为对照。3 条定向诊断样本不计入随机组频率。

Train 20 沿用历史从 210348 条 Raw 中以 seed0 无放回抽样的身份，原始包为 `artifacts/pa5-supplement-qwen/preflight/20261002/acceptance-v2/review-packet.jsonl`；不是从 Derived-v1 的 210326 条中重新抽样。Validation 20 从 Derived-v1 的 23108 条中以 `sorted(random.Random(0).sample(range(1, 23109), 20))` 抽出；1-based、无放回，入选概率均为20/23108。具体 ID、输入 SHA、包内文件 SHA 见 `manifest.json`。生成命令：`python3 scripts/prepare_qwen_sft_review_packet.py --output artifacts/pa5-supplement-qwen/sft/20261029-p2-review-packet`；输出目录已存在时必须停止，恢复时使用新目录。

定向风险证据只引用既有 [P2-B.1 报告](../../../../notes/experiments/SUP-QWEN-data-flywheel/p2-b1-contamination-audit-report.md)及 [三例全文对照](../../../../notes/experiments/SUP-QWEN-data-flywheel/p2-b1-classroom-cases.md)：候选 #1 新闻材料跨 split，#3273/#3274 AlpacaEval 完整问答，#2737 长文包含短引文。它们是机器候选，不是人工污染裁决；不得据此改写或删除数据。

本包只表示准备完成。学习者尚未提交质量标签、严重度、审阅理由、审核人、时间或重大风险处置；Data Admission 仍为 PENDING / NOT APPROVED。无 P3、训练或 GPU 执行。
