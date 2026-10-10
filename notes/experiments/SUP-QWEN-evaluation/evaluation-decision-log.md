# SUP-QWEN-EVAL-v1 — Evaluation Decision Log

日期2026-10-10。用户批准P0设计冻结，指定模型/revision/任务规模/不运行实验边界，并明确批准SFT空字段策略。本文记录技术规范冻结与未决资源/产品决策，**FROZEN不等于对应GPU执行获批**。

审计基线commit：439f17b2f152676175b2ad2e38f2c93302a75b7e（local与origin一致）。审批来源为本轮“PA5 Supplement P0 评估协议冻结”任务；本文件归档commit由Git历史定位。未以仓库旧权限说明扩大用户当前边界。

状态：FROZEN=本轮授权范围内的已定规范；PROPOSED=可选设计提案；PENDING USER APPROVAL=需用户决定/执行授权。技术实现待办另在readiness列，不冒称用户已批准实现。

| Decision ID | Decision | Reason | Alternatives | Status | Impacted Gates |
| --- | --- | --- | --- | --- | --- |
| D01 | 采用SUP-QWEN-EVAL-v1，Qwen adapted且directly_comparable_to_official=false；模型/tokenizer/SFT源固定revision | 用户本轮明确批准P0并指定身份 | 浮动main、将Qwen称官方Llama均不采用 | FROZEN | P0–P10 |
| D02 | Full固定14042/1319/805/100共16266；ID/顺序/数据SHA见协议 | 用户明确范围；本轮CPU核对60文件及全部输入 | 成功子集分母、PILOT冒充Full不采用 | FROZEN | P1/P6/P9 |
| D03 | 保持官方zero-shot文本嵌套，无chat/few-shot；greedy0/1、seed0、512、batch4、# Query: stop、EOS151643及原engine | handout规定greedy并解释stop；其余沿用真实smoke/pilot，不按分数调参 | 增加长度/改stop需新版独立诊断；512不是handout强制推理上限 | FROZEN | P1/P6/P9、Prompt诊断 |
| D04 | MMLU既有选项parser；GSM既有final-number+Decimal；None计错进N | handout与现有通过测试的parser一致 | 不复用Main boxed、不人工替换主score | FROZEN | P1/P6/P9 |
| D05 | 指标分类及公式按metrics spec；无Judge实测为NOT RUN，LC兼容NOT VALIDATED | 用户要求分开Primary/Guardrail/Diagnostic与运行/验证状态 | 不填0、不写虚构分数 | FROZEN | P0/P1/P6/P9 |
| D06 | P95为ceil(.95N)−1；empty主计数为literal空串，whitespace-only单列 | 审计发现旧提案误称floor分位与strip-empty和runner一致；本轮显式纠正文档，保留真实既有口径 | 不改历史metrics、不偷偷改变parser/runner；新blank诊断另字段 | FROZEN | P1/P6/P9 |
| D07 | A Base-zero、B Base-Alpaca、C SFT-zero、D SFT-Alpaca；固定同题比较与interaction公式 | 用户明确2×2及因果解释边界 | D−A不能全部归因SFT；B/C不进主表 | FROZEN | P1可引用A、P6、诊断 |
| D08 | SFT Data Acceptance Policy v1仅排空串/纯空白prompt或response；raw不改，实际过滤NOT RUN | 用户本轮明确批准策略、不批准执行 | 不自动删重复/长短/错误/不完整/拒答/风格差异 | FROZEN | P2 |
| D09 | Judge身份/rubric/血缘；严格true/false；invalid不算safe；compat与strict并报；mock→smoke→pilot→人审→Full | 用户明确可靠性准则；已有官方非true即safe逻辑需审计 | 不把invalid当tie或safe；不跳过可靠性Gate | FROZEN | Judge/P9 |
| D10 | 统一human review字段/状态；原27条pending不改，seed0分层/ID保存；争议sidecar | 用户明确人工与AI状态分离 | 不能由AI补human字段或重生成同一27条包冒充新审阅 | FROZEN | P1/P2/P6/P7/P9/P10 |
| D11 | Error Taxonomy v1和Routing v1为候选规则；来源/隐私/去重/隔离/人工准入后才可训练 | 用户要求数据飞轮及holdout保护 | 自动将失败题加训练不采用 | FROZEN | P2/P7/P10及下一周期 |
| D12 | 逐题schema、四格转移、bootstrap seed0/10000次/95% paired percentile，CI只覆盖题目抽样范围 | 用户要求配对分析；这是CPU计算约定而非质量阈值 | 不把单seed CI称全训练/生成随机性；不按显著性挑指标 | FROZEN | P6/P9 |
| D13 | 合法坏输出保留；infra hard stop/partial；恢复要证明批账本与已保存raw一致，不重抽坏答 | 用户异常保护与可验证恢复要求 | 删除failed/pending直接重跑、丢失ID算0均不采用 | FROZEN | P1/P6/P9 |
| D14 | P0技术完成不要求数值产品阈值；产品决策保持未决且不阻塞P1观察性评估 | 用户本轮第十二/十六节明确 | 凭空指定准确率、安全率、退化pp阈值不采用 | FROZEN | P0/P1、产品决策 |
| D15 | P1只收7B Base candidate及现有可执行评分，不运行72B/Judge诊断B/C/SFT/DPO/Main | 用户范围明确；P0不授予P1执行 | 自动跨Gate不采用 | FROZEN | P0/P1 |
| D16 | 当前P1 generation readiness=BLOCKED；下一步先CPU Full runner/恢复/IO验收 | select非PILOT只取1条，CLI/run排除FULL，manifest仍描述PILOT；已有部分恢复不足以证明Full可靠 | 不因smoke/pilot完成就声称可直接启动Full；本轮不实现 | FROZEN | P1 |
| D17 | 冻结protocol组成文件使用同一归档commit；后续manifest引用protocol commit/SHA与实际代码commit | 可追溯，避免自引用提交SHA循环和未来文档漂移 | 不在历史raw补写新字段，不将归档commit误作执行commit | FROZEN | 全部Gate |
| D20 | 2×2每任务100题；benign50+harmful50；额外自动重复探测器 | 延续上一提案，样本成本和来源尚未获批；人审重复定义已冻结 | 可改规模/暂不做，不影响P1四任务 | PROPOSED | 诊断/P6/P9，不阻塞P1 |
| D21 | SFT/HH/Full review人数、规模、预算，争议二审安排 | 本轮只批准review规则，不虚构人工资源 | 沿用现有27条优先；扩展按成本批准 | PENDING USER APPROVAL | 人审完成、P2/P7/Judge；不阻塞P1自动评分 |
| D22 | P1新执行授权、具体GPU/租费上限、持久存储恢复方案 | 用户本轮仅P0；现场权重/GPU/磁盘未查，不能从旧记录认定可用 | 先CPU准备，不先租长期GPU | PENDING USER APPROVAL | Blocks P1 generation |
| D23 | SFT实际过滤/准入执行、optimizer dtype/硬件、checkpoint选择；DPO优化细节/长度 | 训练尚未执行，所需精度/费用/数据风险未验收 | 维持全参课程路线，不自动LoRA/量化绕过 | PENDING USER APPROVAL | Blocks SFT / DPO；不阻塞P1 |
| D24 | Judge样本/人员/预算、单或双顺序Full、设备调度；异家族样本与LC验收 | 可靠性检查方法冻结，实际资源与custom annotator兼容未证实 | 小规模先验收；无效/不兼容保持NOT RUN/NOT VALIDATED | PENDING USER APPROVAL | Blocks Judge/P9；不阻塞P1 |
| D25 | 能力退化容忍、安全与帮助性取舍、误拒/用户满意度目标 | 缺真实产品场景；本轮明确不得杜撰 | 先做描述性学习，后按产品目标批准 | PENDING USER APPROVAL | Product quality decision only，不阻塞P1 |

## 差异处置记录

- Handout未固定推理max_tokens=512；这是已运行Qwen工程选择。沿用并披露，不写成官方强制要求。
- 旧metrics提案的P95 floor公式与runner不一致；按现有nearest-rank纠正。N=20时两式恰好同索引，不代表所有N等价。
- 旧提案empty用strip，但runner计literal空串。保留legacy主指标，增设blank/whitespace诊断规范，既有raw/scored/metrics不改。
- 旧Judge“位置翻转>10%/agreement<80%”为未批准示例，本轮从验收要求移除，不把它们冻结为产品/可靠性成功门槛。保留实际分布、人工裁决和技术有效性要求。
- 无实际Judge分数统一NOT RUN；LC方法状态NOT VALIDATED；不能把单一PENDING含糊地表示已经运行。

## 后续变更规则

新增决策必须注明被替代的Decision ID、影响Gate与必要重算，不覆盖旧结果。P1实现可变更runner源码/实现commit，但不得变更冻结输入/Prompt/sampling/parser语义；新代码manifest引用新的实际源码hash。发现协议本身错误须新版决策/协议，而不是边跑边调。
