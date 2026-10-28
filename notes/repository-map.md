# Supplement仓库地图

- `notes/experiments/README.md`：Main/Supplement统一实验索引，Main使用原提交链接。
- `notes/experiments/archive-policy.md`、`manifest.template.json`、`artifact-registry.json`：长期归档规则、run模板和产物位置/大小/SHA。
- `cs336_alignment/supplement_metrics.py`：MMLU/GSM8K parser；`tests/test_supplement_metrics_edges.py`补充边界验证。
- `scripts/setup_supplement_environment.sh`、`audit_supplement_environment.py`：仅环境重建/审计，不启动实验。

- `notes/experiments/SUP-00-environment/`：Gate A审计、分阶段路线。
- `notes/experiments/SUP-01-baseline/`：独立baseline计划；后续结果/误差分析。
- `artifacts/pa5-supplement/audit/20261002/`：本次CPU测试、环境与数据指纹。
- `cs336_alignment/prompts_safety/`：官方Supplement模板。
- `tests/test_metrics.py`、`test_data.py`、`test_dpo.py`：parser已实现；SFT数据、DPO adapter尚未实现。
- `scripts/evaluate_safety.py`、`scripts/alpaca_eval_vllm_llama3_3_70b_fn/`：官方judge辅助程序，当前不启动。
- `cs336_alignment/modal_utils_safety.py`：课程共享卷路径参考；当前智星云未挂载。

本分支没有继承个人O1/O2代码、结果或笔记。Main官方脚手架随官方仓库存在，但不属于Supplement实验产物。

## 2026-10-02 Qwen adapted preflight

新增configs/pa5_supplement_qwen.json、scripts/qwen_preflight.py、restore_qwen_preflight_assets.py、Qwen annotator目录、tests/test_qwen_preflight.py；记录SUP-QWEN-*与artifacts/pa5-supplement-qwen。大数据在ignored data/qwen-sft-mirror，tokenizer在ignored models/qwen-preflight，按inventory可重取。

## 2026-10-02 Qwen Baseline CPU Gate

新增qwen_baseline runner、独立Gate配置与7B限定下载脚本；四任务CPU准备通过，42项测试通过。raw逐请求独立封存，scored按版本派生；合法空答保留，pending/infra失败阻断自动恢复。无训练核心变更，学习解释pending。下一步按已授权范围进行SMOKE→PILOT。

## SUP-QWEN-01 GPU证据（2026-10-03）

notes/experiments/SUP-QWEN-01-baseline/{weight-acceptance,smoke-report,pilot-report}.md为报告；artifacts/pa5-supplement-qwen/baseline/{smoke/20261003-smoke-03,pilot/20261003-pilot-03}为真实run。gate-audit/20261003保存辅助验收/离线复算/AI标注脚本和日志，非新训练实现；weight-acceptance.json登记可重新下载权重。manifest-final追加生命周期，不改原始manifest/raw。

## 2026-10-10 Evaluation / Data Flywheel 规划入口

[SUP-QWEN-evaluation](experiments/SUP-QWEN-evaluation/README.md)保存指标、协议、Prompt/逐题对照、错误分类、Judge验证、状态核验和Gate；[SUP-QWEN-data-flywheel](experiments/SUP-QWEN-data-flywheel/data-flywheel-design.md)保存SFT/HH质量审计、准入与路由。SFT/DPO目录新增training设计，SUP-QWEN-final新增计分板/比较/产品行为/下一轮模板。全部规划状态，未产生新实验raw、数据清洗或checkpoint。

## P0唯一协议入口

[SUP-QWEN-EVAL-v1](experiments/SUP-QWEN-evaluation/evaluation-protocol-v1.md) → [decision log](experiments/SUP-QWEN-evaluation/evaluation-decision-log.md) → [P1 readiness](experiments/SUP-QWEN-evaluation/p1-full-baseline-readiness.md)。旧evaluation-protocol.md改为导航；现有规划就地更新，不另复制22份。SFT数据处理策略v1位于原sft-data-quality-plan.md，实际过滤NOT RUN。

## 2026-10-10 P1A Full runner

原`cs336_alignment/qwen_baseline.py`扩展FULL；`qwen_baseline_storage.py`为原子IO/锁/记录校验，`qwen_baseline_audit.py`为独立磁盘复算（均无第二套推理runner）。`tests/test_qwen_full.py`提供37项CPU可靠性测试；`scripts/verify_qwen_full_cpu.py`验证全部16266输入与Mock IO。`notes/experiments/SUP-QWEN-evaluation/p1a-*.md`及`p1b-execution-commands.md`为实现/验收/后续命令；`artifacts/pa5-supplement-qwen/baseline/gate-audit/20261010-p1a/`仅保存工程摘要/日志，不含正式Full raw。Next task：P1B资源与批准。

## P1B-0预检记录

`notes/experiments/SUP-QWEN-evaluation/p1b-resource-preflight.md`记录云端资源核验、CPU/备份恢复及持久化/预算待决项；`artifacts/pa5-supplement-qwen/baseline/gate-audit/20261010-p1b0/`保存预检事实、权重SHA、云端CPU日志、恢复验证/SHA，无正式模型run。

## 2026-10-11 P1B-0.5 backup / restore

`scripts/qwen_artifact_backup.py`只做SSH导出、Mac增量对象/快照、校验/恢复/ack；`scripts/qwen_backup_guard.py`只保护显式命令的自有进程组；`scripts/verify_qwen_backup.py`用CPU fixture与既有Mock验证真实SSH，不调用模型。`tests/test_qwen_backup.py`为24项stdlib故障测试。备份报告与资源清单在`notes/experiments/SUP-QWEN-evaluation/p1b-*`；小型证据在`gate-audit/20261011-p1b05`，外部对象位置由registry/snapshot manifest索引。

## 2026-10-11 P1B-1 Real FULL

`notes/experiments/SUP-QWEN-evaluation/p1b-full-baseline-report.md`为实际Full结果入口；`qwen-base-behavior-profile.md`为AI初析，`p1b-runtime-cost-report.md`为计费/时间/保留边界。`artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/`含四任务原始manifest/指标/检查、小型gzip完整性索引、44条review及原样SHA、外部执行/分析helper源码。raw/scored/selected inputs/完整attempt与VRAM记录在registry登记的Mac CAS、独立restore和27.3MB tar。现有Runner/backup/guard源码未改，Main O1/O2不动。

## 2026-10-16 Human Evaluation Round01

`artifacts/pa5-supplement-qwen/baseline/human-review/20261016-round01/`新增12条独立human-review.jsonl、source决策正文、非破坏性schema v1.1、manifest/summary/integrity/CPU验证及checksum。`notes/experiments/SUP-QWEN-evaluation/{human-evaluation-round01-report,pm-human-evaluation-review-round01}.md`为用户裁决汇总/PM复盘；原Full/Pilot/协议不改，44条旧human字段不回填。读取当前人审状态需按复合身份关联sidecar，不能用旧snapshot字段覆盖新裁决。Next task：Git归档后停止。

## 2026-10-16 PM-04 SFT hypothesis plan

`notes/experiments/SUP-QWEN-evaluation/sft-hypothesis-evaluation-plan-v1.md`为唯一主稿（10章节、H1–H5、评估/控制、人审/统计、8情形PM决策、P2审计交接）。`artifacts/pa5-supplement-qwen/evaluation-design/20261016-pm04/`是设计来源SHA、状态manifest、CPU文档校验和归档验收，不是模型run或P2派生训练数据。现有protocol/metrics/Prompt/Parser/人审sidecar/训练源码不改。Next task：归档后停止等PM评审。

## 2026-10-28 P2-A.1

`scripts/validate_qwen_sft_raw.py`: standalone stdlib CPU Raw verifier; `tests/test_qwen_sft_raw.py`: synthetic contracts. `artifacts/pa5-supplement-qwen/sft/20261028-p2a1-{raw,tests}`: actual evidence, not filtered datasets. `notes/experiments/SUP-QWEN-02-sft/p2-a1-raw-verification-report.md`: execution/limits. Next task: stop pending next Gate.

## 2026-10-28 P2-A.2

`scripts/derive_qwen_sft.py` generates external derived-v1; `scripts/verify_qwen_sft_derived.py` independently reads disk lineage/content/checksums. `tests/test_qwen_sft_derived.py` covers synthetic and corruption cases. Evidence: `artifacts/pa5-supplement-qwen/sft/20261028-p2a2`; report: `notes/experiments/SUP-QWEN-02-sft/p2-a2-derived-report.md`. Complete data/backup/restore live outside worktree under `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/`; registry provides SHA and restore guidance. Stop pending next Gate.

## 2026-10-28 P2-B.1

`scripts/audit_qwen_contamination.py` / `tests/test_qwen_contamination.py`: bounded read-only lexical scan. Evidence in `artifacts/pa5-supplement-qwen/sft/20261028-p2b1` and `20261028-p2b1-tests`; report `SUP-QWEN-data-flywheel/p2-b1-contamination-audit-report.md`. Complete small candidate gzip archived; original run under external persistent `pa5-experiment-backups/sft/20261028-p2b1-audit`. No data filtering.
