# P1B-0 Resource & Budget Preflight

日期：2026-10-10。`experiment_type=PA5 Supplement Adapted Reproduction`；`evaluation_protocol=SUP-QWEN-EVAL-v1`；`directly_comparable_to_official=false`。

本轮仅获准P1B-0。用户任务§4.4/4.6要求确认持久化、预算和独立执行授权后才能进入P1B-1。**真实Full仍为0/16266 / NOT RUN；未加载模型、未下载权重、未创建正式Full run_id/manifest。**

## Repository / configuration

本地Supplement worktree：`/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement`；云端：`/root/cs336/pa5-supplement`；分支`learning/pa5-supplement`。本地/GitHub起点724a340，云端起点为干净的185364d。检查3个新增提交的差异后，云端安全fast-forward至`724a34014c2842807f5260abe68f6bbbe103d9a0`，未覆盖修改、未动Main分支。

现场CPU验收的source_commit为上述724a340，云端测试时源码干净。P1A五个源码/测试文件hash、协议/配置/Prompt/parser、60个benchmark文件和8个policy tokenizer/config资产核验通过；239项历史baseline校验通过。此次只变更预检文档/证据，不改Runner或评估协议。

`full_run_code_commit=null`。正式执行批准后，在启动时冻结实际HEAD；本次文档归档提交不是模型运行提交。归档SHA通过本文件Git History定位。

最初电信、移动入口均在认证前关闭；用户确认连接信息后，以独立SSH参数重试电信入口，握手和密码认证成功。确切故障原因未确定。认证凭据未写入仓库或报告。

## P1B Resource Preflight

| 字段 | 当前结论 |
| --- | --- |
| Repository | PASS：云端同步P1A代码；后续文档归档另行同步 |
| GPU | PASS：1×RTX5090，32607MiB；查询时无compute进程，仅Xorg图形占用 |
| Driver / CUDA | driver595.84；驱动支持CUDA13.2，Torch runtime12.9，二者不是同一版本字段 |
| Environment | Python3.12.13、Torch2.10.0+cu129、Transformers5.7.0、vLLM0.19.1、FlashAttention2.8.3、tokenizers0.22.2；与历史Pilot一致 |
| Model weights | PASS：Qwen/Qwen2.5-7B @ d149729398750b98c0af14eb82c78cfe92750796；4 shards及3配置/index文件的bytes/SHA一致，总15231300464bytes，无需重下 |
| Disk | PASS（容量）：系统盘/dev/vda1 ext4；检查时约130GiB可用，超过5GiB最低余量 |
| Inodes | PASS：12736024可用，超过100000最低余量 |
| Persistent storage | NOT VERIFIED：仅发现根系统盘，用户说明关机后保留实例；重启/释放后的文件恢复保证尚未独立核验；容量/文件系统检查不能替代平台持久化保证 |
| Backup destination | 本地`/Users/hr/Documents/Lesson/pa5-experiment-backups/preflight/20261010-p1b0/`；历史Smoke往返恢复PASS，未来Full持续备份尚未配置 |
| Pilot throughput | MMLU5.4087、GSM1.0726、Alpaca0.6341、Safety1.1644 examples/s，各20题历史测量 |
| Estimated generation time | 5181.37秒≈86.36分钟，仅历史外推 |
| Estimated total time | 初步2–3小时；长输出、磁盘延迟、分别加载模型、故障处理和备份可能延长，非保证 |
| GPU hourly price | 3.16元/小时（用户2026-10-10提供，未读取控制台账单） |
| Incurred cost | UNKNOWN |
| Estimated cost | 2–3小时约6.32–9.48元；准备/空闲/存储费用另计，非获批额度 |
| Current shutdown window | 用户预计2026-10-11 00:13 +08:00关机；23:18检查时仅余约55分钟，不足86分钟纯生成外推 |
| Maximum approved budget | BUDGET_APPROVAL_PENDING |
| Maximum approved runtime | RUNTIME_APPROVAL_PENDING |
| Full execution approval | NO，当前授权仅P1B-0 |
| P1B_EXECUTION_READY | NO |

## CPU / backup evidence

云端CPU测试命令（不加载模型）：

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -m pytest tests/test_qwen_full.py tests/test_qwen_baseline.py \
  tests/test_qwen_preflight.py tests/test_metrics.py tests/test_supplement_metrics_edges.py \
  -q -p no:cacheprovider --tb=short
```

结果：**80 passed in 50.73s**。这是云端环境/文件系统验收，补充P1A本地测试；没有扩展SFT/DPO/GRPO中原有未实现函数。

系统盘候选目录运行既有`scripts/verify_qwen_full_cpu.py`：**16266/16266输入与Mock保存、独立复算和导出schema均PASS**。4个计时阶段合计约312.59秒（5.21分钟），其中Mock写入252.39秒；云端IO开销高于本地，但不能由此推断GPU吞吐。完整结果见[full-cpu-report.json](../../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261010-p1b0/full-cpu-report.json)。CPU driver命令：`TMPDIR=/root/pa5-supplement-setup/20261010-p1b0/cpu-tmp .venv/bin/python scripts/verify_qwen_full_cpu.py --report /root/pa5-supplement-setup/20261010-p1b0/full-cpu-report.json`（沿用上方offline/PYTHONDONTWRITEBYTECODE环境）。

Mock只用于工程验收，不是模型输出或正式Base成绩。如果之后改用不同持久云盘，需在实际挂载重新验证IO。

备份使用原有`20261003-smoke-03`，没有重新生成：云端打包→下载本地并验SHA→上传新文件名→独立目录解包→28个文件bytes/SHA一致，4个raw JSONL可解析。压缩包32755bytes，SHA256=`a0045cf1985c47e26f89eebe54a4b173a448e41b23de2f04677a59adbf9cfeb3`。恢复位置/逐文件inventory见[backup-restore-check.json](../../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261010-p1b0/backup-restore-check.json)。本地副本独立于云实例；未来Full必须另行持续备份并验收，不能用Smoke探针代替。

云端没有tmux；已有setsid/nohup/systemd-run。短CPU进程使用独立session，在创建它的SSH命令channel退出后继续执行并fsync成功（PID=SID，PPID=1）。这仅验证命令channel脱离，SSH master仍在线；未模拟真实断网/重启/释放，也未部署Full后台进程。正式运行需进程锁、唯一run、独立日志和持续备份，恢复前检查活跃进程。

## Runtime / budget / stop policy

历史Pilot外推：MMLU约43.3分钟、GSM8K约20.5分钟、Alpaca约21.2分钟、Safety约1.4分钟。每任务仅20题，长度分布与Full可能不同；本轮不跑新GPU Pilot校准。CPU Mock耗时仅评估工程开销，不能作为GPU吞吐。

当前时价为3.16元/小时，建议下一次开机安排2–3小时，并讨论**最多3小时 / 9.48元GPU运行额度**；准备/空闲等费用另计。这只是建议，尚未获批。用户预计10月11日00:13关机；23:18时仅余约55分钟，不足86分钟纯生成外推，因此本次不建议开始Full或临时拆分一部分抢跑。若用户批准更小额度，提前停止保存PARTIAL。`--max-seconds`限制累计attempt的下一批准入，模型加载/正在执行批次可越过上限；它不自动关闭云实例，也不是精确计费封顶。不同task独立run时必须另跟踪四任务累计预算，不能各自重复使用同一总额度。

获批后复用[P1B执行命令](p1b-execution-commands.md)，不另建推理Runner。CLI已检查，正式`--approve-full`命令未运行。Full结束后再评分、独立复算、人审包、备份和归档；当前Alpaca Win Rate NOT RUN、LC NOT VALIDATED、Safety Score NOT RUN，人审状态不变。

## Remaining blockers / next gate

1. 确认系统盘在关机、重启、释放实例后的保留规则，或提供已确认的独立持久云盘挂载；验证最终产物位置及外部副本恢复。未同步到独立备份的新raw仍无释放实例后的恢复保证，不能仅承诺“结束后再下载”。
2. 用户已提供3.16元/小时时价；仍需批准费用上限和最长累计运行时间，并安排足够的开机窗口。已产生账单保持UNKNOWN。
3. 汇报P1B-0结果后，取得单独的**P1B-1 Full执行批准**。启动前再确认HEAD、GPU空闲、空间和备份状态。

本次技术检查可归档，但**完整Preflight尚未PASS，P1B_EXECUTION_READY=NO**。按用户阶段边界停止，不自动开始Full。
