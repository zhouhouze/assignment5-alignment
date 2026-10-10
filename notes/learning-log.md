# Supplement学习日志

## 2026-10-02 — Gate A审计与baseline计划

- Component：独立实验线准备，未实现训练或parser。
- Concept：Base→SFT→DPO区分demonstration与preference；评估模板和judge解析也会影响结果。
- Files：SUP-00审计/路线、SUP-01计划、audit数据/hash/环境/测试记录。
- Tests：离线运行test_data/test_dpo/test_metrics，7 failed，全部NotImplementedError；无依赖收集失败。
- Bugs/limitations：服务器Python3.14且缺git/uv/ML依赖；HF未认证401；课程SFT预处理文件缺失；Safety helper有invalid默认safe风险。
- Decision：从官方c2734a2分支，不混入Main实现；停在审计Gate，后续先修环境和parser。
- Remaining：HF权限、课程SFT数据来源、训练硬件、judge和停止规则验证。
- Learner explanation status：Pending；本轮不宣称已理解或完成任何训练组件。

## 2026-10-02 — Supplement parsers

- Component：MMLU/GSM8K字符串提取，新增supplement_metrics与薄adapter。
- Concept：提取规则与答案正确性分离，不能读取gold帮助解析。
- Files：supplement_metrics.py、tests/adapters.py、新增边界测试、parser-report及测试产物。
- Tests：两个官方parser各2 passed；Supplement+边界20 passed/3个未实现失败；官方Main脚手架19个NotImplementedError，未带入个人Main实现。
- Bugs encountered：无parser测试失败；已知协议局限见parser-report。
- Final decision：MMLU明确声明冲突返回None；GSM8K最后十进制数字，处理符号与千分位，不求值表达式。
- Remaining：真实pilot解析覆盖率；环境/HF认证；学习检查。
- Learner explanation status：Pending。Next task：baseline runner在后续批准Gate实现。

## 2026-10-02 — 环境修复与GitHub实验档案

- Component：云端独立环境修复、HF配置访问、SFT来源调查、跨分支实验索引。
- Concept：可恢复依赖与不可替代raw分开保存；归档完成不等于模型实验完成。
- Files：AGENTS/README、archive-policy/template/index/registry、preflight报告与manifest/日志、两个环境脚本。
- Tests：云端20 passed/3个SFT/DPO未实现；179个数据hash通过；BF16/FA2 kernel通过；审计脚本语法与实际运行通过。
- Bugs encountered：初始缺git/uv/Python3.12；apt后台终端作业暂停后恢复完成，环境安装退出0；HF401与课程processed数据缺失仍未解除。
- Decision：环境按uv.lock恢复，模型不下载；Main28个产物仅固定提交引用，raw不覆盖；稳定Gate必须commit/push。
- Remaining：HF账号登录和license、processed SFT数据、下一Gate授权。
- Learner explanation status：Pending；未启动generation/training/judge。Next task：解决HF访问后讨论baseline runner。

## 2026-10-02 Qwen adapted preflight

概念：同一训练结构不等于相同模型/数据/judge标尺。Qwen EOS与Judge EOS不同；schema合法仍不等于训练数据合格。修改独立配置、CPU审计、Judge模板、sanity与归档。30项sanity/parser与持久judge配置检查通过；官方4通过3NotImplemented；GRPO19NotImplemented属于独立Supplement脚手架。问题：24空字段、样本真实性/约束遵循/安全偏差。决定：raw保留、SFT准入阻塞，不提前实现训练。Learner explanation status: pending；下一学习检查：为何PAD==EOS时不能按ID遮罩全部EOS？

## 2026-10-02 Qwen Baseline CPU Gate

新增qwen_baseline runner、独立Gate配置与7B限定下载脚本；四任务CPU准备通过，42项测试通过。raw逐请求独立封存，scored按版本派生；合法空答保留，pending/infra失败阻断自动恢复。无训练核心变更，学习解释pending。下一步按已授权范围进行SMOKE→PILOT。

## 2026-10-03 — SUP-QWEN-01 GPU Gate

权重验收、SMOKE4/4、PILOT80/80完成，43项相关CPU测试通过，离线复算PASS。运行代码固定f5f4050，无runner/parser修改；新增权重/smoke/pilot报告与逐题证据。GSM906说明分项正确但缺少总数会与final-number提取规则相互作用；Alpaca4/20触及长度上限。没有GPU infra failure；SCP reset通过既有SSH分段传输并校验解决。冻结512上限，坏输出保留，不因观察结果改prompt/parser。待理解：为什么解析成功不等于任务完成？首调用额外开销如何影响吞吐？learner explanation pending；27条human review pending。下一Gate未批准，已停止。

## 2026-10-10 — Evaluation / Data Flywheel design only

- Component：Qwen评估、Prompt因果对照、数据准入/Judge/飞轮与P0–P10规划；未实现训练组件。
- Concept learned：训练变化和Prompt变化需要对照；Judge invalid与错误输出不同；holdout错误只能指导独立数据构建。
- Files changed：SUP-QWEN-evaluation、SUP-QWEN-data-flywheel、SFT/DPO训练设计、final模板与统一索引。
- Checks：baseline239项SHA通过；4+80条raw JSON可解析；SFT三文件SHA/行数/24空字段重核；HH四文件存在/首行/SHA；阅读历史43 passed及3个NotImplemented，未重跑GPU/训练测试。
- Bugs encountered：无本轮代码修复；记录既有Safety非true默认safe风险；训练接口仍NotImplemented。
- Final decision：只提交规划/模板；数据过滤、Full、训练/Judge均NOT RUN，P0 approval PENDING。
- Remaining questions：指标阈值、Prompt stop、空白规则、人审预算、optimizer dtype、训练/Judge硬件与LC可靠性。
- Learner explanation status：pending；未代用户宣称理解。建议解释为何Base-zero→SFT-Alpaca不能单独归因训练。

## 2026-10-10 — P0 Evaluation Design Freeze

Component：SUP-QWEN-EVAL-v1协议冻结，未实现新训练/推理功能。概念：技术有效性与产品质量门槛分开；协议FROZEN不等于Full runner已ready。Files：3份核心协议/decision/readiness，更新已有metrics/Prompt/Judge/人审/数据策略/taxonomy/索引。Checks：20个parser CPU测试通过；60数据文件、16266 prompt/ID、8个tokenizer/config、239历史SHA核验通过；27条人审pending。发现：旧提案P95/empty口径与runner不一致，已纠正文档；Full CLI/selection与恢复规模IO尚未验收。Decision：仅P0归档，实际过滤/Full/训练/Judge均NOT RUN；产品阈值不虚构。Remaining：P1 CPU readiness与现场资源/预算/执行批准。Learner explanation status：pending；为何技术协议完成而P1仍BLOCKED，需用户后续解释，不代签理解。

## 2026-10-10 — P1A Full Runner Engineering Gate

- Component：可靠Full输入/增量保存/resume/独立复算/原子发布，CPU限定。
- Concept learned：结果持久化恰好一次不等于推理恰好一次；完整集合与不可变证据是比较模型的前提；RAW_COMPLETE不同于最终COMPLETED。
- Files changed：qwen_baseline、storage/audit helpers、CPU验收脚本/测试、4份P1A/P1B文档、统一索引/registry/工程证据。
- Tests run：80项相关CPU测试通过；全部16266输入及Mock保存/复算通过；原有SFT2+DPO1+GRPO19为NotImplemented，未扩展实现。
- Bugs encountered：prepare指标文档路径误写，模型调用前失败并修正；额外覆盖最后一条已提交但流程异常、发布目录fsync失败等边界。
- Final decision：raw单条sealed JSONL原子提交，显式resume保留事故/已保存字节，只处理缺失ID；schema2与历史schema1分开；固定parser/Prompt/config不动。
- Remaining questions：P1B真实GPU/权重/存储、预算/执行批准；云盘POSIX持久性须现场验收；不承诺位级复现。
- Learner explanation status：pending；请后续解释第7条保存后崩溃为何第8条可能再次推理，却不应有两条有效raw。
- Next task：本轮停止；P1B获批并验收资源后才真实生成。

## 2026-10-10 — P1B-0 Resource/Budget Preflight

- Component：本地/云端配置与资源核验、CPU IO验收、独立备份恢复，不改核心代码。
- Concept：源码一致、资源可用、持久可恢复、预算与执行批准是独立条件；fsync与云实例释放后保留也不是同一保证。
- Files changed：p1b-resource-preflight、预检JSON/SHA/CPU日志、索引/registry/进度。
- Tests run：云端80 passed in 50.73s；16266/16266 Full CPU输入/Mock保存/复算/schema通过（阶段合计312.59秒）；4个权重分片+3配置/index SHA通过；239历史SHA通过；历史Smoke本地往返28文件恢复通过。
- Bugs encountered：最初两条SSH入口在认证前关闭；用户确认信息后独立SSH参数重试成功，确切原因未确定。云端缺少rg，后续文件/进程查询用Python；未安装新依赖。
- Final decision：预检技术证据归档，P1B_EXECUTION_READY=NO；不运行真实Full，不改协议/Prompt/parser/参数。
- Remaining questions：根系统盘重启/释放后的保留规则、最终持久挂载、Full持续备份、用户已提供时价3.16元/小时；批准金额/时间与独立P1B-1授权仍待定。00:13预定关机窗口不足本次Full，建议下次预留2–3小时。
- Learner explanation status：pending，不代签理解。
- Next task：补齐持久化和预算，汇报后等待P1B-1批准；真实Full仍0/16266。
