# O2 单 GPU 独立 Smoke 报告

日期：2026-09-14。硬件：1 × RTX 5090 32,607 MiB。模型：`allenai/OLMo-2-0425-1B`。训练侧与 rollout 侧在两个顺序执行的独立 Python 进程中运行；第二项开始前确认第一项已退出且显存回到约 15 MiB。

## HF Training-Side Smoke

命令：

```sh
uv run --no-sync python scripts/o2_single_gpu_smoke.py training \
  --output-dir /root/cs336/results/O2-standard-grpo/single-gpu
```

只加载 Hugging Face policy，没有启动 vLLM。使用第一道 GSM8K 问题的 `r1_zero` prompt，加一个正确回答和一个错误回答形成 group_size=2 的 mixed reward；这些回答由脚本固定提供，不是模型 rollout。执行 BF16 + FlashAttention 2 forward、log-prob/entropy、标准 GRPO loss、backward、梯度裁剪、一次 AdamW step 和 zero_grad。

| 指标 | 结果 |
| --- | ---: |
| model load | PASS，BF16 / `flash_attention_2` |
| batch / microbatches | 2 / 2 |
| response tokens | 64 |
| mean total / answer / format reward | 0.5 / 0.5 / 1.0 |
| loss | -0.09213036，finite |
| mean token entropy | 1.15234375，finite |
| grad norm before clipping | 5.1875，finite；max_grad_norm=1.0 |
| optimizer step | PASS |
| gradients cleared | PASS，全部为 None |
| PyTorch peak allocated | 14,250.65 MiB |
| PyTorch peak reserved | 14,802 MiB |
| nvidia-smi sampled peak used | 14,267 MiB |
| elapsed | 740.55 秒，包含首次约 5.95 GB 模型下载 |

Summary：`artifacts/O2-standard-grpo/single-gpu/training-side-summary.json`。

## vLLM Rollout-Side Smoke

命令：

```sh
uv run --no-sync python scripts/o2_single_gpu_smoke.py rollout \
  --output-dir /root/cs336/results/O2-standard-grpo/single-gpu
```

只加载 vLLM，没有 HF training model、backward 或 optimizer。第一道 GSM8K 测试题使用实际 `r1_zero` prompt，seed=0、temperature=1.0、top_p=1.0、max_tokens=64、n=2、stop=`</answer>` 并保留 stop 字符串。

| 指标 | 结果 |
| --- | ---: |
| vLLM model load | PASS，BF16，日志确认 FlashAttention 2 |
| requests / responses | 1 / 2，数量一致 |
| completion 0 | 64 tokens，finish_reason=length，reward/answer/format=0/0/0 |
| completion 1 | 52 tokens，finish_reason=stop，reward/answer/format=0/0/0 |
| rewards finite | PASS |
| nvidia-smi sampled peak used | 24,979 MiB |
| elapsed | 192.41 秒，包含首次 compile/cudagraph capture |
| shutdown | PASS；进程退出后显存约 15 MiB |

第一条在生成限制处截断；第二条漏掉“做松饼用掉 4 个蛋”，算成 26，并在 `</think>` 与 `<answer>` 之间换行，未满足评分器要求的严格 `</think> <answer>` 形式。两条均作为合法模型行为原样保存、评分，没有 retry、skip 或 resample。

Raw JSONL：`artifacts/O2-standard-grpo/single-gpu/rollout-side-raw.jsonl`。Summary 与完整 vLLM log 位于同目录。

## 已验证与边界

已验证：环境、标准 GRPO CPU 数学组件、mask/广播、梯度累积、HF 训练侧真实 GPU 更新、vLLM 推理侧真实生成、原始输出落盘。

尚未验证：HF policy 与 vLLM 同时驻留、两 GPU 划分、NCCL 权重同步、真实 rollout → reward → backward → optimizer → sync 闭环、更新后再生成、One-Step Two-GPU Smoke、50-Step Pilot、200-Step Full、4 seeds。

这两个独立 smoke 不能合并描述为完整 GRPO end-to-end 验证。Software ready for Two-GPU One-Step Smoke: YES。Current hardware ready: NO。
