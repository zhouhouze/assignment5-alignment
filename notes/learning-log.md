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

## 2026-10-11 — P1B-0.5 Incremental Backup / Restore Gate

- Component：Raw优先稳定快照、SHA对象增量传输、Mac原子发布、远端ack与自有进程组过期保护；不改模型/数学实现。
- Concept learned：备份成功需要持久化且可恢复；周期副本有RPO；pending事故证据与有效Raw完成数分离；恢复prefix不等于Full完成。
- Files changed：3个scripts、1个stdlib测试文件、验收报告/启动命令/检查单、索引/registry/manifest/checksums。
- Tests run：Mac/Linux各24 tests PASS；真实周期/网络失败恢复/guard CPU退出PASS；既有16266条CPU Mock回传后Runner validate PASS；按项目要求GRPO suite原有19项NotImplemented失败，未修复/隐藏。
- Bugs encountered：失效SSH master需重新认证；补充quiescent保留pending后旧验收把“Raw增量”和“传输对象增量”混同，已保留FAILED证据并分两步复验。
- Final decision：仅稳定且已封存Raw计完成；SHA内容对象不可覆盖；本地验证后才回传ack；quiescent锁内保存最终包与未提交事故字节；失败不删除旧副本。
- Remaining questions：账户保留磁盘设置/期限/费用、当前实际费率和开机窗口、批准金额/时长、独立P1B-1授权；GPU worker退出仍需真实运行现场观察。
- Learner explanation status：pending，不代签理解；为什么文件传完不等于备份完成？为什么pending要留但不能计分？
- Next task：停止于P1B-0.5；获批后按runbook绑定正式run，Full仍0/16266。

## 2026-10-11 — P1B-1 Real Full Base Baseline

- Component：固定已有Runner在1×5090顺序执行四个独立REAL/FULL run；16,266条输出、冻结自动评分/独立复算、周期备份和独立恢复。没有实现新训练或推理核心。
- Concept learned：parse success不等于语义答案对齐；冻结正式分数与AI初析/参考争议分开；完整raw/可恢复性与Judge/人工确认是独立完成状态。
- Files changed：Full报告、行为画像、runtime/cost、四任务小型manifest/metrics/checks/SHA、44条review、UNKNOWN友好的routing、registry/计分板/索引与进度。外部helper源码随证据归档，不伪称其在47ae79f clean inference tree中。
- Checks run：四任务原Runner完整性/独立复算PASS；Mac四次quiescent/deferred=[]恢复SHA PASS；24,472个portable tar成员SHA PASS；10冻结文件、60数据、8tokenizer、239历史checksum PASS；Pilot27条包原字节不变。没有核心编辑，无新增核心unit-test要求；既有P1A80/P1B0.5各平台24项仅引用原证据。
- Bugs encountered：外部分析用Unicode splitlines误切JSON字符串内分隔符，改物理LF迭代后全部14,042条可读；未修改raw、Parser或重采样。GPU infra failure=0。
- Archival checks：通用*.log ignore导致8份日志初次未入index，最终无损gzip且确认全部checksum路径已入Git；外部校验helper初次对stage后artifact编辑范围假设过窄，限定notes/本轮archive并联合检查staged+unstaged后重验。原始run未改。
- Final decision：MMLU9813/14042=69.8832%、GSM929/1319=70.4321%保留；GSM5条抽样的语义/最后数字不一致及virology参考争议另待人审；Alpaca/Safety只候选，不报告Judge分数。4,619条wrong全部路由，12条AI初归因、4,607条UNKNOWN；原holdout训练准入0。
- Remaining questions：44条human PENDING、Judge NOT RUN/LC NOT VALIDATED、未来Evaluator提案、人审SFT准入和来源/安全/去重；到期后磁盘费用/期限及释放恢复UNKNOWN。
- Learner explanation status：PENDING，不代签理解。后续解释为何parse0失败仍不能保证正确评分，及为何length和语义截断不同。
- Next task：仅建议P2 SFT Dataset Acceptance/P3 SFT CPU Pipeline Implementation；Git同步完成后停止，未执行下一Gate。

## 2026-10-16 — Human Evaluation Round01 archival

- Component：12条用户确认人审裁决append-only sidecar、schema v1.1非破坏性扩展、审核汇总/PM复盘、索引/registry/checksum。只归档，无数学/训练核心修改。
- Concept learned：人审步骤COMPLETED≠不确定真值已裁决；Instruction Following与Correctness、length与语义截断、Safety与拒答/支持质量分开。正式标签/候选/辅助观察/AI注释/用户原裁决分离；父子Safety标签按一个事件。
- Files changed：baseline/human-review/20261016-round01、human-evaluation-round01-report、pm-human-evaluation-review-round01及必要索引/计分板人审行/进度。原raw/scored/manifest/metrics/44条包/Pilot/协议不变。
- Tests run：16项CPU契约测试PASS；12/12复合身份及Raw SHA匹配；24472旧文件/16266 Raw、旧Full/Pilot/冻结文件SHA验证PASS；幂等no-op/冲突/重复/不确定状态/辅助标签/时间/原裁决防改写检查通过。无模型导入或GPU调用。
- Bugs encountered：用户首附件在sst_075处截断，停止缺失结论写入并请求补充；收到3条完整补充和用户提供别名后继续。历史12条reviewed_at不可核实，nullable UNKNOWN，独立记录真实recorded_at；没有伪造。
- Final decision：人审12/12完成，source packet覆盖12/44；Safety SAFE3/UNSAFE1/UNCERTAIN1；075专项真值待裁决，060已UNSAFE但S3候选严重度细化pending，729正确性uncertain。候选Ambiguity/Over-verbosity不确认为正式错误；holdout训练准入0。
- Remaining：075专项裁决、060严重度细化、729正确性不确定；32条Full人审尚未完成；Judge/SFT/DPO未运行，历史审核时间仍UNKNOWN。
- Learner explanation status：未单独取得概念解释确认，不代签理解；用户人审完成事实由本轮明确裁决记录，不与学习确认混同。
- Next task：完成Git归档后停止；仅建议用户安排专项复核/后续P2，不自动执行。

## 2026-10-16 — PM-04 SFT Hypothesis & Evaluation Plan v1

- Component：训练前设计文档归档；证据→H1–H5→评估/控制→配对人审/统计→PM决策→P2审计需求。不改模型/训练源码。
- Concept learned：可检验假设须有相反证据与不确定判据；统计方向支持≠训练归因≠产品接受；CI跨零不证明能力保持；A/D配置差异不能单归SFT。
- Files changed：sft-hypothesis-evaluation-plan-v1、PM04设计来源/manifest/CPU检查/checksum、必要索引/registry与进度图谱。12份证据来源及冻结协议不改。
- Checks：12必核来源+6支持证据SHA，Base9813/14042、929/1319、805/100候选、97/805 length与人审12/SAFE3/UNSAFE1/UNCERTAIN1核对；5假设×15字段、10章节、8决策场景、2×2差值/交互、链接/边界/敏感模式/变更范围检查。无GPU tests或模型导入。
- Bugs encountered：无训练/评估代码修复；起草时将Refusal Quality FAIR计数与Supportive Quality混同，按sidecar改为拒答质量2条、支持质量1条，校验加入该事实约束。
- Final decision：H1/H2/H3改善与H4保持均待后测，H5固定Prompt归因；新诊断/人审/产品阈值待批，SFT空白策略FROZEN但实际P2未执行，holdout训练准入PROHIBITED。
- Remaining：PM04_PM_REVIEW=PENDING；075真值、060严重度细化、729正确性；诊断规模/来源、人审预算/二审、Judge/LC可靠性、能力/安全取舍、P2及后续训练Gate。
- Learner explanation status：PENDING，未代用户宣称认可假设/产品结论。可后续解释为何D−A与CI跨零不能分别证明训练效应和能力保持。
- Next task：完成设计归档与远端核对后停止，等待用户亲自PM-04评审；不自动P2/SFT/DPO/Judge。

## 2026-10-28 — P2-A.1 Raw Validator

- Component / concept: read-only identity/schema validation; per-field reasons vs unique physical rows.
- Files changed: new validator/test, P2-A.1 evidence/report/index/registry and progress notes.
- Tests: 23 new PASS, 10 preflight PASS; 19 pre-existing GRPO NotImplemented FAIL (unchanged).
- Bugs encountered: no new test or Raw verification failures; legacy GRPO failures retained.
- Decision: real Raw verification PASS; 22/2/0 anomalies, all strict empty. No Derived or training.
- Remaining: P2-A.2 and complete admission pending.
- Learner explanation status: PENDING, not claimed on learner behalf.
- Next task: stop after archive; await next explicit Gate.

## 2026-10-28 — P2-A.2 Derived Dataset

- Component/concept: immutable byte-preserving derivation, complete lineage, independent disk verification; machine acceptance is not content admission.
- Files changed: derive/verify scripts, dedicated tests, P2-A.2 evidence/report/registry and progress notes.
- Tests: 15 new PASS; 33 Raw/preflight PASS; 19 pre-existing GRPO NotImplemented FAIL, unchanged.
- Bugs encountered: no new test/real-run failures.
- Decision: train210326 / validation23108 / sample1000; exclusions24 match A.1, all retained bytes and mappings verified; exact train/validation overlap0; restored bundle verified.
- Remaining questions: semantic contamination, human quality/risk review, complete admission and off-device durability.
- Learner explanation status: PENDING.
- Next task: stop after archive; suggest separately authorized P2-B.

## 2026-10-28 — P2-B.1 contamination audit

- Component/concept: exact vs normalized/ngram candidates; deterministic anchor recall limitations; short answers/templates are not causal contamination evidence.
- Files: independent audit tool/tests, P2-B.1 evidence/report/registry/progress.
- Tests: 20 new PASS, 48 related PASS, 19 unchanged GRPO NotImplemented FAIL.
- Actual run: 210326 train, 23108 validation, 16266 benchmark; 3732 field hits; 94.197s, peak1.659GiB; input identities unchanged.
- Bugs: auxiliary candidate reader selected parent directory; stopped, retained original source/failure, fixed root only; all3732 emitted candidates rechecked. Primary run no failures.
- Decision: execution PASS, admission PENDING; no automatic cleaning or adjudication.
- Remaining: long-material/question-cluster risk, short benchmark overlap provenance, semantic recall and human decisions.
- Learner explanation: PENDING. Next task: stop; request separately scoped review Gate only after user acceptance.

## 2026-10-31 — P2-C Derived-v2
- Component: scoped versioned exclusion of one exact AlpacaEval 370 Q/A from SFT Train; learner explanation status PENDING.
- Concept: source-row identity and complete mapping let one removal be independently audited without changing other bytes or claiming full Data Admission.
- Files changed: scripts/derive_qwen_sft_v2.py, scripts/verify_qwen_sft_v2.py, tests/test_qwen_sft_v2.py, P2-C report/manifest/checksums/registry/index.
- Tests: 4 narrow PASS; 58 related PASS; 19 unchanged GRPO NotImplementedError FAIL. Independent full-file verifier and restored archive PASS.
- Bugs encountered: a precheck helper initially passed a byte string to a path-hash function; corrected the helper and reran identity checks before any v2 output. No source data anomaly.
- Decision: only Raw train line181453 / v1 line181433 excluded; retain all other candidates and human admission as PENDING.
- Remaining questions: disposition of other candidate risks and learner's explanation of mapping/version semantics.
