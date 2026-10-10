# Qwen Base→SFT→DPO 对照框架

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

| 阶段 | MMLU | GSM8K | AlpacaEval winrate/LC | Safety |
| --- | --- | --- | --- | --- |
| Qwen Base（PILOT，非FULL） | 15/20；75% | 17/20；85% | 20条candidate；未judge | 20条candidate；未judge |
| Qwen SFT | 未训练 | 未训练 | 未训练 | 未训练 |
| Qwen DPO | 未训练 | 未训练 | 未训练 | 未训练 |

本路线只作Qwen内部Base→SFT→DPO对照，不能凭绝对分数宣布Qwen优于官方Llama。
变动变量：policy家族/规模及预训练、tokenizer/词表/EOS/token长度与packing量、judge家族/标尺及chat包装、第三方历史SFT镜像、硬件/依赖实现/日期；Safety无效输出审计也独立披露。
即使Qwen内部，Base→SFT的外层prompt遵循官方发生变化，单seed与样本噪声仍限制因果解释；不能把变化完全归因于训练算法。

数据飞轮观察链：SFT质量/拒答/虚构体验 → 模型风格与能力 → 错误/安全审计 → HH偏好标准 → DPO helpfulness/safety及alignment tax → 下一轮数据修订（另建版本，不改raw）。
本表Base只有固定20条/任务的PILOT，不是最终benchmark成绩。见[分析报告](../SUP-QWEN-01-baseline/pilot-report.md)。Next task：待批准后FULL Baseline；SFT/DPO与Judge仍未执行。


## 2026-10-10 评估协议提案

后续统一使用[评估/数据飞轮计划入口](../SUP-QWEN-evaluation/README.md)与[Full scorecard模板](model-evaluation-scorecard.md)。上轮439f17b时状态为proposal-v1、P0审批PENDING；当前状态见下方P0冻结记录，不修改以上历史实验事实；现有PILOT不填入Full结果。


## P0技术协议已冻结

当前统一规范为[SUP-QWEN-EVAL-v1](../SUP-QWEN-evaluation/evaluation-protocol-v1.md)，替代上方proposal状态；P1工程readiness仍BLOCKED。Judge无实测NOT RUN，LC NOT VALIDATED；主表不得填PILOT数值。
