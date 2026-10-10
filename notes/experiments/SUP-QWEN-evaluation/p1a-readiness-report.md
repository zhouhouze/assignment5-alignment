# P1A Readiness — Full Baseline Runner Engineering Gate

日期：2026-10-10。**CPU 工程验收通过；真实 Full generation NOT RUN。** 本次用户只批准 P1A，完成工程与归档后停止。

## Repository / 实际证据

- Worktree：`/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement`，持久 Supplement worktree，未删除。
- Branch：`learning/pa5-supplement`；起点 local/remote HEAD 同为 `09c18e7d4e966264f994f8ce2fc5deb1b385a937`，干净。
- Implementation commit：本报告所属独立提交，subject=`Implement reliable Qwen full baseline runner`，准确 SHA 由 `git log -1 --format=%H -- cs336_alignment/qwen_baseline_storage.py` 和最终回报定位。
- 测试来源：P0 HEAD + dirty 开发修改，`full-cpu-report.json` 保存 runner/storage/audit/driver 的准确源码 SHA；测试源码与本提交内容对应。归档提交号不能冒充 CPU 测试运行时 HEAD。
- 旧 Main 分支/产物、P0 协议、Prompt/parser、SFT 数据与正式 scorecard 未改；239 历史 checksum 通过。

## 工程 Gate

| 验收 | 结果 | 证据 |
| --- | --- | --- |
| Full CLI 与旧 Smoke/Pilot 兼容 | PASS | [实现](p1a-runner-implementation.md)；旧 43 + 新 37 = 80 tests |
| 四任务全量输入与稳定 ID | PASS | 14042 + 1319 + 805 + 100 = 16266；60 文件 SHA；P0 ID/render inventory 一致 |
| 增量 raw / resume / crash / duplicate / corrupt / config drift | PASS | [故障矩阵](p1a-reliability-tests.md) |
| 原子 finalization 与正式状态 | PASS | metrics/checksum/manifest/fsync 故障不能发布 completed |
| 离线独立复算 | PASS | 从磁盘读取；不共享 runner score/aggregation；MMLU/GSM 分母与长度/finish/timing 对齐 |
| Judge 任务 | Candidate schema PASS | Alpaca805、Safety100 的 Mock 导出验证；Win/safe rate **NOT RUN** |
| 全量 Mock 与正式隔离 | PASS | CPU 临时目录；无 Mock scorecard；vLLM 未导入 |
| P1B 运行命令 | 已准备 | [执行 runbook](p1b-execution-commands.md)，本轮没有执行真实分支 |
| GitHub 归档 | 本报告随指定独立 commit 推送 | 最终以远端 SHA 核对；无 force push/merge |

`P1A_ENGINEERING_READY=YES`：工程测试和完整输入已验收，Git 归档由该 Gate 独立提交及远端 SHA 核验闭合。

`P1B_EXECUTION_READY=NO`，`P1B_RESOURCE_CHECK_PENDING`。本轮未连接/核验新的 GPU 会话，没有“GPU 空闲/权重完整/云盘持久/预算已批”的现场结论。

## 当前 P1B 资源状态

| 项目 | 状态 / 约束 |
| --- | --- |
| GPU | 计划 1×RTX5090 32GB；现场型号、VRAM、进程、driver 尚未核验 |
| 7B 权重 | 固定 revision d149729…；历史约15.23GB、峰值显存24761MiB仅为参考；执行前按冻结 acceptance 文件逐文件 SHA/bytes 核验 |
| 软件 | 历史 Python3.12.13/Torch2.10.0+cu129/vLLM0.19.1/Transformers5.7.0/FA2.8.3；现场要记录并核验差异 |
| 磁盘 | 模型/环境之外建议至少 **5 GiB 空闲、100,000 可用 inodes** 作本次结果/日志工作余量；这是规划余量，不是严格空间上限。另有独立持久备份容量 |
| 持久目录 | 必须实际确认实例释放后仍保留，且支持 fsync/link/rename/flock；本机 POSIX 成功不代表云盘已验收 |
| 时间与费用 | Pilot 外推纯生成约86.4分钟；建议调度预留2–3小时，并保留到4小时的人工决策空间；不能保证完成时刻。实际单价和金额上限未提供，不能计算确定费用 |
| 执行授权 | P1B 未批准。CPU 工程 READY 不能自动启动 16266 条真实推理 |

## Pilot 外推

| Task | Pilot平均输出tokens | 实测examples/s | Full纯生成外推 |
| --- | ---: | ---: | ---: |
| MMLU | 19.15 | 5.4087 | 43.27 min |
| GSM8K | 181.20 | 1.0726 | 20.50 min |
| AlpacaEval | 289.05 | 0.6341 | 21.16 min |
| Safety | 133.50 | 1.1644 | 1.43 min |
| Total | — | — | 86.36 min / 1.44 h |

计算 `N_task / pilot_examples_per_second`，原始依据为 20261003-pilot-03/metrics-v1.json；机器可复算文件见 `runtime-estimate.json`。每任务只有20题，MMLU subjects/输出尾部分布未完全覆盖；Alpaca4/20达到512，长尾、首调用、模型加载/权重验收、云盘写入、重启都会改变总时长。CPU Mock 约46秒只说明本机工程链路开销。

租费若为 p 元/小时，预估生成工作窗口费用为 `(2–3)×p`；4小时预留为 `4×p`，不是已经批准的金额。模型下载、CPU准备或手动空闲计费需另计。确定预算后把批准的累计秒数传给 `--max-seconds`；不能把它视为云实例自动关机功能。

## Full Run 实际布局

```text
<持久存储>/<run_id>/
  manifest.json + manifest.sha256      # 固定配置，不改写
  selected_examples.json / input-check.json
  progress.json                       # 仅 raw capture 状态
  raw/<task>-<request_index:05>.jsonl  # 单条原子提交，含 record_sha256
  attempts/<attempt_id>/start.json, *.intent.json, *.saved.json, end.json
  recoveries/                         # 仅实际发生恢复时
  logs/                               # P1B 操作者保存 stdout/stderr
  finalized/v1/
    manifest-final.json / metrics.json / SHA256SUMS
    scored/<task>.scored.jsonl
    exports/alpaca_eval.json / simple_safety_tests.jsonl
    checks/{integrity-report,recomputation-report,source-inventory}.json
```

未完成写入 `.pending-*`、失败 `.finalizing-*` 保留为事故证据；它们不是有效 raw/正式结果。最终 SHA 覆盖 bundle，source-inventory 链接 raw/manifest/selected/attempt/log 等文件；校验和不含自身。整目录迁移后执行 validate。支持任务子集，但 manifest scope=TASK_SUBSET，不能当作四任务完成。

实际 Git 工程产物为四份 P1A/P1B 文档、扩展 runner、storage/audit helpers、新测试、CPU 验证脚本、工程日志/摘要/checksum。没有新增正式 Full 实验 raw。

## Recommended next gate

请求下一轮 **P1B：Qwen2.5-7B Full Base Generation（16,266 条）** 的现场资源/持久化/预算确认与执行授权。保留人审 pending 与 Judge NOT RUN；不自动继续 SFT/DPO。Next task：按 [P1B runbook](p1b-execution-commands.md)先验收目标存储和环境。
