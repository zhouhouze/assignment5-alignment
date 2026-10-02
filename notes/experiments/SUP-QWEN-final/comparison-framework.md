# Qwen Base→SFT→DPO 对照框架

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

| 阶段 | MMLU | GSM8K | AlpacaEval winrate/LC | Safety |
| --- | --- | --- | --- | --- |
| Qwen Base | 未执行 | 未执行 | 未生成/未judge | 未生成/未judge |
| Qwen SFT | 未训练 | 未训练 | 未训练 | 未训练 |
| Qwen DPO | 未训练 | 未训练 | 未训练 | 未训练 |

本路线只作Qwen内部Base→SFT→DPO对照，不能凭绝对分数宣布Qwen优于官方Llama。
变动变量：policy家族/规模及预训练、tokenizer/词表/EOS/token长度与packing量、judge家族/标尺及chat包装、第三方历史SFT镜像、硬件/依赖实现/日期；Safety无效输出审计也独立披露。
即使Qwen内部，Base→SFT的外层prompt遵循官方发生变化，单seed与样本噪声仍限制因果解释；不能把变化完全归因于训练算法。

数据飞轮观察链：SFT质量/拒答/虚构体验 → 模型风格与能力 → 错误/安全审计 → HH偏好标准 → DPO helpfulness/safety及alignment tax → 下一轮数据修订（另建版本，不改raw）。
Next task：baseline pilot后补充真实样本和指标；本轮无模型结果。
