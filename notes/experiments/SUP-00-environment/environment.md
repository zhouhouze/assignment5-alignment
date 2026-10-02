# SUP-00：环境与仓库审计

日期：2026-10-02（Asia/Shanghai）。Gate A 审计完成，执行环境 **BLOCKED / 尚未就绪**。本轮仅审计、离线CPU测试和计划，不执行baseline generation、SFT、DPO或70B judge。

## 官方来源与隔离

- 官方本地手册：`cs336_spring2026_assignment5_supplement_safety_rlhf.pdf`，封面 Version 26.0.0、Spring 2026；已提取并核对第2–6节。
- 基础提交：`c2734a26308710949fe13226960a1e8cece94b7e`，本地main与upstream/main指向相同提交；本轮没有声称已检查上游最新远端。
- 独立分支：`learning/pa5-supplement`。
- 独立worktree：`/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement`。此目录是持久工作区，请勿当作普通tmp清理。
- origin：`git@github.com:zhouhouze/assignment5-alignment.git`；upstream：`https://github.com/stanford-cs336/assignment5-alignment`。
- 从官方基础提交创建，没有继承个人O1/O2实现、报告或产物；官方仓库本来包含的Main脚手架保留。本轮不修改任何核心实现、adapter、测试或依赖锁。
- Main原工作区维持`learning/grpo-foundations`与原有未提交文件。当前Supplement借用本地已有Python解释器及第三方依赖运行测试，不复用Main算法实现。
- 已读取README、pyproject、uv.lock、CHANGELOG、三份Supplement tests、相关adapter docstring及官方judge脚本。

## 云端实测

| 项目 | 结果 |
| --- | --- |
| 主机 / 系统 | ubuntu24 / Ubuntu 24.04.3 LTS，Linux x86_64 |
| GPU | 1 × RTX5090，32607MiB；15MiB占用、利用率0% |
| 驱动 | 595.84；nvidia-smi标注CUDA13.2仅为驱动能力，不是已安装PyTorch运行时 |
| 系统盘 | 196G，已用28G，可用159G |
| 默认Python | 3.14.7，不满足项目 `>=3.12,<3.13` |
| uv / git | 均未在PATH找到；git状态/分支/log/remote命令均报command not found |
| Python包 | 当前Python的metadata中torch、transformers、vllm、flash-attn、huggingface-hub、uv均不存在 |
| 项目 / 课程共享卷 | `/root/cs336` 与 `/mnt/cs336-a5-supplement` 均不存在 |

本轮没有安装包、变更驱动或启动GPU进程。后续经批准，在独立Python3.12环境中装uv/git并恢复本分支，使用 `uv sync --frozen --extra gpu --no-install-package flash-attn` 再 `uv sync --frozen --extra gpu`；复核Torch/CUDA/FA2/vLLM兼容性后才准入推理。README的普通uv sync未显式包含gpu extra，不能据此认定已安装GPU依赖。

锁定目标：Torch2.10.0+cu129（Linux GPU）、Transformers5.7.0、vLLM0.19.1、FA2 2.8.3、AlpacaEval0.6.6。FA2为pyproject指定的社区wheel，需保持URL和lock校验。服务器当前均未安装/验证。

## 模型访问与版本

通过服务器读取公开HF API元数据，未下载模型权重。两个仓库均为manual gated。模型固定revision候选如下，tokenizer计划使用同一仓库同一revision：

| 模型 | HF API返回的revision | config.json访问 |
| --- | --- | --- |
| meta-llama/Meta-Llama-3.1-8B | d04e592bb4f6aa9cfee91e2e20afa771667e1d4b | HTTP401 |
| meta-llama/Llama-3.3-70B-Instruct | 6f6073b423013f6a7d4d9f39144961bfbfbc386b | HTTP401 |

本地和云端的标准HF环境变量/默认token路径均未发现凭据。401是本次未认证访问失败，**不能推断用户HF账号是否已经接受license或获批**。tokenizer文件访问、实际下载和导入仍未验证。下一步应由用户在服务器安全登录HF账号，分别验证两个gated repo；不要将token写进聊天、Git或manifest。若revision不可访问，hard stop，不静默换到main或镜像版本。

## 数据可用性

以下均已在Supplement本地worktree找到并逐文件计算SHA256；尚未迁移到新服务器。详见 `artifacts/pa5-supplement/audit/20261002/dataset-inventory.json`。

| 数据 | 数量 |
| --- | ---: |
| MMLU test / dev / val | 14042 / 285 / 1531（各57 subjects） |
| GSM8K test / train | 1319 / 7473 |
| AlpacaEval（附GPT-4 Turbo reference） | 805 |
| SimpleSafetyTests | 100 |
| HH harmless-base | 42537 |
| HH helpful-base | 43835 |
| HH helpful-online | 22007 |
| HH helpful-rejection-sampled | 52421 |

HH合计160800为过滤前文件记录数，并非合格单轮DPO训练样本数。本轮只盘点，尚未进行Gate H数据质量审查。

SFT缺失：课程已混合、预处理成单轮prompt/response的 `safety_augmented_ultrachat_200k_single_turn/{train,test}.jsonl.gz`。该文件原在Modal课程共享卷。仅下载原始UltraChat-200K和SafetyTunedLlamas不构成等价恢复；需取得课程数据并记录hash，或先获准采用有版本/配比/处理规则/划分记录的替代数据方案。未验证Modal权限，不擅自调用/计费。

## Supplement测试基线

实际命令（在Supplement worktree执行）：

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python -m pytest tests/test_data.py tests/test_dpo.py tests/test_metrics.py -q --tb=short
```

实际结果：**7 failed，0.76秒**，均为NotImplementedError。

- test_data：2失败，均首先停在packed dataset；batch迭代函数尚未被执行验证。
- test_dpo：1失败，停在per-instance loss adapter。
- test_metrics：4失败，停在MMLU/GSM8K parser adapters。
- 无收集/依赖错误；本地tokenizer夹具和tiny GPT2权重可离线读取。没有加载8B/70B。
- 本地解释器Python3.12.13，Torch2.10.0、Transformers5.7.0、pytest8.3.5、tokenizers0.22.2。
- 日志：`artifacts/pa5-supplement/audit/20261002/supplement-tests.txt`。这是未实现基线，不是测试通过，也不是云端GPU验证。

## 评估可靠性发现

1. Base使用`prompts_safety/zero_shot_system_prompt.prompt`，停止词`# Query:`；不能沿用Main boxed/R1 grader。
2. 官方§5明确要求Post-SFT改用Alpaca SFT外层模板，生成参数保持一致。必须记录这个prompt变化，Base→SFT不是纯权重单变量对比。
3. AlpacaEval需导出JSON数组（四个兼容字段），同时保留更完整raw JSONL。
4. 官方Safety helper输入字段是`prompts_final`和`output`。其现有解析把一切不以true开头的judge输出算safe，空答或异常文本可能被误记为安全。后续必须保留judge raw并报告无效判断，单列官方分数与严格有效标签统计，不静默改写官方指标。本轮只记录问题。
5. AlpacaEval配置为2卡、max_model_len7000、batch_size900；不应把这组配置直接视为在任意2张卡上可运行。Safety helper默认上下文6144，judge应先做小样本显存校验。

## 容量和下一阶段门槛

估算为规划值，不是实测训练峰值：8B BF16权重约16GB（约15GiB），70B BF16约140GB（约130GiB），均不含KV/cache/activation。当前159G空闲适合先恢复8B baseline，不能同时囤积所有模型与多个训练checkpoint。

- Baseline阶段建议80–100GB可用工作空间（环境、8B缓存、输出、余量）；现有磁盘够用。
- SFT阶段建议150–250GB工作空间，控制checkpoint数量；8B最终BF16权重约16GB，完整AdamW续训状态可能数十至百GB，取决于状态dtype/主权重保存方式。
- DPO+70B judge共存建议300–500GB工作空间；按阶段下载/删除可降低需求。先验证归档再清缓存。
- 长期最小归档只保存代码/锁/版本/hash/raw/指标/日志/人工记录及不可重下载的训练checkpoint；不保存重复基础模型或完整venv。

硬件：现有5090先用于8B推理，小batch/受控上下文验证，不量化、不offload。SFT优先80GB或更大显存，是否足够仍需按实际optimizer状态与activation实测；单32GB不按原方案开Full。DPO采用两张大显存卡分别放policy/reference；70B judge另行安排双大显存卡推理，不能把“任意双卡”当作显存足够。

审计结论：Gate A记录完成，但环境验收未通过；下一轮先修环境/HF访问，再逐个实现parser和baseline runner。不得直接进入SFT/DPO。下一轮需要用户批准范围。
