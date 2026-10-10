# Base × SFT 的 2×2 Prompt 诊断

状态：设计/比较规则FROZEN，归属[SUP-QWEN-EVAL-v1](evaluation-protocol-v1.md)；执行NOT RUN；每任务100题的样本规模仍PROPOSED，需诊断Gate批准，不阻塞P1。假设：SFT 后的表面收益可能一部分来自外层模板，且训练与模板存在交互。保留课程主评估不变，诊断结果单独发表。

| 组 | 权重 | 外层模板 | 当前状态 |
| --- | --- | --- | --- |
| A | 固定 Base | Official zero-shot | 诊断 NOT RUN（已有 Base PILOT 不等于本诊断） |
| B | 固定 Base | Alpaca | NOT RUN |
| C | 同一个验收 SFT checkpoint | Official zero-shot | NOT RUN |
| D | 同一个验收 SFT checkpoint | Alpaca | NOT RUN |

建议每任务固定100题，SST使用全部100题，MMLU按57学科分层至少每科1题，剩余额度按学科大小确定；seed=0，清单在推理前冻结。Alpaca/GSM各100随机，四组同题同序同 decoding，任务内 prompt 原文相同。100只是成本提案，不能支撑精确小效应结论。全部输出最多1600条；其中主 Full A/D 若配置/ID/原文 hash完全一致可引用，不必重生成，B/C新增800条。P1本轮定义只含Base正式候选；B须独立批准诊断Gate，C在后续SFT诊断Gate。不能将“同次加载方便”视为权限。

设某指标为 y：

- B−A：固定 Base 的 Prompt 效应。
- D−B：固定 Alpaca 的 SFT 效应。
- C−A：固定 zero-shot 的 SFT 效应。
- D−A：课程产品配置总变化，不能单独归因训练。
- 交互 = (D−C)−(B−A) = (D−B)−(C−A)。非零提示模板对两种模型的影响不同。

同一抽样ID同时重采样四组，给差值与交互 bootstrap CI；每任务分别分析，不把 accuracy 与安全率相加。Judge、reference、候选匿名化、rubric一致。判断重叠 CI 不是差值 CI，不能互换。

另记长度、截断、parse失败及指令完成，辨别“变长”与“完成更多约束”。A/D与主评估可在完全匹配时引用原raw，但报告必须标 diagnostic/subset。任一组缺失则配对结果 PENDING，不独自删题。

局限：单一训练 seed 只能说明该 checkpoint 的效果；模板交互结论仅针对这两种模板。若要强结论，另批多个训练 seed 并把 seed 与题目不确定性分开估计。
