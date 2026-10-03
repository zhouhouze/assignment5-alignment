# Supplement概念图谱

Base + zero-shot提示 → 四类baseline（知识/数学/assistant quality/安全）。

SFT：instruction-response demonstrations → packed next-token训练 → 观察指令遵循、风格、能力和安全变化。

DPO：固定SFT reference + chosen/rejected pair → 提升相对偏好概率 → 检查偏好收益与能力损失。

评估证据：raw输出 → 可复算parser/judge → 指标 → 人工复核 → 有边界的结论。标签格式、外层prompt与judge错误均可能成为混杂因素。

2026-10-02：运行代码commit → manifest（配置/版本/hash）→ immutable raw → 新版scored → metrics → report → Git归档commit。归档成功与实验成功分别记录，partial/failed不能冒充full。

## 2026-10-02 Qwen adapted preflight

Adapted reproduction → 固定policy/judge/tokenizer/data revision → CPU验收 → baseline → Alpaca+EOS SFT → 同SFT checkpoint policy/reference DPO；模型/评估标尺与prompt confounder必须披露。数据schema / 内容质量 / 人工复核为不同Gate。

## 2026-10-02 Qwen Baseline CPU Gate

新增qwen_baseline runner、独立Gate配置与7B限定下载脚本；四任务CPU准备通过，42项测试通过。raw逐请求独立封存，scored按版本派生；合法空答保留，pending/infra失败阻断自动恢复。无训练核心变更，学习解释pending。下一步按已授权范围进行SMOKE→PILOT。

## Qwen Baseline GPU Gate（2026-10-03）

配置/来源冻结 → 权重验收 → SMOKE链路验收 → PILOT行为诊断 → immutable raw → versioned scoring → 独立复算 → AI分析与human review分离 → Git证据。GSM906：分项正确≠给出要求总数；Alpaca111：流畅文本≠完成指令。stop标记被剥离≠模型未尝试续写下一题。小样本pilot≠正式benchmark。理解状态pending。
