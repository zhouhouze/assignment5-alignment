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
