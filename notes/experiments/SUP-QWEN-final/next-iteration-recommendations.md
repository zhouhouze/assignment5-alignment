# 下一轮实验与数据优先级模板

状态：PENDING；P10之后才能填实证建议，不授权现在构建数据或再训练。

| Issue / evidence | Severity / frequency | Route / reason | Independent source / rights | Expected metric / guardrail | Human status | Cost / priority | Next approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |

排序建议：先解决污染/评分可靠性，再处理严重安全错误，再处理有充分样例支持的任务失败，最后考虑风格与成本优化；最终排序由用户目标和证据决定，不把发生频率当唯一优先级。

每项只变一个主要变量，预先固定独立train/val/test和验收指标，记录预计标注与GPU开销。正式holdout原题只入regression/evaluator审计，不流入训练。新一轮数据候选和accepted集分开，来源/隐私/去重/质量/审批完整后才进入训练。

待填：上一轮修复与回归列表、未决风险、拒收候选及原因、候选量/人审覆盖、预算、成功/停止条件、复现实验版本与用户批准范围。所有当前数值NOT RUN。
