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
