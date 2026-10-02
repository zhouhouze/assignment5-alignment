# Supplement概念图谱

Base + zero-shot提示 → 四类baseline（知识/数学/assistant quality/安全）。

SFT：instruction-response demonstrations → packed next-token训练 → 观察指令遵循、风格、能力和安全变化。

DPO：固定SFT reference + chosen/rejected pair → 提升相对偏好概率 → 检查偏好收益与能力损失。

评估证据：raw输出 → 可复算parser/judge → 指标 → 人工复核 → 有边界的结论。标签格式、外层prompt与judge错误均可能成为混杂因素。

2026-10-02：运行代码commit → manifest（配置/版本/hash）→ immutable raw → 新版scored → metrics → report → Git归档commit。归档成功与实验成功分别记录，partial/failed不能冒充full。
