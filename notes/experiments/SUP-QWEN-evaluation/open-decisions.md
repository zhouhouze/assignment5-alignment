# 待用户决定的关键事项

状态：PENDING，以下是建议而非代用户批准。可以分Gate作决定；P0不要求提前选定尚无pilot证据的具体GPU，但必须同意后续实测再报价的边界。

| 决策 | 推荐提案 | 最晚时点 / 未决影响 |
| --- | --- | --- |
| 主指标及胜负定义 | 四任务分开；不做任意加权总分；Guardrail包含安全/解析/空/length | P0；定义未冻不跑Full |
| 可接受退化与收益 | 用户给MMLU/GSM非劣界、安全/误拒容忍度、最小有用收益；同时报告CI，不只p值 | P0至少确认“观察性学习、暂不作上线决策”或具体阈值；无阈值不宣称产品验收通过 |
| Judge invalid和tie | strict安全分母N、invalid不算safe；Alpaca tie=.5，invalid>0主结论PENDING且报界限 | P0 |
| Prompt/stop和长度 | 主评估保持既有512/4096及# Query: stop，SFT/DPO同参数；超长先暂停，不裁题 | P0；2×2可比性依赖 |
| 2×2样本规模 | 每任务100题固定seed0，A/D精确匹配可引用Full | P0；额外B/C generation须明确授权 |
| bootstrap与seed | 10000次95% paired bootstrap；主训练seed0；多seed作为另批扩展 | P0；单seed限制必须披露 |
| benign/harmful诊断 | 独立50+50，来源许可、rubric与样本冻结；不混课程分数 | P0先定是否纳入首轮；未做则false refusal PENDING |
| SFT空白规则 | strip()==空串仅作检测，不改非空原文；只排空字段 | P2之前需明确审批，原始数据保持不可变 |
| 人审规模/预算/人选 | SFT100随机+50分层+20val；HH100对上限；Judge40案例，争议二审 | 对应Gate开始前；可缩规模但披露不确定性，不由AI签字 |
| optimizer精度与训练设备 | 先统计实际dtype/memory，首步实测，不默认80GB足够；分片方案另批 | P3/P4；决定数值/成本，不自动替换LoRA |
| checkpoint选择 | SFT固定1epoch最终；DPO按handout policy val classification，同分低val loss再早step | P3/P7冻结，不用benchmark挑选 |
| DPO长度和RMSprop细节 | 按HH真实长度预检再定max length；不默认512；固定alpha/eps等 | P7；超长策略影响偏好含义 |
| Judge运行预算及顺序 | 先82calls以内smoke/reliability；Full单顺序2715calls或双顺序5130calls | Judge开始前明确；双顺序聚合/冲突处理需事前冻结 |
| LC可靠性/同家族审计 | 先验自定义Qwen LC；异家族样本/额外Judge需明确资源和使用许可 | Judge Gate；不可用项目保持PENDING，不替用别的标尺 |
| 存储/租费上限 | 选择持久云盘或已授权LFS、容量与保留checkpoint数；声明GPU小时/金额上限 | 各GPU Gate；未知费用不执行Full |
| 训练回流授权 | holdout只用于回归；独立来源新数据逐版本审批；线上数据另有许可/隐私要求 | P10/下一周期；本计划不授权自动数据回流 |

推荐下一次仅处理P0设计冻结与P1范围/预算。批准记录应包含decision_id、日期、审批人、选项、理由、protocol commit、授权Gate和额度；无批准则保持PENDING。
