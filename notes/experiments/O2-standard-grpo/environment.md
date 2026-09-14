# O2 Standard On-Policy GRPO 环境审计

## 最新复核：本轮 Git / 环境 / CPU 组件授权

2026-09-14：用户后续明确允许在单 GPU 上完成 Git 恢复、环境验证和 CPU 组件实现。下方“BLOCKED”章节是上一轮审计历史，不代表本轮软件状态。

### Git 恢复完成

- 旧目录 `/root/cs336/assignment5-alignment` 保留，未 git init、未覆盖。
- 从 `https://github.com/zhouhouze/assignment5-alignment.git` clone 到 `/root/cs336/assignment5-alignment-checkout`。
- 远端没有 `learning/grpo-foundations`；从 `learning/prompting-baselines` 的 O1 HEAD 新建同名云端本地分支。`git merge-base --is-ancestor 2267287678062eefe5a2bd5f0e5f6a3a03f37565 HEAD` 成功。
- 新 checkout HEAD：`2267287678062eefe5a2bd5f0e5f6a3a03f37565`。
- clone 后工作区 clean；本轮软件同步后正式模块、薄 wrapper 和 smoke 脚本为待提交改动。
- 本地也继续使用 `learning/grpo-foundations`，保留既有文档与草稿改动。
- 应用补丁前已确认云端 adapter 无 diff，并备份到 `/root/cs336/results/adapters-before-o2.py`；所有补丁均先 `git apply --check` 后应用。

### 锁定依赖恢复与实际验证

读取正式 checkout 的 README、pyproject、lockfile 后执行：

```sh
export PATH=/root/cs336/bootstrap/bin:$PATH
export UV_CACHE_DIR=/root/cs336/cache/uv
uv sync --frozen --extra gpu --no-install-package flash-attn
uv sync --frozen --extra gpu
```

退出码 0。GPU 依赖是 optional extra，普通 `uv sync` 不足以安装 vLLM/FlashAttention。后续验证使用 `uv run --no-sync` 避免默认 extras 同步移除 GPU 包。未改锁文件或任意选版本。

| 检查 | 结果 |
| --- | --- |
| 云端 Python | 3.12.7 |
| PyTorch | 2.10.0+cu129，import 成功 |
| CUDA runtime | 12.9，available=True |
| GPU | 1 × RTX 5090，32,607 MiB，驱动 595.71.05 |
| CUDA matmul | seed=0，1024×1024 输入，结果 cuda:0，finite=True，synchronize 成功 |
| Transformers | 5.7.0，import 成功 |
| vLLM | 0.19.1，import 成功；没有启动 server 或模型生成 |
| FlashAttention | 2.8.3，来自仓库指定 wheel，import 成功 |
| FlashAttention kernel | BF16 输入 [1,16,2,64]，causal=True，输出同形状，finite=True，synchronize 成功 |
| 本地 CPU 环境 | Python 3.12.13 / Torch 2.10.0 / Transformers 5.7.0 |
| 本地完整 GRPO tests | 7 passed / 12 expected unimplemented variants failed，0.20s |
| 云端完整 GRPO CPU tests | 7 passed / 同样 12 expected failures，0.24s |

训练模型、rollout 模型、NCCL 同步、GPU 反向传播和 OLMo 端到端链路均未验证，不以 kernel 测试代替这些验证。

### 文件一致性与使用路径

本地与新云端 checkout 的 SHA256 一致：

```text
cs336_alignment/grpo.py fbe6d5d81427cf2420e979906cb2b436ed0eb6ab2f90941e863ccc8c00aedb1d
tests/adapters.py f0dd94992bb009382c50fc84a063d87930cfb3abec9020d5600f472d9a670874
scripts/o2_single_gpu_smoke.py fcc28277b2f5821ad50f458af5a6ca08ede606c4445b1d19f18312ed2032040e
pyproject.toml c724414eef01a9e74df29426de7a9411e1716acb97f9fab5b1019b173ac9a94d
uv.lock 0c58eabd82d0f9f3ecce25489a169f668f4458450b8d72999365ee7c63fa5629
```

`source /root/cs336/activate-pa5.sh` 现指向新 checkout 的环境；原激活脚本备份为 `/root/cs336/results/activate-pa5-before-o2.sh`。

远端日志：`/root/cs336/results/o2-checkout-setup.log`、`/root/cs336/results/O2-standard-grpo/full-cpu-test-final.log` 及 smoke 目录。只同步本轮 O2 软件补丁，没有上传其他笔记或完整本地 Git 历史。

当前结论：A/B/C 软件准备完成，后续又完成了训练侧和 rollout 侧两个互斥的单卡 smoke。仍只有一张 GPU，**Software ready for Two-GPU One-Step Smoke: YES；Current hardware ready: NO**。必须增加第二张可用 GPU 并获得下一阶段授权，才能验证完整闭环。本轮未执行双卡 smoke、pilot 或 full。

---

## 上一轮审计（保留历史）

审计日期：2026-09-14。范围：用户本轮要求的第一阶段云端环境审计及 Git 状态确认。

## 结论

**BLOCKED：只有一张可用 GPU，未满足本轮明确规定的双 GPU 架构。** 停止在环境阶段，不执行组件实现、CPU 测试、GPU smoke、50-step pilot 或 Full。Ready for 50-Step Pilot: NO。

## 本轮约束

用户要求：GPU 0 放 Hugging Face policy 与 optimizer，GPU 1 放 vLLM；少于两张可用 GPU 时停止，由用户决定下一步。O1 不重跑；仅 standard on-policy，禁入 variants；本轮上限为 one-step smoke，不能运行 pilot 或 Full。

## 云端实测

主机：智星云电信地址 `180.127.11.177:28028`。目录：`/root/cs336/assignment5-alignment`。

| 项目 | 结果 |
| --- | --- |
| GPU 数量 | 1 |
| GPU 型号 | NVIDIA GeForce RTX 5090 |
| 显存 | 32,607 MiB，总占用约 15 MiB |
| GPU 利用率 | 0%，仅显示进程 |
| 驱动 | 595.71.05 |
| nvidia-smi 显示 CUDA | 13.2；这是驱动支持信息，不是已验证的 PyTorch 运行时 |
| shell Python | 3.12.7 |
| 项目 .venv Python | 3.12.7 |
| torch 包版本 | 2.10.0+cu129 |
| transformers 包版本 | 5.7.0 |
| vllm 包版本 | 0.19.1 |
| flash-attn | 未安装 |
| Git 工作区 | 非 Git 仓库，没有 .git |
| 分支、commit、remote、clean 状态 | 无法报告；四个 Git 查询均返回 not a git repository |

版本由 `.venv/bin/python` 的 `importlib.metadata` 读取。**包已安装不等于导入、CUDA kernel、vLLM generation 或权重同步已验证。** 此前分阶段安装命令排除了 flash-attn；本次安装日志显示其他依赖已安装，未发现仍运行的 `uv sync` 进程。本轮未继续安装。

## 执行的审计命令

```sh
nvidia-smi
python --version
cd /root/cs336/assignment5-alignment
git status --short
git branch --show-current
git log -1 --oneline
git remote -v
.venv/bin/python --version
```

另通过 `importlib.metadata.version` 查询上述四项依赖，并读取 `/root/cs336/results/setup.log` 尾部及安装进程状态。

## 本地仓库

- 当前分支：`learning/grpo-foundations`。
- HEAD：`2267287678062eefe5a2bd5f0e5f6a3a03f37565`，O1 完成提交。
- `learning/prompting-baselines` 也指向该提交；`main` 位于 `c2734a2`。
- origin：`git@github.com:zhouhouze/assignment5-alignment.git`。
- upstream：`https://github.com/stanford-cs336/assignment5-alignment`。
- 工作区不 clean：学习日志有修改；实验清单、O1 中文报告及核验、O2 foundations 草稿、tmp 为未跟踪内容。本轮又新增此审计报告。
- 保留所有已有文件与分支；未创建、切换或删除分支，未提交或推送。

## 后续阶段状态

| 阶段 | 本轮状态 |
| --- | --- |
| Standard GRPO components | 未实现 |
| CPU unit tests | 未运行 |
| reward/advantage sanity check | 未运行 |
| one-step GPU smoke | 未运行 |
| loss、梯度、optimizer step | 未验证 |
| NCCL 权重同步 | 未验证 |
| raw training JSONL | 未产生 |
| 50-step pilot / Full | 未运行 |

前一轮 O1 的 5 项可靠性测试通过，不代表 GRPO 组件通过。本轮硬件门槛未满足，不能沿用 O1 推理成功记录宣称 GRPO 可训练。

## 下一步需要用户决定

维持当前双 GPU 方案时，需要提供至少两张可用 GPU 的新实例并重新审计。另一种选择是用户明确允许先在本地做 CPU 组件学习与测试，把 GPU 阶段推迟。单卡训练需要用户明确变更架构要求，不能自行采用。

即便硬件满足，还需补齐云端可追溯 Git checkout、确认依赖兼容性与 FlashAttention 配置，再按组件顺序和学习检查推进。不会复制本地不相关草稿或完整历史来绕过此前的上传审批限制。
