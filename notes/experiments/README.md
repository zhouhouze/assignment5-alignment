# CS336 PA5统一实验索引

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
| SUP-QWEN-01 | 权重PASS；SMOKE 4/4；PILOT 80/80；offline PASS；27条人审pending；2026-10-10云端同步/校验通过 | [权重验收](SUP-QWEN-01-baseline/weight-acceptance.md)、[smoke](SUP-QWEN-01-baseline/smoke-report.md)、[pilot](SUP-QWEN-01-baseline/pilot-report.md) |
| SUP-QWEN-02 | 三文件验收已做；train/test共24条空字段；人审pending | [验收](SUP-QWEN-02-sft/data-acceptance.md)、[逐条审读](SUP-QWEN-02-sft/data-audit.md)、[训练计划](SUP-QWEN-02-sft/training-plan.md) |
| SUP-QWEN-03 | NOT STARTED | [DPO计划](SUP-QWEN-03-dpo/dpo-plan.md) |
| SUP-QWEN-final | Base PILOT已归档；尚无FULL/SFT/DPO最终比较 | [对照框架](SUP-QWEN-final/comparison-framework.md) |

Qwen证据：[preflight manifest/checksum/原文复核包](../../artifacts/pa5-supplement-qwen/preflight/20261002/)。当前Baseline Gate已完成CPU→4条SMOKE→80条PILOT→复算/review packet/archive。27条human review仍pending；已停止，FULL/SFT/DPO/Judge需后续独立Gate。Qwen四任务结果均为PILOT，不是FULL benchmark成绩。

本轮GPU Gate的本地/GitHub/云端归档同步已恢复，2026-10-10云端239项checksum和84条原始输出一致性验收通过；见[归档同步记录](SUP-QWEN-01-baseline/archive-sync-status.md)。

## 2026-10-10：Qwen Evaluation / Data Flywheel 规划

上轮状态（439f17b）：**PLAN ARCHIVED；当时P0 approval PENDING**。当前已进入下方P0冻结归档。本轮只做文档/模板与只读核验；未运行Full、过滤SFT、训练或72B Judge。正式结果仍为NOT RUN/PENDING。

- [总入口与当前证据](SUP-QWEN-evaluation/README.md)、[状态核验](SUP-QWEN-evaluation/current-state-verification.md)。
- [指标](SUP-QWEN-evaluation/evaluation-metrics-spec.md)、[协议](SUP-QWEN-evaluation/evaluation-protocol.md)、[Prompt对照](SUP-QWEN-evaluation/prompt-control-experiment.md)、[逐题比较](SUP-QWEN-evaluation/paired-comparison-spec.md)。
- [SFT质量/准入](SUP-QWEN-data-flywheel/sft-data-quality-plan.md)、[SFT训练设计](SUP-QWEN-02-sft/sft-training-experiment.md)、[HH审计](SUP-QWEN-data-flywheel/dpo-preference-data-audit-plan.md)、[DPO训练设计](SUP-QWEN-03-dpo/dpo-training-and-evaluation-plan.md)。
- [Judge可靠性](SUP-QWEN-evaluation/judge-reliability-plan.md)、[错误分类](SUP-QWEN-evaluation/error-taxonomy.md)、[飞轮](SUP-QWEN-data-flywheel/data-flywheel-design.md)、[路由](SUP-QWEN-data-flywheel/data-routing-policy.md)。
- [P0–P10 Gate/资源](SUP-QWEN-evaluation/execution-gates.md)、[待决事项](SUP-QWEN-evaluation/open-decisions.md)、[Full计分板模板](SUP-QWEN-final/model-evaluation-scorecard.md)。

独立归档提交由上述文件Git历史定位；本计划不替换任何历史运行结果。下一步建议用户确认P0，再单独授权P1。

## 2026-10-10：P0 Evaluation Design Freeze

**SUP-QWEN-EVAL-v1技术协议FROZEN；P0设计已批准。P1 GPU generation readiness=BLOCKED，尚未运行。**

[唯一协议](SUP-QWEN-evaluation/evaluation-protocol-v1.md) → [逐项决策](SUP-QWEN-evaluation/evaluation-decision-log.md) → [P1 readiness / blocker](SUP-QWEN-evaluation/p1-full-baseline-readiness.md)。归档commit由Git History定位；下一run记录该协议commit/SHA及自身实际执行commit。

本轮只读核验60个benchmark文件、16266条Base prompt、8项tokenizer/config、239项历史SHA；20项CPU parser测试通过。SFT空串/纯空白排除策略已批准，实际过滤NOT RUN；Base原27条人审pending。Full/SFT/DPO/Judge均NOT RUN，LC NOT VALIDATED。

P1阻塞为Full CLI/selection/manifest尚未实现、恢复/规模IO未验收、现场GPU/weights/磁盘/持久化/预算与执行授权待落实。产品阈值未决不阻塞P1观察性学习。建议下一轮先批准P1 CPU readiness准备，不直接启动GPU。
