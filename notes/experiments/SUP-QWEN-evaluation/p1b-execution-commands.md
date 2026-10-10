# P1B — 可执行命令与资源 Gate（尚未执行）

当前 `P1B_RESOURCE_CHECK_PENDING`、`P1B_EXECUTION_READY=NO`，真实 Full **NOT RUN**。以下命令对应本轮已实现的 CLI，**只在用户另行批准 P1B、确认金额/时长上限和现场资源后执行**。本文件本身不是批准。

## 1. 环境与存储验收

在真实 Supplement checkout 执行：

```bash
pwd
git status --short
git branch --show-current
git rev-parse HEAD
git ls-remote origin refs/heads/learning/pa5-supplement
nvidia-smi
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

云端必须 checkout 本次归档的准确 implementation commit（本报告所在 commit；从本地/远端核对），源码 clean。不要在未知 dirty 树执行 reset/覆盖；不要占用其他实验正在使用的 GPU。历史权重合格不能替代现场核验。

先由操作者把以下变量设成**已核实的真实路径和批准额度**，不猜测智星云挂载点。`PY` 为已验收 Python 环境中解释器的绝对路径；`P1B_STORE` 为已确认持久存储根目录；`P1B_MAX_SECONDS` 为批准的本次 run 累计 attempt 秒预算。建议审批时讨论2–3小时窗口，不能把历史外推当保证。

```bash
: "${PY:?Set the verified Python interpreter path}"
: "${P1B_STORE:?Set verified persistent storage root}"
: "${P1B_MAX_SECONDS:?Set the approved cumulative time budget in seconds}"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
MODEL_PATH="$PWD/models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796"
"$PY" -c 'from cs336_alignment.qwen_baseline import environment; import json; print(json.dumps(environment(), indent=2))'
df -h "$P1B_STORE"
df -i "$P1B_STORE"
```

确认权重/环境之外至少5GiB工作余量、100,000 inodes，再按实际预估调整；准备独立备份位置并确认保留策略。核验挂载所属云盘和实例释放后的保留承诺，不能仅凭 `df` 判断持久性。

在**目标挂载**再跑 CPU 文件系统/全量工程验收（不会加载 GPU 模型）：

```bash
mkdir -p "$P1B_STORE/cpu-tmp" "$P1B_STORE/preflight"
TMPDIR="$P1B_STORE/cpu-tmp" "$PY" scripts/verify_qwen_full_cpu.py \
  --report "$P1B_STORE/preflight/full-cpu-$(date -u +%Y%m%dT%H%M%SZ).json"
"$PY" -m pytest tests/test_qwen_full.py tests/test_qwen_baseline.py \
  tests/test_qwen_preflight.py tests/test_metrics.py tests/test_supplement_metrics_edges.py \
  -q -p no:cacheprovider --tb=short
```

这一步同时验 fsync/hard link/rename/flock 的基本可用性。失败即停。若软件不同，记录差异并验证 CPU 兼容，不称跨版本 response 字节级一致。

## 2. 准备一个独立真实 run（CPU，不生成）

仅在前述 Gate 与 P1B 批准完成后创建正式目录：

```bash
RUN_ID="qwen-full-$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="$P1B_STORE/full/$RUN_ID"
"$PY" -m cs336_alignment.qwen_baseline prepare --stage full \
  --task mmlu gsm8k alpaca_eval simple_safety_tests \
  --run-id "$RUN_ID" --output-dir "$P1B_STORE/full" \
  --dataset-root "$PWD" --config configs/qwen_baseline_gate.json
"$PY" -m cs336_alignment.qwen_baseline validate --run-dir "$RUN_DIR"
mkdir -p "$RUN_DIR/logs"
printf '%s\n' "$RUN_DIR"
```

`--dataset-root` 是包含 `data/` 子目录的根，不是 `data/` 本身。`--config` 是完整模型+generation JSON；冻结值变化会报错，不能静默切换模型/采样。需要只检查输入时改用独立临时目录和 `prepare --stage full --dry-run`；dry-run 目录以后不能切成真实 run。

原 Smoke/Pilot 命令仍可用：`prepare --stage SMOKE/PILOT --run-dir ...`，以及原 `run --model-path ...`。本轮不需要重跑历史实验。

## 3. 真实执行（本轮禁止启动）

建议在已安装的 tmux 会话中运行，或使用已有调度系统；不要让唯一进程依赖 SSH 连接存续。在该会话内重新设置/保留上述变量。

```bash
"$PY" -m cs336_alignment.qwen_baseline run --run-dir "$RUN_DIR" \
  --model-path "$MODEL_PATH" --approve-full --max-seconds "$P1B_MAX_SECONDS" \
  > "$RUN_DIR/logs/generation.log" 2>&1
```

run 在任何 vLLM 导入前验证配置/数据/已有 raw、干净 Git 状态，并按冻结 accepted weights inventory 检查**全部权重 bytes/SHA**。固定 BF16、TP1、batch4、512 tokens、greedy；不会调用 Judge。`run_code_commit` 取此时真实 HEAD，prepare commit 与 archive commit 分开保存。

`generation.log` 在首次命令启动前应不存在；恢复使用新的日志文件。不要对已有日志使用同名 `>`，也不要同时启动第二个 run/任务。

预算：统计所有 attempt 的实际 wall time；crash 没有 end 则保守扣整次预留额度。到上限停止提交下一批，保留 PARTIAL/FAILED。正在进行的模型加载/批可能越过秒上限，因此这是准入上限，不是精确计费截断，也不会自动关停/退租云实例。接近租期截止或磁盘余量不足时操作员停止进程，随后按恢复流程处理；不删除 partial。

## 4. 恢复

错误先检查日志和 `attempts/`。OOM、数量/身份不符、写失败时不要循环自动重试。数据/prompt/config 变化、命名 raw 损坏、duplicate ID 必须停止并保留事故；不要删坏文件“补跑涨分”。若恢复磁盘坏文件，只从可信持久副本按原 SHA 恢复，不根据答案好坏挑版本。

在恢复原因、资源和剩余额度核验后：

```bash
"$PY" -m cs336_alignment.qwen_baseline validate --run-dir "$RUN_DIR"
"$PY" -m cs336_alignment.qwen_baseline run --run-dir "$RUN_DIR" \
  --model-path "$MODEL_PATH" --approve-full --resume --max-seconds "$P1B_MAX_SECONDS" \
  > "$RUN_DIR/logs/resume-$(date -u +%Y%m%dT%H%M%SZ).log" 2>&1
```

显式 `--resume` 记录原事故摘要和缺失 ID，已提交 raw 不变；生成后未落盘的记录可能重新生成，这是本轮用户明确采用的恢复语义。不同模型/采样/Prompt 不可混入同一 run。源码变动默认拒绝，先 checkout 原执行代码；文档归档产生新 HEAD 时会记录各 attempt 的真实 commit。

## 5. 评分、关闭和迁移归档

确认 generation 命令退出、日志关闭，然后执行：

```bash
"$PY" -m cs336_alignment.qwen_baseline validate --run-dir "$RUN_DIR"
"$PY" -m cs336_alignment.qwen_baseline score --run-dir "$RUN_DIR" --score-version v1 \
  > "$P1B_STORE/${RUN_ID}-score-v1.log" 2>&1
"$PY" -m cs336_alignment.qwen_baseline validate --run-dir "$RUN_DIR"
(cd "$RUN_DIR/finalized/v1" && shasum -a 256 -c SHA256SUMS)
```

score 日志放在 run **之外**，避免 finalize 建立 source-inventory 后 CLI 打印继续改变被校验的日志。只有完整 expected==completed、独立复算一致、candidate schema/文件完整和 bundle 发布成功才能标 COMPLETED；既有 finalized 目录/日志不可修改。新评分改 `--score-version v2`，不覆盖 raw/v1。

将完整 run（包括 raw、selected、attempt/recovery/log、finalized 与失败证据）复制到独立持久位置，传输后在相同代码/配置/数据下运行 validate；默认仓库相对路径支持 checkout 迁移，外部绝对路径按 manifest 恢复挂载。报告、metrics、manifest、review、hash、恢复命令提交 Git；完整 raw 根据实际体积压缩或用已授权持久存储，registry 登记 bytes/SHA/run_id/date/location/restore/durability。不自动启用 LFS 或付费服务，不删除唯一 raw。模型权重只登记固定 revision 与文件 inventory，可重新下载；未来训练 checkpoint 另需真实保存。

P1B 结束后记录实际耗时/租费、错误与截断、人审 pending 和 Judge NOT RUN。此 runbook 没有启动 Full、没有下载模型。Next task：现场验收与取得 P1B 范围/预算批准。
