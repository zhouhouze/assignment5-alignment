# CS336 PA5 Supplement — 保留原有 Qwen 模型与路径的全流程恢复 Runbook（2026-11-07）

**目标：沿用原有 Qwen 模型及其固定版本、保留实际文件路径，让 P0–P10 实验按既定 Gate 逐步跑通；不要求或承诺计算结果 100% 一致。状态：DOCUMENTED / REMOTE RE-CHECK BLOCKED；本次不授权训练。**
实验身份：`PA5 Supplement Adapted Reproduction`（Qwen 路线，`directly_comparable_to_official=false`）。分支：`learning/pa5-supplement`。本 Runbook 与 [现场快照](../../../artifacts/pa5-supplement-qwen/environment/20261107-cloud-restore/onsite-environment-snapshot.json)一起作为 GitHub 入口。

## 0. 证据等级、限制与安全边界

- **用户现场核对（2026-11-07，非本轮重新登录验证）**：Ubuntu 24.04.3、1× RTX 5090、驱动 595.84；项目 `.venv` Python 3.12.13；Torch 2.10.0+cu129、Transformers 5.7.0、vLLM 0.19.1、FlashAttention 2.8.3；Qwen7B Base 的7个已登记模型文件 SHA 全部通过。服务器代码停在历史短 SHA `ad04ade`。短 SHA 所在 branch/完整 SHA **未现场复核**。
- **仓库既有不可变证据**：2026-10-11 Qwen Base FULL、GPU/environment/weights acceptance、P2-C Derived-v2 等报告；以各 run manifest 和归档 commit 为准，不能将历史报告误写成本轮现场生成的新结果。
- **本次会话工具侧**：尝试连通两个用户提供的 SSH 入口，TCP 29824 均报 `Connection refused`；这只说明本次运行环境无法直接登录，**不能据此认定云实例已停机**。没有再次执行 `nvidia-smi`、重新哈希远端权重、核验 OS/uv/驱动或启动 GPU 程序。
- **安全**：不把服务器公网 IP、端口、登录账户密码、密钥、HF/GitHub token、host fingerprint、云平台 ID 上传到 GitHub。通过云平台控制台/个人私密运维笔记取得最新 SSH 入口；首次连接核对控制台独立提供的 host key 指纹。此次在对话中出现过的密码应更换，优先使用 SSH 密钥和非 root 账户。禁止 `StrictHostKeyChecking=no`、密码出现在命令行/脚本/env文件/Git提交里。
- **可复现性**：同一 `Git SHA + uv.lock + 权重/Tokenizer SHA + 数据 SHA + Prompt/生成参数` 有助于复现实验**配置和输入身份**；无法保证云 IP、第三方轮子/模型源一直可访问，或 GPU 非确定性运算做到逐 bit 复现。每次恢复必须重新执行下列 Gate。
- **费用**：连接/核验前通过平台确认实例是否运行、磁盘是否保留、计费和实际硬件；不要假设当前机器/数据在停止或释放后仍存在。

## 1. 版本与来源台账

| 类别 | 固定/已知信息 | 来源与限制 |
|---|---|---|
| OS / GPU | Ubuntu 24.04.3；RTX 5090，历史 32607 MiB；driver 595.84 | 2026-11-07 用户现场核对；显存来自 P1 FULL 历史证据 |
| Python / GPU Python 包 | 3.12.13；Torch 2.10.0+cu129 (CUDA runtime 12.9)；Transformers 5.7.0；vLLM 0.19.1；FlashAttention 2.8.3 | 用户现场核对，待每次新环境重验。历史还记录 tokenizers 0.22.2、uv 0.12.13；**未声明本次 uv 版本已核对** |
| 依赖 | `pyproject.toml` + `uv.lock`；`scripts/setup_supplement_environment.sh` | Linux `--extra gpu`；FA2 使用 `pyproject` 指定的第三方预编译 wheel URL，供应链/可用性需复核 |
| 训练 Policy | `Qwen/Qwen2.5-7B` Base / tokenizer revision `d149729398750b98c0af14eb82c78cfe92750796` | [配置](../../../configs/pa5_supplement_qwen.json) |
| Base 权重 | 4 safetensors 分片 + `config.json`、`generation_config.json`、`model.safetensors.index.json` = **7文件**，总 15,231,300,464 bytes | [7文件 bytes/SHA](../../../artifacts/pa5-supplement-qwen/baseline/weight-acceptance.json)；**另有 tokenizer/preflight 文件清单，不能以这7文件代替** |
| Judge（规划） | `Qwen/Qwen2.5-72B-Instruct`，revision `495f39366efef23836d0cfae4fbe635880d2be31` | 72B 权重与真实 Judge **NOT RUN**；单张 RTX5090 不代表可运行 |
| SFT来源 | `garg-aayush/sft-cs336-assign5-datasets` revision `ac710ef808346bf458d7b093bfe4586cb15699d9` | 第三方镜像，不保证与 2026 官方 Modal 数据字节相同 |
| 当前 SFT 派生数据 | Derived-v2: Train 210325，SHA `0678b25fcfd387df125012efbf054d2379c5eff2205400c932b37414e9db21e8`；Validation 23108，SHA `ae6af19e5198f058ff08e8f36ffb028f3cf26fd2d45f90f99f4d99e5fb039ffc`；Sample1000，SHA `b26bbe382793889ccb397e7c8afdf64ad3e52f0109d191e66c424587fba596df` | [P2-C报告](../SUP-QWEN-02-sft/p2-c-derived-v2-report.md)；完整数据仍在用户 Mac 外部备份，非 Git repo |
| 历史 P1 FULL 代码 | `47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726` | 复现旧 RUN 时应使用对应固定 commit；不要以最新 branch HEAD 伪称旧跑法 |
| 2026-11-07 云端当前代码 | 用户报告短 SHA `ad04ade` | 远端未在本轮重连，**需先查看 `git status` 与完整 `git rev-parse HEAD`** |
| 本 Runbook 编写前 GitHub branch HEAD | `c9ac135918704d2425133e303a715928eaf575ae` | 编写时快照；本 Runbook 的归档 commit 可由文件 Git History 获得，今后以实际执行的完整 SHA 为准 |

**注意：** `nvidia-smi` 显示的 CUDA 上限来自驱动，与 PyTorch 的 `torch.version.cuda`（12.9）不是同一个概念。不要单凭驱动 CUDA 字段判断包版本错误。

## 2. 私密连接：先验证实例与 SSH 身份

先在云平台后台确认实例 ID、运行状态、SSH 地址、端口、入口运营商、用户以及 host-key 指纹。公网端口可能改变，因此**不将具体 SSH 端点写死在 GitHub**。

在本地可信终端执行（变量值从控制台手动输入，不保存进仓库；密码应由 SSH 交互提示输入，优先改为 SSH 密钥）：

```bash
read -r -p "SSH host (cloud console): " SSH_HOST
read -r -p "SSH port (cloud console): " SSH_PORT
read -r -p "SSH user (prefer non-root): " SSH_USER
ssh -o StrictHostKeyChecking=ask -p "$SSH_PORT" "$SSH_USER@$SSH_HOST"
```

如提示 host fingerprint 不一致，**停止并经控制台独立核验**，不得直接删除 known_hosts 或关闭验证以求连上。需要 sudo 的系统操作使用有权限账户按需申请，不为了复现实验默认使用 root。

## 3. 连接成功后：先取证，再同步代码

**不要在旧 checkout 上盲目 `git reset --hard`、`git clean -fd`、`git pull`，云端可能有只存在于旧工作区的文件。** 先只读查询（旧位置 `/root/cs336/pa5-supplement` 是历史 Manifest 所记载的路径；若已变化以 `pwd` 为准）：

```bash
cd /root/cs336/pa5-supplement       # 若路径不存在，先在实际工作区定位，勿创建假目录
pwd
git status --short --branch
git rev-parse HEAD
git branch -avv
git remote -v                      # 检查输出中是否意外带了 token；勿公开日志
git diff --stat
```

若旧树有未提交文件：先保全并核实其价值，**不得覆盖**。最安全的方式是在另一空目录取得最新 Supplement 分支：

```bash
mkdir -p "$HOME/pa5-recovery"
git clone --branch learning/pa5-supplement --single-branch \
  https://github.com/zhouhouze/assignment5-alignment.git \
  "$HOME/pa5-recovery/supplement"
cd "$HOME/pa5-recovery/supplement"
git fetch origin learning/pa5-supplement
git pull --ff-only
git status --porcelain
git rev-parse HEAD
git rev-parse origin/learning/pa5-supplement
```

上述目标目录**必须尚不存在**；若已存在应检查并使用新目录，避免覆盖。私有仓库认证使用安全的 credential helper/SSH key，**不要把 PAT 拼进 URL**。后续每个新 RUN 在开始前记录完整 HEAD SHA、tree状态、`pyproject.toml`/`uv.lock` SHA；真实复现旧 P1 FULL 时应改用第1节列出的旧 `run_code_commit` 独立 checkout，不要用最新开发版代替。

## 4. 恢复 Python / GPU 依赖

前置条件：系统具备 `git`、`uv`，GPU 驱动可见，云镜像/网络允许下载锁定依赖。历史验收使用 uv 0.12.13，若需严格重演应先检查并固定 uv 版本。

```bash
cat /etc/os-release | head -n 8
uname -m
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
uv --version
git --version
bash scripts/setup_supplement_environment.sh
.venv/bin/python - <<'PY'
import sys, importlib.metadata as m
expected = {
  "torch": "2.10.0", "transformers": "5.7.0",
  "vllm": "0.19.1", "flash-attn": "2.8.3",
  "tokenizers": "0.22.2",
}
for name, version in expected.items():
    actual = m.version(name)
    assert actual == version, f"{name}: {actual} != {version}"
    print(f"{name}={actual} PASS")
assert sys.version_info[:3] == (3, 12, 13), sys.version
import torch
assert torch.version.cuda == "12.9", torch.version.cuda
assert torch.cuda.is_available(), "CUDA unavailable"
print("GPU:", torch.cuda.get_device_name(0))
assert "5090" in torch.cuda.get_device_name(0)
x = torch.ones(1, device="cuda")
assert float((x + 1).item()) == 2.0
import vllm, flash_attn
print("CPU package checks + tiny CUDA sanity PASS")
PY
```

`scripts/setup_supplement_environment.sh` 是**仅安装依赖**的既有脚本，不会自动下载模型权重或启动训练；两段 `uv sync --frozen --extra gpu` 以及针对 FA2 的先后安装流程不可随意调换。**不要用普通 `uv run` 隐式 re-sync 去掉 GPU extra**；后续测试用 `.venv/bin/python` 或 `uv run --no-sync`。若驱动/外部 wheel 无法下载或版本/导入失败，应停止并保留日志，不偷偷切换 Torch/FA2/vLLM 版本。

## 5. 不下载权重：用固定 Manifest 重新做完整 SHA 校验

历史权重目录在 `/root/cs336/pa5-supplement/models/qwen-baseline-7b/<policy-revision>`。若采用新 checkout，可让 `QWEN_WEIGHTS_DIR` 指向**现有只读目录**；无需拷贝15GB或重新下载。Tokenizer 的历史目录为 `models/qwen-preflight/Qwen2.5-7B`，它有独立的8文件 SHA清单。

```bash
export QWEN_WEIGHTS_DIR="/root/cs336/pa5-supplement/models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796"
export QWEN_TOKENIZER_DIR="/root/cs336/pa5-supplement/models/qwen-preflight/Qwen2.5-7B"
.venv/bin/python - <<'PY'
import hashlib, json, os
from pathlib import Path
manifest = json.loads(Path("artifacts/pa5-supplement-qwen/baseline/weight-acceptance.json").read_text())
weight_files = manifest["weights"]["files"]
assert len(weight_files) == 7, len(weight_files)
def verify(path, nbytes, digest):
    assert path.is_file(), f"MISSING: {path}"
    assert path.stat().st_size == nbytes, f"BYTES MISMATCH: {path}"
    with path.open("rb") as f:
        got = hashlib.file_digest(f, "sha256").hexdigest()
    assert got == digest, f"SHA MISMATCH: {path}"
for name, entry in sorted(weight_files.items()):
    verify(Path(os.environ["QWEN_WEIGHTS_DIR"]) / name, entry["bytes"], entry["sha256"])
    print("7B weight OK:", name)
tokenizer_files = manifest["tokenizer_inventory_verified"]
assert len(tokenizer_files) == 8, len(tokenizer_files)
for entry in tokenizer_files:
    verify(Path(os.environ["QWEN_TOKENIZER_DIR"]) / entry["file"], entry["bytes"], entry["sha256"])
    print("7B tokenizer/preflight OK:", entry["file"])
print("MODEL 7/7 + TOKENIZER 8/8 SHA PASS")
PY
```

任何路径、大小、SHA 不匹配立即 STOP。**7权重文件已通过用户现场复核，不代表此处8个 Tokenizer/配置文件也已在新连接中通过；必须分别检查。** 只有确实缺失、获得下载/费用授权、来源访问可用且完成CPU Gate之后，才按现有 `scripts/download_qwen_baseline_weights.py` 的固定 revision 恢复权重。禁止替换为 Instruct 版本、混合 revision 或忽略哈希。

## 6. 数据 / Benchmark / 实验状态隔离

- SFT 镜像原始数据 SHA、排除记录、mapping、Derived-v2 Train/Validation/Sample 的完整SHA与恢复步骤详见 [P2-C](../SUP-QWEN-02-sft/p2-c-derived-v2-report.md)；**完整 Derived-v2 位于用户 Mac 外部持久目录**（或由批准的原料重新派生），不自动从 GitHub 读取大文件。
- 训练前，必须在恢复/上传后用已提交的 `scripts/verify_qwen_sft_v2.py` 和清单校验。注意 Mac 备份与恢复副本在**同一 Mac 磁盘**，不等同异地灾备；使用云实例前应另确认副本、磁盘空间和传输费用。
- P1 既有四任务原始生成 16,266/16,266：MMLU 14042、GSM8K 1319、AlpacaEval 805、SimpleSafetyTests 100；其固定 input inventory、protocol 和每任务 raw/manifest 在 [P1 FULL证据](../../../artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/README.md)。不要把这些 holdout 数据输入 SFT/DPO。
- P1 Full 配置要从 **各任务 manifest** 读取；汇总条件是 BF16、TP1、`max_model_len=4096`、`gpu_memory_utilization=.75`、`max_num_seqs=4`、`max_num_batched_tokens=4096`、`enforce_eager=true`、`prefix_caching=false`、`generation_config=vllm`、`trust_remote_code=false`、temperature0、top_p1、n1、max_tokens512、prompt纯文本无chat wrapper（参见[报告](../SUP-QWEN-evaluation/p1b-full-baseline-report.md)）。不能仅凭模型权重SHA复现完整模型行为。
- 当前正式 Gate：**P2-D DATA ADMISSION=HOLD / NOT APPROVED**；P3核心Dataset/Batching/Training Loop未验收；SFT/DPO checkpoint不存在，72B Judge未运行。环境恢复成功只代表 `ENVIRONMENT_READY`，**绝不自动授权训练或新的 Base Full generation**。
- 对后续 SFT BF16 全参数训练而言，单张 RTX5090 32GB 不足以默认装下传统AdamW静态参数/优化器/梯度，更不能将72B Judge配置直接用于5090；另行评审 GPU 容量、预算与Gate批准。

## 7. 最小只读验收与成功/停止判据

```bash
mkdir -p "$HOME/pa5-recovery/audits"
.venv/bin/python scripts/audit_supplement_environment.py \
  --output "$HOME/pa5-recovery/audits/environment-$(date -u +%Y%m%dT%H%M%SZ).json"
.venv/bin/python -m pytest \
  tests/test_qwen_preflight.py tests/test_metrics.py tests/test_supplement_metrics_edges.py \
  -q --tb=short
```

此外记录 `git rev-parse HEAD`、`git status --porcelain`、`nvidia-smi`、模型+Tokenizer 文件SHA、固定输入数据Manifest SHA及测得的CUDA内核结果。原Supplement中某些GRPO/Packed Dataset接口仍有历史 `NotImplementedError`：按实际测试分类，不为求全绿修改官方测试或冒称 PASS。

**验收口径：**

| Gate | 通过要求 | 不通过如何处理 |
|---|---|---|
| CONNECT | 控制台确认实例有效、SSH身份与host fingerprint正确 | 不提供凭据、不禁用HostKey检查、不冒称在线 |
| CODE | 新 checkout 指向指定分支/完整commit，干净且无意外改动；旧云端历史代码留存 | 不reset/覆盖；分叉则新 checkout |
| DEPENDENCIES | uv.lock按`--frozen --extra gpu`恢复且实测指定版本、imports、tiny CUDA kernel可用 | 保留详细失败证据；不暗中替换依赖 |
| ASSETS | Qwen Base7个权重文件、额外8个Tokenizer/preflight文件逐项bytes/SHA核验 | 缺文件就STOP，获授权后才下载 |
| DATA/INPUTS | 目标实验需要的数据、Benchmark、Prompt、Manifest均与固定SHA匹配 | STOP；不拿未准入数据跑训练 |
| EXPERIMENT_GATE | 确认当前P2 HOLD/后续明确审批和资源预算 | **不运行训练、DPO、72B Judge** |

不要上传 shell history、SSH配置、`env` 全量输出、私有地址、密码、API token、个人数据和大量原始模型权重到GitHub。小型**脱敏**的审计报告、测试状态、运行commit和源SHA可提交新run目录；新run必须有独立run_id，不覆盖旧run。

## 8. 环境恢复及全流程进展

- `REBUILD_SPEC_READY`：Runbook、commit/lock/源身份和哈希锚点齐全，**本次可达成**。
- `REMOTE_CONNECTED`：本次无法从聊天运行环境连接SSH；**NOT VERIFIED**。
- `RUNTIME_RECOVERED`：需要新SSH现场恢复+包导入+CUDA验收；**NOT RUN**。
- `MODEL_ASSETS_VERIFIED_ON_2026-11-07`：**USER-REPORTED（7权重文件）**；不是本次聊天工具直接实测。
- `WORKFLOW_RESUMABLE_SPEC_READY`：原有模型、版本、路径、恢复步骤和后续Gate已记录；部分接口与资源尚未就绪，因此目前不能宣称已经端到端跑通。
- `EXPERIMENT_REPRODUCED`：不承诺逐bit复现；实际执行每个阶段后用新run_id记录结果、输入身份和完整证据。当前仅历史P1 Base Full完成，后续阶段尚未完成。


## 9. 保留原路径，按原有模型完成 P0–P10：下次实验接续台账

**目标定义：不追求与旧实验逐字节100%一致；追求同一Qwen实验路线下的模型身份不变、输入/代码/依赖可核验、路径可追溯，并按Gate逐阶段完成。** 恢复环境本身只是先决条件，不代表训练或Judge已经执行。

### 9.1 必须保留的历史绝对路径

| 资产 | 历史/现有位置 | 操作规则 |
|---|---|---|
| 云端旧 Supplement checkout | `/root/cs336/pa5-supplement` | **原路径原文件不覆盖**，先记录旧Git完整HEAD及dirty状态；2026-11-07用户报告短SHA `ad04ade`，仍需现场复查 |
| 新的隔离 checkout（建议，不是历史源路径） | `$HOME/pa5-recovery/supplement` | 从 `learning/pa5-supplement` 新clone；不用reset/clean覆盖旧项目；新实验记录实际checkout路径 |
| 云端原有Qwen2.5-7B Base模型 | `/root/cs336/pa5-supplement/models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796` | 7个权重/config文件按 [weight-acceptance.json](../../../artifacts/pa5-supplement-qwen/baseline/weight-acceptance.json) 逐项 bytes/SHA 校验；可从新checkout用原路径只读加载，不必移动 |
| 云端Tokenizer/Preflight | `/root/cs336/pa5-supplement/models/qwen-preflight/Qwen2.5-7B` | 另外8个文件独立核验，不能只查7个权重文件 |
| 云端原P1 Full outputs | `/root/pa5-supplement-setup/full/<run_id>` | 历史路径；可能随实例释放而丢失，不覆盖、不视作唯一备份 |
| Mac持久Supplement worktree | `/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement` | 保留此真实worktree，不删除为临时目录 |
| Mac原始SFT镜像 | `/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement/data/qwen-sft-mirror/sft-instruct` | 三个原始JSONL以登记的SHA为准，不改Raw |
| Mac历史Derived-v1 | `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1` | 保留旧版本，可作为v2独立校验输入 |
| Mac当前Derived-v2 | `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261031-p2c-derived-v2` | 数据已生成并独立校验，**正式训练准入仍HOLD** |
| Mac Derived-v2 tar备份 | `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261031-p2c-derived-v2.tar.gz` | SHA `f49a0e731637d1ab4ba5682a2a005dd57d7a2eb022e3c28827416216cc50e17c`；只恢复到新目录 |
| Mac P1 Full CAS备份 | `/Users/hr/Documents/Lesson/pa5-experiment-backups/full/<run_id>` | 保留objects/snapshots/LATEST整套，非仅单个manifest |
| Mac P1 Full打包存档 | `/Users/hr/Documents/Lesson/pa5-experiment-backups/full/p1b1-20261011-session/qwen-full-20261011T034800Z-verified-runs.tar.gz` | SHA `c9167497a800d803f2510f55201654465e376b905154e796f9c587150777b6a9` |
| 未来云端Derived数据及SFT/DPO checkpoints、72B权重 | **尚无正式生成并验收的绝对路径** | 第一次实际执行时绑定真实绝对路径和run_id、登记SHA、存到持久存储，不能编造或覆盖原路径 |

**注意**：“保留路径”指代码、权重、数据及产物的文件系统位置；不意味着把公网SSH入口/密码写入GitHub。SSH连接信息继续保存在云控制台或个人私密凭据管理器。

### 9.2 同一模型路线的后续全流程执行表

| 阶段 | 固定模型/输入 | 执行与结束条件 |
|---|---|---|
| P0 | 固定[Qwen Adapted配置](../../../configs/pa5_supplement_qwen.json)和评估协议 | 已冻结，恢复时核对版本及记录 |
| P1 Base | **Qwen/Qwen2.5-7B Base** `d149729398750b98c0af14eb82c78cfe92750796`；MMLU/GSM8K/AlpacaEval/Safety四任务 | 历史16,266/16,266 Full已完成；非必要不重做，用各run manifest和旧code SHA归档 |
| P2 | SFT Mirror Raw → Derived-v2（Train210325、Validation23108、Sample1000） | P2-C机器校验通过，**P2-D Data Admission HOLD**，当前禁止正式训练 |
| P3 | 同一Qwen Tokenizer、官方Alpaca模板、Dataset/Batching/训练loop | 先CPU实现和测试；尚未完成 |
| P4/P5 SFT | **以该Qwen2.5-7B Base为初始权重**、BF16全参数SFT，不换成Instruct/LoRA/量化；[训练设计](../SUP-QWEN-02-sft/sft-training-experiment.md) | 在P2/P3通过、批准硬件及费用后才Smoke→Pilot→Full。RTX5090 32GB不足以默认执行传统全参AdamW |
| P6 Post-SFT评测 | Base与实际SFT checkpoint，冻结相同Benchmark/Prompt | 保存新run_id与逐题raw/metrics，检查训练收益与alignment tax |
| P7/P8 DPO | 同一个已验收 SFT checkpoint 初始化policy+frozen reference；Anthropic HH偏好数据，[DPO计划](../SUP-QWEN-03-dpo/dpo-training-and-evaluation-plan.md) | CPU实现/测试后才Smoke→Full；**不能拿Base当reference** |
| P9 Judge + DPO后评测 | 固定Qwen2.5-72B-Instruct `495f39366efef23836d0cfae4fbe635880d2be31`；[Judge可靠性计划](../SUP-QWEN-evaluation/judge-reliability-plan.md) | 72B模型/真实Judge仍NOT RUN，需另外批准合适大显存硬件、先校验Judge可靠性 |
| P10 Data Flywheel | 使用Base/SFT/DPO实际指标及失败样本 | 训练效果分析→错误归因→下一轮数据建议；Benchmark仍只用于评估 |

**验收口径**：任何一步缺模型/数据/硬件/批准即记录BLOCKED并停止，不能为了“走完整个流程”静默换模型或绕过测试。真正完成P0–P10必须具备每个阶段的真实运行证据、所需checkpoint、输出SHA、验证和归档位置。**路径不变与版本一致有助于持续接续，但不承诺GPU输出逐bit一致，更不表示目前一张5090足以运行全部阶段。** 新实验产物使用唯一run_id，不写回旧Full和Derived目录。

