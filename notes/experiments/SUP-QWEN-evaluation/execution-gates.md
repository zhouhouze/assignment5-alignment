# P0–P10 执行 Gate 与资源安排

日期2026-10-10；全部未来执行Gate为NOT RUN，P0文档已准备但approval=PENDING。本轮只归档本计划。任何Gate“通过”不自动授权下一Gate；如同一批明确授权多个CPU阶段，仍分别验收与记录。

建议依赖顺序：P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10。P2/P3可经授权在P1后处理/等待Judge时用CPU推进，不占第二个GPU实验；P7文档调查可前移但DPO初始化必须等SFT checkpoint。

P1/P6在Judge尚未验收时只关闭raw/自动评分子阶段，Alpaca/Safety质量门槛PENDING。Judge可靠性mock/smoke/pilot必须在任何Full Judge之前，最迟在P9先完成；不把P9顺序理解成先Full再验Judge。需要提前得到完整SFT质量判断时，可单独批准将Judge子Gate前移。

所有时间为计划估算或公式，不是租期保证。费用=Σ(卡数×墙钟小时×该卡小时单价)+存储/传输+人工；价格/可用型号/网络/排队均PENDING。多卡1小时不是1 GPU-hour。

## P0 — Evaluation Design Freeze

**Objective**：确认要回答的问题、统计口径、可归因范围和可承受成本。当前文档已准备，design freeze approval=PENDING。

**Inputs**：本计划、当前状态核验、2026 handout、历史PILOT及归档规范。

**Execution Tasks**：用户审阅open-decisions；确定主/诊断指标、Prompt/stop、数据ID、Judge invalid/tie/LC、guardrail非劣界、review预算；记录审批版本，不通过口头“继续”推断无限实验范围。

**Metrics**：未决项数量、协议字段完整率、现有证据覆盖；本阶段无模型分数。

**Acceptance Criteria**：全部执行阻断项有明确决定/延期范围，固定proposal版本和批准的下一Gate；延期Judge不等于批准缺项结论。

**Failure / Stop Conditions**：指标/样本/模型版本不一致；关键分母或预算尚无共识时不启动GPU。

**Deliverables**：已批准protocol/scorecard/gates及decision log。当前仅proposal文档。

**GPU Requirements**：无GPU；本地阅读与CPU验证。

**Expected Cost and Time**：估算用户审阅30–60分钟，复杂口径另计；GPU费用0。计划编写已在本轮完成，不计为模型实验时间。

**Next Gate Approval**：明确批准P1的Full Base raw+自动评分范围；P2/P3 CPU工作如要并行需明确列入。不能自动跨Gate。

## P1 — Full Base Baseline

**Objective**：建立可靠的四任务全量Base原始输出与自动评分基线。

**Inputs**：P0冻结协议、已通过Base smoke/pilot、固定模型权重/数据SHA、可用GPU和批准预算。

**Execution Tasks**：CPU全量ID/长度预检→启动前显存/磁盘核查→四任务16266条generation→MMLU/GSM复算→原文review/归档；Prompt B诊断若获单独授权可同次加载串行做。

**Metrics**：各任务N/N、accuracy、parse/empty/length、tokens与batch throughput；Alpaca/Safety Judge分数PENDING。

**Acceptance Criteria**：四任务完整raw和checksum、自动指标独立复算、坏输出未丢弃；称generation阶段完成，Judge质量待P9。

**Failure / Stop Conditions**：OOM/异常/数量不符/写失败/超长/损坏hard stop；不根据分数低重跑。

**Deliverables**：Full raw/manifests/metrics/logs/review/checksums、Base Full阶段报告和external registry。

**GPU Requirements**：已实测可推理的1×RTX5090 32GB或等效验收硬件；本计划不表示当前云GPU已检查。

**Expected Cost and Time**：粗估纯生成约1.44小时，来自各任务20条PILOT速率外推（见下）；建议预留2–4 GPU小时含加载/长尾/归档，不含Judge和人工，排队/网络另计；工程准备1–3小时估算。

**Next Gate Approval**：归档后单独批准P2；P1 Judge部分明确PENDING，不自动启动72B。

## P2 — SFT Data Acceptance

**Objective**：得到可追溯且明确获批的SFT派生数据视图和质量风险记录。

**Inputs**：原始三文件固定SHA、24异常清单、空白定义和过滤批准、审计预算。

**Execution Tasks**：按data-quality-plan重新验证schema→只排除获批空字段→保留行号→split隔离/污染审计→随机与分层复核。

**Metrics**：有效/排除计数、overlap、质量标签/严重度、human覆盖；来源不可识别则明确unknown。

**Acceptance Criteria**：派生SHA可复算、原始不变、数量差异有解释、无未处置隔离问题、约定人审完成；重大风险有决定。

**Failure / Stop Conditions**：新schema异常、未经审批的清洗范围、split泄漏、重大安全争议未裁决。

**Deliverables**：exclusions、derived manifest与数据引用、质量报告、review packet。

**GPU Requirements**：无GPU，CPU/磁盘即可；不为此续租GPU。

**Expected Cost and Time**：机器扫描/派生估算0.5–2小时；提议170条人审按2–5分钟约5.7–14.2人时，含复核可更长；规模可审批缩减，披露覆盖。

**Next Gate Approval**：明确批准P3一个核心组件开始；人审未完成不得说训练准入已通过。

## P3 — SFT CPU Implementation

**Objective**：实现且理解Dataset、batching与自写训练循环。

**Inputs**：P2 accepted view、官方docstrings/tests、SFT training design、学习者逐组件解释。

**Execution Tasks**：按项目流程读docs/tests→说明shape/math/edge→最小编辑→窄测试；验证packing/shift/accumulation/optimizer/resume/val；逐组件学习检查。

**Metrics**：官方相关tests、toy梯度/恢复对照、数据覆盖和训练/验证隔离。

**Acceptance Criteria**：新组件测试通过；GRPO已有NotImplemented明确分类、无新增回归；学习者解释状态诚实记录。

**Failure / Stop Conditions**：错误shift/mask/丢尾batch/梯度断开/无法恢复；学习理解关键缺口先澄清。

**Deliverables**：可解释的实现、测试日志、CPU sanity、配置草案、学习记录。

**GPU Requirements**：无GPU；tiny model CPU即可。

**Expected Cost and Time**：工程估算8–16小时，包含学习检查，不是已实测工时/交付承诺；复杂环境问题另计。

**Next Gate Approval**：批准P4硬件方案及仅smoke/pilot的GPU预算；通过测试不自动租卡。

## P4 — SFT Smoke / Pilot

**Objective**：证明训练可运行、状态精度/显存/吞吐可接受且能恢复。

**Inputs**：P3测试通过、具体硬件预算与数据subset、精度/optimizer参数冻结。

**Execution Tasks**：1–2step smoke→验收→固定1000示例1epoch约32step pilot→保存/恢复→验证loss；smoke或pilot失败先停。

**Metrics**：finite loss/grad、参数更新、state dtype、step时间、tokens/s、peak VRAM、resume一致性。

**Acceptance Criteria**：没有数值/数据/恢复缺陷；有full step数与可信耗时/存储预算；成功加载模型不算通过。

**Failure / Stop Conditions**：OOM/NaN/ref或数据hash错误/错误累积/恢复失败；改变硬件或核心精度另审批。

**Deliverables**：smoke/pilot报告、state/memory inventory、时间区间和Full报价。

**GPU Requirements**：大显存全参AdamW设备先审预算；80GB单卡不是保证；必要时获批状态分片，不默认LoRA/量化。

**Expected Cost and Time**：仅工程排程建议预留1–3 GPU小时做验收，非训练速度预测；型号/单价PENDING，下载排队另计。实际pilot给出P5预算。

**Next Gate Approval**：用户验收测量值并单独批准P5 Full；不以pilot通过自动Full。

## P5 — Full SFT

**Objective**：在固定数据视图上完成一次完整全参数SFT。

**Inputs**：P4通过、Full预算批准、参数与checkpoint策略冻结。

**Execution Tasks**：1epoch训练/固定validation/保存checkpoint和resume状态→完整性与恢复验证→归档。

**Metrics**：train/val token CE、lr、grad norm、step/tokens throughput、VRAM、有效tokens/epoch覆盖。

**Acceptance Criteria**：有效数据一epoch覆盖、状态可恢复、最终模型/tokenizer持久保存、指标可追溯；不要求人为设定必涨benchmark。

**Failure / Stop Conditions**：非finite、OOM、数据漂移、磁盘不足/损坏、配置变更；不能自动改batch/epoch继续。

**Deliverables**：SFT checkpoint+tokenizer、resume state、训练报告/曲线/manifest/校验和。

**GPU Requirements**：使用P4验收过的具体硬件/并行策略。

**Expected Cost and Time**：NOT MEASURED：Tload+ceil(floor((Ttokens−1)/512)/32)×tstep+Tval+Tsave+Tarchive；须P4补上下界再批准GPU小时，当前不能报可靠固定时长。

**Next Gate Approval**：批准P6 Post-SFT评估，固定待评checkpoint SHA。

## P6 — Post-SFT Evaluation

**Objective**：确定相对Base的能力/行为变化并拆解Prompt混杂。

**Inputs**：P5 checkpoint、P1 raw、冻结协议、2×2诊断清单、已批准范围。

**Execution Tasks**：四任务SFT Full generation/复算；获批后生成B/C诊断缺项→paired迁移/CI→人审；Judge尚未通过则相关分数PENDING。

**Metrics**：Base→SFT修复/退化、主指标、guardrail、长度与2×2效应/交互。

**Acceptance Criteria**：raw N/N、同题同评价版本、主结果与诊断分离、未完成Judge不写结论、风险如实报告。

**Failure / Stop Conditions**：infra失败/数据或prompt漂移/试图用benchmark调checkpoint；退化保留并评审，不删结果。

**Deliverables**：Post-SFT报告、配对表、诊断结果、人审包和checkums。

**GPU Requirements**：单7B推理验收设备；训练进程先退出。Judge另Gate。

**Expected Cost and Time**：暂预留2–5 GPU小时作排程估算，SFT输出可能显著变长；先小批测时间再更新；人审按实际抽样×2–5分钟另计。

**Next Gate Approval**：明确批准P7 CPU数据/实现工作；若性能退化，用户决定调查还是继续课程DPO。

## P7 — DPO Data / Implementation

**Objective**：建立HH单轮偏好数据和经过测试的DPO组件。

**Inputs**：四个官方HH来源、同一个accepted SFT checkpoint、DPO审计/训练设计。

**Execution Tasks**：官方单轮过滤/来源保留/validation分组隔离→3+3样例及分层review→实现loss/loop→reference冻结和toy/resume测试。

**Metrics**：各源有效pair、争议/长度分布、人审覆盖、DPO loss测试、无reference梯度。

**Acceptance Criteria**：可复算数据manifest、隔离validation、核心tests通过、分类准确率/选择策略/最大长度已冻结。

**Failure / Stop Conditions**：前缀不一致/边界歧义/泄漏/reference更新/错误mask或跨设备梯度，先停。

**Deliverables**：HH audit report、split IDs、实现/tests、硬件预算。

**GPU Requirements**：CPU阶段无需GPU；跨真实GPU验证属于下一Gate。

**Expected Cost and Time**：工程估算6–12小时；100对审阅按3–6分钟约5–10人时另计，预算不足可批准先6对但须披露质量证据不足。

**Next Gate Approval**：批准P8a smoke范围和设备，不自动批准P8c Full。

## P8 — DPO Smoke / Full

**Objective**：验证再完成一次课程DPO，保留明确的smoke/pilot/full子Gate。

**Inputs**：P7通过、SFT policy/reference同SHA、RMSprop设置和长序列/显存方案。

**Execution Tasks**：P8a 1–2step smoke→单独验收P8b固定subset pilot→根据实测重新报价→单独批准P8c 1epochFull；每阶段独立run归档。

**Metrics**：DPO train/val loss、两种pref accuracy、四种logprob及margins、gradient/lr/throughput/VRAM。

**Acceptance Criteria**：各子Gate数值有限、reference不变、checkpoint可恢复；Full按预注册val口径选最佳，不查看benchmark挑模型。

**Failure / Stop Conditions**：OOM/NaN/reference漂移/缺pair/无法恢复/擅改beta/optimizer；低质量结果不是重采样理由。

**Deliverables**：smoke/pilot/full报告、best/final checkpoint身份、训练曲线和血缘。

**GPU Requirements**：默认课程两GPU policy/reference布局，具体卡型须实测预算；不能仅看两卡总VRAM。

**Expected Cost and Time**：smoke/pilot建议预留1–3 GPU墙钟小时（2卡时GPU-hours×2）；Full NOT MEASURED，ceil(Ntrain/64)×tstep+验证/保存/加载。原课程1 B200 hr不可照搬。

**Next Gate Approval**：P8a→P8b→P8c均明确批准；完成后批准P9推理与Judge各自预算。

## P9 — Full Judge & Post-DPO Evaluation

**Objective**：完成可审计的Base/SFT/DPO四任务比较。

**Inputs**：DPO accepted checkpoint、三模型raw、已批准Judge预算、人工review可用。

**Execution Tasks**：先Post-DPO四任务generation/自动评分；Judge CPU mock→smoke→可靠性pilot→人工裁决→另批Full judging→LC验收/同版复算→paired分析。Judge可靠性子Gate也可经单独批准前移，不能省略。

**Metrics**：四任务主分数、invalid/order/length/repeat/human agreement、strict安全、LC、能力退化、false refusal/效率。

**Acceptance Criteria**：三模型完整raw、Judge可靠性阻断项解决、分母和版本一致；无法计算LC明确PENDING原因；不能将有缺项表称全部完成。

**Failure / Stop Conditions**：Judge invalid/重大漏判未解决、数据/版本不一致、缺人工裁决、硬件失败。

**Deliverables**：三模型scorecard、comparison、Judge audit/raw、行为报告、review和存储registry。

**GPU Requirements**：7B generation与72B大显存TP顺序占用，不并行挤占同资源；BF16 Judge显存需独立验收。

**Expected Cost and Time**：DPO generation暂估2–5 GPU小时；72B时间NOT MEASURED，按2715或5130calls及实测两任务吞吐报价；人工40案例约80–200分钟+争议；全量审查另预算。

**Next Gate Approval**：批准P10仅复盘/候选规划；新一轮数据构建/训练另审批。

## P10 — Data Flywheel Review

**Objective**：把有证据的错误机制转为下一轮优先级，不污染评估。

**Inputs**：P9比较、paired transitions、错误taxonomy、人审裁决与成本。

**Execution Tasks**：每case路由和理由→区分独立SFT/DPO候选/回归/evaluator fix/no action→来源授权/隐私/去重/隔离设计→下一轮单变量实验提案。

**Metrics**：修复/回归、candidate覆盖、风险/标注成本、污染拒收、未决数、证据强度。

**Acceptance Criteria**：所有case有route或明确pending；holdout不回流；下一轮有独立数据/验收与预算；AI结论不冒充人审。

**Failure / Stop Conditions**：原benchmark题回流、来源/隐私不明、擅改评分、夸大因果收益。

**Deliverables**：product-behavior-analysis、next-iteration-recommendations、candidate registry提案。

**GPU Requirements**：无GPU，仅CPU分析与人审；下一周期GPU另申请。

**Expected Cost and Time**：估算2–4小时整理已审证据；额外审阅按case数计；GPU费用0，不包括未来再训练。

**Next Gate Approval**：停止，用户批准下一轮具体数据准入及实验Gate后才执行。

## 时间估算依据和租用建议

已测PILOT吞吐（仅任务batch生成，不含加载/写盘）MMLU5.4087、GSM8K1.0726、Alpaca.6341、SST1.1644 examples/s。按现有全量库存外推：14042/5.4087 + 1319/1.0726 + 805/.6341 + 100/1.1644 ≈ 5180秒≈1.44小时。这不是Full实测；20例长度分布不代表全量，故P1排程先留2–4小时。

CPU设计/实现/人审期间不用长期占GPU。P4和P8先短租实测，满足首步内存并得到稳态step时间再批准Full续租；Judge等三模型raw具备时可集中加载评分，减少72B加载开销，但需要早期质量决策时先小规模前置Judge。租期至少覆盖获批Gate估算上界、checkpoint写入和归档缓冲，不能等待快到期才保存唯一权重。

Full SFT/DPO总时长、Judge价钱及端到端完成日期当前PENDING。P4/P8/72B pilot完成后才给可靠milestone日期；人审与审批等待独立列出，不计作GPU运行时间。
