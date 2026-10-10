# 产品行为分析报告模板

状态：PENDING。模型行为、人类偏好与实际产品价值分层表述；所有人工审阅字段pending，除非真实review记录支持。

| 产品问题 | 需要的证据 | 当前结论 |
| --- | --- | --- |
| SFT是否更会完成任务？ | completion/constraints、paired wrong→correct与退化原文 | PENDING |
| 是否只是更像助手/更长？ | 固定模板对比、长度/重复/截断、任务完成对照 | PENDING |
| DPO改变什么偏好？ | HH来源标签、固定SFT→DPO paired、Judge与人审 | PENDING |
| 是否以拒绝换安全分？ | SST strict安全+独立benign误拒+unsafe compliance | PENDING |
| 是否付出alignment tax？ | MMLU/GSM配对差、CI、回归案例 | PENDING |
| Judge是否可信/可复现？ | invalid/order/length/repeat/human audit和限制 | PENDING |
| 成本与延迟是否可接受？ | 同硬件/同口径吞吐、token、加载与Judge/人审成本 | PENDING |
| 能否宣称用户满意度提高？ | 独立真实用户/任务结果验证，不由Judge分数替代 | PENDING |

每条案例记录：example_id、模型/Prompt身份、三份原文、GT/评分、AI初审、人工status/notes、错误机制、证据强度、反例与产品影响。不得仅挑改善样例。

总结模板：观察到的变化=PENDING；因果可归属部分=PENDING；混杂/样本限制=PENDING；不可声称的结论=PENDING；下一步最小验证=PENDING。学习者解释状态=PENDING，不代用户宣称已理解。
