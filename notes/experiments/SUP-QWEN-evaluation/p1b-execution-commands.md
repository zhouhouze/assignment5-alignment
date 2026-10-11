# P1B — 可执行命令与资源 Gate（尚未执行）

当前P1B-0.5备份验收通过；`P1B_EXECUTION_READY=NO`，真实Full **NOT RUN**。最新周期备份/保护命令见第6节。以下命令对应本轮已实现的 CLI，**只在用户另行批准 P1B、确认金额/时长上限和现场资源后执行**。本文件本身不是批准。

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

## 6. P1B-0.5 新增：周期备份与备份过期保护（正式启动命令，尚未执行）

2026-10-11：备份验收见[p1b-incremental-backup-acceptance.md](p1b-incremental-backup-acceptance.md)，资源/费用见[检查单](p1b-resource-cost-checklist.md)。本轮只验收CPU备份；**以下真实Full命令必须在用户单独批准P1B-1、金额/累计时间和存储机制后执行**。原协议不变。不要把本文件里的命令复制进当前验收任务执行。

### A. SSH master（Mac独立终端）

重新确认当日端口；当前提供的为32124。交互输入密码，不写入命令、环境文件或Git。启用keepalive，后续备份用BatchMode；若连接失效则备份失败，guard会过期停止实验，需重新认证恢复。

```bash
ssh -4 -F /dev/null -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=2 \
  -o ControlMaster=auto -o ControlPersist=600 -o ControlPath=/tmp/pa5-ssh-backup-live \
  -p 32124 root@180.127.11.177
```

### B. 云端准备（仅P1B-1获批后）

在`/root/cs336/pa5-supplement`、正确归档HEAD且clean时执行。以下使用已验收系统盘作为工作区、Mac作为独立持久副本；**系统盘不因此获得释放后的保留保证**。若更换挂载，重验IO。批准额度由用户给出，不从建议值自动赋值；费用包括哪些部分也需明确。

```bash
cd /root/cs336/pa5-supplement
: "${P1B_MAX_SECONDS:?Set explicitly approved total attempt seconds}"
: "${P1B_APPROVED_BUDGET_CNY:?Set explicitly approved expense ceiling}"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PY=/root/cs336/pa5-supplement/.venv/bin/python
export P1B_STORE=/root/pa5-supplement-setup
export RUN_ID="qwen-full-$(date -u +%Y%m%dT%H%M%SZ)"
export RUN_DIR="$P1B_STORE/full/$RUN_ID"
export ACK_PATH="$P1B_STORE/backup-health/$RUN_ID.json"
export MODEL_PATH="$PWD/models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796"
export P1B_MAX_SECONDS P1B_APPROVED_BUDGET_CNY

git status --short
git rev-parse HEAD
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
df -h "$P1B_STORE"
df -i "$P1B_STORE"
"$PY" -m cs336_alignment.qwen_baseline prepare --stage full \
  --task mmlu gsm8k alpaca_eval simple_safety_tests \
  --run-id "$RUN_ID" --output-dir "$P1B_STORE/full" \
  --dataset-root "$PWD" --config configs/qwen_baseline_gate.json
"$PY" -m cs336_alignment.qwen_baseline validate --run-dir "$RUN_DIR"
printf '%s\n' "$RUN_ID"
```

检查输出后再进入下一步；GPU被占用、dirty、预算未定、空间不足或协议漂移均停止。本轮只用一个包含四task的run，共享累计max-seconds；不要同时启动多个实验。货币上限由操作者按真实费率/已耗时间监控，Runner参数不自动退租或货币封顶。

### C. Mac初始备份和周期worker（独立终端）

将B输出的**同一个RUN_ID**填入；不要另生成时间戳。Mac保持开机/网络，合盖睡眠仍会失联。下面前台worker在终端中持续运行，Ctrl-C停止；无需Codex会话保持活跃。已有工作worker时不要重复启动，同一store有flock保护。

```bash
cd /Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement
: "${RUN_ID:?Paste exact cloud RUN_ID}"
export LOCAL_STORE="/Users/hr/Documents/Lesson/pa5-experiment-backups/full/$RUN_ID"
export REMOTE_RUN="/root/pa5-supplement-setup/full/$RUN_ID"
export REMOTE_ACK="/root/pa5-supplement-setup/backup-health/$RUN_ID.json"
BACKUP_ARGS=(
  --host root@180.127.11.177 --port 32124
  --control-path /tmp/pa5-ssh-backup-live
  --remote-python /root/cs336/pa5-supplement/.venv/bin/python
  --remote-script /root/cs336/pa5-supplement/scripts/qwen_artifact_backup.py
  --run-dir "$REMOTE_RUN" --store "$LOCAL_STORE" --ack-path "$REMOTE_ACK"
)
python3 scripts/qwen_artifact_backup.py pull "${BACKUP_ARGS[@]}"
python3 scripts/qwen_artifact_backup.py status --store "$LOCAL_STORE" --max-age 180
caffeinate -i python3 scripts/qwen_artifact_backup.py pull "${BACKUP_ARGS[@]}" \
  --cycles 0 --interval 60 --timeout 180
```

首轮须SUCCESS且ack已回传；worker运行后再启动D。所有逐轮日志在`$LOCAL_STORE/backup-events.jsonl`，传输错误stderr/incoming被保留。首轮/周期失败非零退出，先修复网络/磁盘/认证，重新运行相同store续传。不要删除旧快照/对象去“清空重试”。worker一次导出超时180秒可能先触发guard过期，安全停止优先于持续生成。

### D. 云端通过guard启动真实Full（仅获批后）

复用B的shell环境，确认C持续健康。下面Python launcher打开独立日志，实际guard PID明确；不使用可能再次fork而混淆PID的后台shell链。guard第一次检查ack通过后才spawn Runner。

```bash
"$PY" - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
run = Path(os.environ['RUN_DIR'])
(run/'logs').mkdir(exist_ok=True)
command = [sys.executable, 'scripts/qwen_backup_guard.py',
    '--ack-file', os.environ['ACK_PATH'], '--run-dir', str(run),
    '--max-age', '180', '--poll', '5', '--',
    sys.executable, '-m', 'cs336_alignment.qwen_baseline', 'run',
    '--run-dir', str(run), '--model-path', os.environ['MODEL_PATH'],
    '--approve-full', '--max-seconds', os.environ['P1B_MAX_SECONDS']]
with (run/'logs/generation.log').open('xb') as log:
    proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
        stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
print(json.dumps({'guard_pid': proc.pid, 'run_dir': str(run)}))
PY
```

`open('xb')`拒绝覆盖旧日志。进程/PID、completed/expected、elapsed/费用、GPU、空间和本地last SUCCESS需观察。ack失联超过180秒，guard在下一次poll后TERM自有进程组，30秒不退出则KILL；保留PARTIAL/事故。还需确认GPU计算进程实际退出，不能根据guard退出直接推断所有vLLM子进程都退出。不要自动终止其他实验。

恢复前检查没有活跃Runner，核验旧raw与剩余累计预算；重新启动Mac worker，确认新ack；使用同一run并在Runner参数里显式加入`--resume`，日志另用唯一新文件名。禁止直接重复初始启动命令覆盖/并行运行。

### E. 关闭、最终备份与恢复验收

确认guard/Runner退出且日志关闭；按上方第5节先validate、score（stdout日志在run外）、再validate。期间继续Mac worker，评分结束后Ctrl-C结束worker，确保同一store锁已释放，再在Mac执行：

```bash
python3 scripts/qwen_artifact_backup.py pull "${BACKUP_ARGS[@]}" --quiescent
python3 scripts/qwen_artifact_backup.py status --store "$LOCAL_STORE"
python3 scripts/qwen_artifact_backup.py restore --store "$LOCAL_STORE" \
  --destination "/Users/hr/Documents/Lesson/pa5-experiment-backups/restored/$RUN_ID"
```

最终snapshot必须quiescent=true、deferred为空、raw_count=16266；quiescent还保留pending/失败finalizing证据，但不计入raw_count。在相同代码/依赖/固定数据的独立恢复目录运行原`qwen_baseline validate`；本Gate实际验证了Mac恢复后回传云端，validate 16266/16266与finalized/source inventory通过。正式run必须再对自身执行一次，不能拿Mock证明替代。确认外部恢复成功、指标/manifest/checksum/registry已归档，才讨论关机/释放；释放保留磁盘的操作不包含在实验授权内。

Next task：取得P1B-1与预算/时长批准后才执行A–E；本轮CPU测试worker已停止。
