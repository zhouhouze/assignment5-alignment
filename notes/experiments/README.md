# CS336 PA5统一实验索引

> 2026-10-31 P2-C Derived-v2 仅排除已指定的 Train Raw 181453：Train210325、Validation23108、Sample1000；独立复算和恢复PASS。机器处理完成，Data Admission仍PENDING。[执行报告](SUP-QWEN-02-sft/p2-c-derived-v2-report.md)。

> 2026-10-29 P2 精简人审包已准备：历史 Train 随机20、固定 seed Derived-v1 Validation 随机20、定向拒答诊断3；血缘与原文核对 PASS，人工审核和 Data Admission 仍 PENDING。[准备记录](SUP-QWEN-data-flywheel/p2-compact-review-packet.md)。

> 2026-10-20 PM-04：设计已于10月16日归档，本次用户正式签收 **PM Review APPROVED (Design Only)**；PM04_DESIGN_COMPLETE=YES，P2_EXECUTION=NOT AUTHORIZED。H1–H5仍待真实SFT实验检验，产品阈值/预算/资源与后续Gate未获批准。 [PM-04主文档与签收记录](SUP-QWEN-evaluation/sft-hypothesis-evaluation-plan-v1.md)。

> 2026-10-16 Human Evaluation Round01：用户裁决已独立归档 **12/12（Alpaca7、Safety5）**；Full复核包当前12/44已审、32条待审。Safety SAFE3/UNSAFE1/UNCERTAIN1；sst_075人审完成但专项裁决待定，sst_060 S3候选严重度细化PENDING，Alpaca729正确性UNCERTAIN。Judge/SFT/DPO未运行。 [本轮报告](SUP-QWEN-evaluation/human-evaluation-round01-report.md)。下方原日期记录保留历史含义，旧44条包不回填。

> 2026-10-11 最新：P1B-1真实Full **16,266/16,266**；生成、评分、独立复算、quiescent备份/恢复PASS。MMLU69.8832%，GSM8K70.4321%；Alpaca/Safety候选齐全，Judge NOT RUN、LC NOT VALIDATED；新44条人审PENDING。Git归档7516dd3已push，GitHub/云端核对通过；P1B_STATUS=COMPLETED。 [Full报告](SUP-QWEN-evaluation/p1b-full-baseline-report.md)。下方各历史Gate的NOT RUN仅描述当时状态。

本索引是Main与Supplement的证据入口。长期规则见[archive-policy.md](archive-policy.md)。Main内容通过固定提交链接引用，未移动历史文件或混入Supplement实现。

| Experiment | Status | Report | Artifacts | Commit |
| --- | --- | --- | --- | --- |
| O1 Prompt Baselines（历史） | FULL报告完成；旧raw缺失 | [历史结果](https://github.com/zhouhouze/assignment5-alignment/blob/2267287678062eefe5a2bd5f0e5f6a3a03f37565/notes/experiments/O1-prompting-baselines/full-results.md) | 旧AutoDL完整raw不可恢复；不能逐题复现 | `2267287` |
| O1归档复现 | FULL自动归档完成；24条人工复核待填 | [复现报告](https://github.com/zhouhouze/assignment5-alignment/blob/96b14809b08927516cfd049cfc6ddb33cd3f115c/notes/experiments/O1-prompting-baselines/reproduction-report.md) | [raw/metrics/review/checksum](https://github.com/zhouhouze/assignment5-alignment/tree/96b14809b08927516cfd049cfc6ddb33cd3f115c/artifacts/O1-prompting-baselines-reproduction) | `96b1480` |
| O2 Standard GRPO | 单卡独立SMOKE完成；双卡闭环/PILOT/FULL未完成 | [单卡报告](https://github.com/zhouhouze/assignment5-alignment/blob/9321c61d2814fa3db464690ccfe68b199057d39d/notes/experiments/O2-standard-grpo/single-gpu-smoke.md) | [smoke证据](https://github.com/zhouhouze/assignment5-alignment/tree/9321c61d2814fa3db464690ccfe68b199057d39d/artifacts/O2-standard-grpo/single-gpu) | `9321c61` |
| SUP-00 Environment | 环境/kernel验收PASS；HF访问BLOCKED | [初审](SUP-00-environment/environment.md)、[本轮前置报告](SUP-00-environment/preflight-report.md) | [初审](../../artifacts/pa5-supplement/audit/20261002/)、[本轮](../../artifacts/pa5-supplement/audit/20261002-preflight/) | 初审`36de0b7`；本轮归档提交见文件Git历史 |
| SUP-01 Baseline | parser完成；模型生成/评分未开始 | [计划](SUP-01-baseline/baseline-plan.md)、[parser报告](SUP-01-baseline/parser-report.md) | 本轮测试日志，非模型raw | parser `4b6014e` |
| SUP-02 SFT | 仅调查数据来源；未审样本/训练 | [数据源调查](SUP-02-sft/dataset-source-investigation.md) | [来源元数据](../../artifacts/pa5-supplement/audit/20261002-preflight/sft-sources.json) | 本轮归档提交见文件Git历史 |
| SUP-03 DPO | NOT STARTED | [Gate H–L计划](SUP-00-environment/execution-plan.md) | 无run，无模型结果 | — |
| SUP-final | 持续分析框架；无最终比较结果 | [数据飞轮](SUP-final/data-flywheel.md) | 待后续证据 | — |

准确的提交哈希与分支可由GitHub每个文件的History查询；不在commit内写自身SHA。代码执行来源和产物hash见各manifest。全部大小/位置/SHA登记见[artifact-registry.json](artifact-registry.json)。旧记录不因新索引而被补标为完全合规。

上述官方Llama路线停留在准备阶段；后续Qwen路线授权和状态见下节。baseline full、SFT、DPO与Judge不在本轮范围。

## Qwen Adapted Reproduction（独立路线）

`directly_comparable_to_official=false`。官方Llama3.1-8B + Llama3.3-70B记录保留；新路线Qwen2.5-7B Base + Qwen2.5-72B-Instruct Judge，SFT使用第三方固定mirror。

| Phase | Status | Evidence |
| --- | --- | --- |
| SUP-QWEN-00 | Config/tokenizer CPU验收完成；实际GPU结果见SUP-QWEN-01 | [兼容审计](SUP-QWEN-00-config/compatibility-audit.md)、[报告](SUP-QWEN-00-config/preflight-report.md)、[Judge方案](SUP-QWEN-00-config/judge-compatibility.md) |
| SUP-QWEN-01 | Base FULL 16,266/16,266；自动评分/复算/恢复PASS；Judge NOT RUN；Full人审12/44，32待审，075专项待定；Smoke/Pilot历史保留 | [权重验收](SUP-QWEN-01-baseline/weight-acceptance.md)、[smoke](SUP-QWEN-01-baseline/smoke-report.md)、[pilot](SUP-QWEN-01-baseline/pilot-report.md) |
| SUP-QWEN-02 | 三文件验收已做；train/test共24条空字段；人审pending | [验收](SUP-QWEN-02-sft/data-acceptance.md)、[逐条审读](SUP-QWEN-02-sft/data-audit.md)、[训练计划](SUP-QWEN-02-sft/training-plan.md) |
| SUP-QWEN-03 | NOT STARTED | [DPO计划](SUP-QWEN-03-dpo/dpo-plan.md) |
| SUP-QWEN-final | Base FULL已验收；SFT/DPO/Judge及模型间最终比较未执行 | [对照框架](SUP-QWEN-final/comparison-framework.md) |

Qwen证据：[preflight manifest/checksum/原文复核包](../../artifacts/pa5-supplement-qwen/preflight/20261002/)。历史2026-10-03 Baseline Gate完成CPU→4条SMOKE→80条PILOT→复算/review/archive，27条human review仍pending。2026-10-11独立P1B-1 Full结果见最新记录；历史20例PILOT分数不替换为Full。SFT/DPO/Judge仍需后续独立Gate。

本轮GPU Gate的本地/GitHub/云端归档同步已恢复，2026-10-10云端239项checksum和84条原始输出一致性验收通过；见[归档同步记录](SUP-QWEN-01-baseline/archive-sync-status.md)。

## 2026-10-10：Qwen Evaluation / Data Flywheel 规划

上轮状态（439f17b）：**PLAN ARCHIVED；当时P0 approval PENDING**。当前已进入下方P0冻结归档。本轮只做文档/模板与只读核验；未运行Full、过滤SFT、训练或72B Judge。正式结果仍为NOT RUN/PENDING。

- [总入口与当前证据](SUP-QWEN-evaluation/README.md)、[状态核验](SUP-QWEN-evaluation/current-state-verification.md)。
- [指标](SUP-QWEN-evaluation/evaluation-metrics-spec.md)、[协议](SUP-QWEN-evaluation/evaluation-protocol.md)、[Prompt对照](SUP-QWEN-evaluation/prompt-control-experiment.md)、[逐题比较](SUP-QWEN-evaluation/paired-comparison-spec.md)。
- [SFT质量/准入](SUP-QWEN-data-flywheel/sft-data-quality-plan.md)、[SFT训练设计](SUP-QWEN-02-sft/sft-training-experiment.md)、[HH审计](SUP-QWEN-data-flywheel/dpo-preference-data-audit-plan.md)、[DPO训练设计](SUP-QWEN-03-dpo/dpo-training-and-evaluation-plan.md)。
- [Judge可靠性](SUP-QWEN-evaluation/judge-reliability-plan.md)、[错误分类](SUP-QWEN-evaluation/error-taxonomy.md)、[飞轮](SUP-QWEN-data-flywheel/data-flywheel-design.md)、[路由](SUP-QWEN-data-flywheel/data-routing-policy.md)。
- [P0–P10 Gate/资源](SUP-QWEN-evaluation/execution-gates.md)、[待决事项](SUP-QWEN-evaluation/open-decisions.md)、[Full计分板模板](SUP-QWEN-final/model-evaluation-scorecard.md)。

独立归档提交由上述文件Git历史定位；本计划不替换任何历史运行结果。当时建议确认P0；后续状态见下方P0/P1A记录。

## 2026-10-10：P0 Evaluation Design Freeze

**SUP-QWEN-EVAL-v1技术协议FROZEN；P0设计已批准。P1 GPU generation readiness=BLOCKED，尚未运行。**

[唯一协议](SUP-QWEN-evaluation/evaluation-protocol-v1.md) → [逐项决策](SUP-QWEN-evaluation/evaluation-decision-log.md) → [P1 readiness / blocker](SUP-QWEN-evaluation/p1-full-baseline-readiness.md)。归档commit由Git History定位；下一run记录该协议commit/SHA及自身实际执行commit。

本轮只读核验60个benchmark文件、16266条Base prompt、8项tokenizer/config、239项历史SHA；20项CPU parser测试通过。SFT空串/纯空白排除策略已批准，实际过滤NOT RUN；Base原27条人审pending。Full/SFT/DPO/Judge均NOT RUN，LC NOT VALIDATED。

P0时的阻塞为Full CLI/恢复/规模IO及现场资源/执行授权；其中工程项现已由下方P1A解决。产品阈值未决不阻塞P1观察性学习，P1B仍需现场资源/预算/执行授权。

## 2026-10-10：P1A Full Baseline Runner Engineering Gate

**P1A_ENGINEERING_READY=YES；P1B_EXECUTION_READY=NO / P1B_RESOURCE_CHECK_PENDING。** Full CLI、原子增量raw、显式resume、配置漂移/损坏/duplicate保护、独立离线复算与原子finalization完成。80项相关CPU tests通过；SFT/DPO/GRPO原有22项NotImplemented单独分类。全部16266条CPU输入覆盖与独立Mock链路通过；无真实GPU generation、训练或Judge，正式Full scorecard未填。

- [P1A readiness与资源估算](SUP-QWEN-evaluation/p1a-readiness-report.md)、[实现与恢复语义](SUP-QWEN-evaluation/p1a-runner-implementation.md)、[故障测试](SUP-QWEN-evaluation/p1a-reliability-tests.md)、[P1B实际命令](SUP-QWEN-evaluation/p1b-execution-commands.md)。
- [工程证据/manifest/checksum](../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261010-p1a/)。本轮恢复决定采用用户明确允许的“未持久化可重算”，协议、Prompt/parser和239项历史产物保持原样。
- 归档提交subject=`Implement reliable Qwen full baseline runner`；准确implementation/archive SHA由该文件Git History及最终远端核对定位。CPU测试实际HEAD为09c18e7+dirty源码，完整源码hash已保存。

下一Gate仅建议P1B 16266条Qwen2.5-7B Full Base，尚未批准；人审仍pending，Judge NOT RUN。

## 2026-10-10：P1B-0 Resource & Budget Preflight

**现场源码/GPU/权重/容量核验通过；P1B_EXECUTION_READY=NO。** SSH已恢复，云端从干净185364d安全同步724a340；4个权重分片及3个配置/index文件SHA通过，60个benchmark、8个tokenizer/config及239项历史证据校验通过。RTX5090空闲，系统盘约130GiB/1273万inodes可用。云端80项CPU测试通过；16266/16266 CPU Mock保存/复算/导出通过，证据见预检目录，不能计入模型成绩。历史Smoke本地备份及28文件恢复SHA通过。

[现场预检与下一步](SUP-QWEN-evaluation/p1b-resource-preflight.md)、[机器可读证据](../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261010-p1b0/)。无独立云盘，用户说明关机后保留实例，释放后恢复规则未确认；时价3.16元/小时，费用/时间上限和P1B-1授权待定。用户预计10月11日00:13关机，23:18时仅余约55分钟，不足Full外推86分钟；建议下一开机窗口预留2–3小时。真实Full仍0/16266，未加载/下载模型。用户要求预检后停止，不能将技术检查通过视为正式生成获批。

## 2026-10-11：P1B-0.5 Full 增量备份与恢复验收

**P1B_0_5_BACKUP_ACCEPTANCE=PASS；P1B_EXECUTION_READY=NO；真实Full 0/16266。** 新增stdlib备份/guard/验收脚本，不改协议或Runner；Mac/Linux各24项测试通过。实际SSH周期写入备份、失败日志/保留旧快照/文件级恢复、自有CPU进程过期停止通过；既有16266条CPU Mock备份到Mac并回传独立云端目录，原Runner validate及finalized完整性PASS。没有重新生成Smoke/Pilot，没有GPU Full或训练/Judge。原有GRPO19项NotImplemented失败保持分类。

- [备份验收/保留机制边界](SUP-QWEN-evaluation/p1b-incremental-backup-acceptance.md)、[实际启动命令第6节](SUP-QWEN-evaluation/p1b-execution-commands.md)、[资源/费用检查单](SUP-QWEN-evaluation/p1b-resource-cost-checklist.md)。
- [源码hash/真实SSH/测试/恢复证据](../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261011-p1b05/)。旧Mock、失败验收和事故文件不冒充正式模型结果。备份对象/压缩包在Mac既有备份根，registry登记；模型/环境不提交。
- 公共文档区分保留磁盘与释放；账户级保留设置/费用UNKNOWN，用户关机保留说明与本轮文件仍在不构成释放后恢复承诺。最近费率3.16元/小时，2–3小时约6.32–9.48元另计准备/空闲等；最长运行时间、费用上限及P1B-1批准待定。

本轮测试watcher已停止。归档commit通过Git history定位；源码执行起点14e2db9+dirty新增工具，精确hash见验收manifest。Next task：取得独立P1B-1与预算/时长批准后，才绑定正式run启动60秒周期worker及guard。

## 2026-10-11：P1B-1 Real Full Base Baseline

2026-10-11 最新：P1B-1真实Full **16,266/16,266**；生成、评分、独立复算、quiescent备份/恢复PASS。MMLU69.8832%，GSM8K70.4321%；Alpaca/Safety候选齐全，Judge NOT RUN、LC NOT VALIDATED；新44条人审PENDING。Git归档7516dd3已push，GitHub/云端核对通过；P1B_STATUS=COMPLETED。

- [Full结果与完整性](SUP-QWEN-evaluation/p1b-full-baseline-report.md)、[Base行为画像](SUP-QWEN-evaluation/qwen-base-behavior-profile.md)、[资源/费用/保留边界](SUP-QWEN-evaluation/p1b-runtime-cost-report.md)。
- [Full小型证据与44条人审包](../../artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/README.md)、[正式Base计分板](SUP-QWEN-final/model-evaluation-scorecard.md)。完整raw/scored/attempts/logs在Mac verified CAS/restore/tar，registry记录位置、SHA及恢复方法。
- run_code_commit=`47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726`；归档commit独立，以实际Git History及同步回执定位。协议/Parser/Prompt/模型版本与旧Smoke/Pilot不改。仅建议P2 SFT Dataset Acceptance→P3 SFT CPU Pipeline Implementation，未执行。

## 2026-10-16：Human Evaluation Round01

2026-10-16 Human Evaluation Round01：用户裁决已独立归档 **12/12（Alpaca7、Safety5）**；Full复核包当前12/44已审、32条待审。Safety SAFE3/UNSAFE1/UNCERTAIN1；sst_075人审完成但专项裁决待定，sst_060 S3候选严重度细化PENDING，Alpaca729正确性UNCERTAIN。Judge/SFT/DPO未运行。

[审核汇总](SUP-QWEN-evaluation/human-evaluation-round01-report.md)、[PM复盘](SUP-QWEN-evaluation/pm-human-evaluation-review-round01.md)、[append-only sidecar / schema / 校验](../../artifacts/pa5-supplement-qwen/baseline/human-review/20261016-round01/README.md)。原44条包SHA、Raw/Scored/Metrics/Manifest、旧Pilot与冻结协议不变；历史reviewed_at全部未知/null，recorded_at为本轮实际归档时间。仅持久化用户裁决，已授权Git归档后停止，无新实验。

## 2026-10-16：PM-04 SFT Hypothesis & Evaluation Design

[主稿](SUP-QWEN-evaluation/sft-hypothesis-evaluation-plan-v1.md)以Full Base和12条已确认人审建立证据矩阵，定义H1指令遵循、H2助手质量、H3安全与帮助性、H4能力保持、H5训练/Prompt归因，区分方向性证据与产品接受。新诊断样本、人审预算与产品阈值待批；[来源/CPU文档检查（10月16日历史快照）](../../artifacts/pa5-supplement-qwen/evaluation-design/20261016-pm04/README.md)。10月16日归档时PM04_PM_REVIEW=PENDING；10月20日已更新为APPROVED (Design Only)，P2_EXECUTION仍NOT AUTHORIZED。本次仅归档用户签收，旧档案与旧SHA保持不变；后续Gate待独立授权。

## 2026-10-28：P2-A.1 Raw Verification

**P2-A.1=PASS**：真实CPU校验三份Raw共234458行，SHA/Bytes/Schema通过；train22、validation2条严格空字段，纯空白0。23项新测试、10项旧preflight通过；GRPO19项既有NotImplemented失败原样保留。未过滤、未生成Derived；完整Data Admission=PENDING。[执行报告](SUP-QWEN-02-sft/p2-a1-raw-verification-report.md)。本轮用户授权仅P2-A.1；上方旧授权状态保留历史含义。停止等待下一Gate。

## 2026-10-28：P2-A.2 Derived v1

**P2-A.2=PASS（机器派生验收）**：train210326、validation23108、sample1000；24条排除与A.1一致，全量映射/保留字节/独立复算/恢复通过。train-validation精确prompt/pair overlap均0，sample是train子集。15项新测试、33项相关回归通过，GRPO19项既有NotImplemented失败保留。完整Data Admission=PENDING/NOT APPROVED；P2-B/P3/SFT/GPU未运行。[执行与恢复报告](SUP-QWEN-02-sft/p2-a2-derived-report.md)。

## 2026-10-28：P2-B.1 CPU Contamination Audit

**Execution PASS；Data Admission PENDING/NOT APPROVED**。真实扫描train210326、validation23108和四benchmark16266题；3732字段命中，均为未人审机器证据。Train/Validation3559去重记录对；MMLU126短选项命中；Alpaca4记录对含1常识Q/A同文；GSM/SST本方法0命中不等于无污染。20新测试/48回归PASS；GRPO19既有FAIL。独立候选回读路径错误已留痕修正，最终3732条核验PASS。[报告](SUP-QWEN-data-flywheel/p2-b1-contamination-audit-report.md)。未改数据/Policy，停止待用户验收。
