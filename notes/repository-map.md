# Repository Map - Assignment 5 Alignment

Date: 2026-07-15

## Repository Status

- Branch: `main`, tracking `origin/main`.
- Working tree at orientation time:
  - Modified: `AGENTS.md`.
  - Untracked: `第五章笔记初版.pdf`, `第五章补充(DPO)笔记初版.pdf`.
- Notes added for learning orientation:
  - `notes/repository-map.md`
  - `notes/learning-log.md`
  - `notes/concept-map.md`

## Assignment Version

This repository is the Spring 2026 version.

Evidence:

- `README.md` title: `CS336 Spring 2026 Assignment 5: Alignment`.
- `README.md` points to `cs336_spring2026_assignment5_alignment.pdf`.
- `pyproject.toml` description: `CS 336 Spring 2026 Assignment 5: Reasoning RL`.
- `CHANGELOG.md` version `2.0.0` dated 2026-05-20 adds MaxRL and GSPO and changes the main task from Qwen/MATH to OLMo/GSM8K.
- The handout includes 2026-specific sections for Dr. GRPO, MaxRL, off-policy clipping, and GSPO.

## Official Sources Read

- `AGENTS.md`
- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `cs336_spring2026_assignment5_alignment.pdf`
- `tests/test_grpo.py`
- `tests/adapters.py`
- `tests/conftest.py` GRPO fixtures
- `cs336_alignment/modal_utils.py`
- `cs336_alignment/vllm_utils.py`
- `cs336_alignment/drgrpo_grader.py` high-level role only

## Core GRPO Functions

All required GRPO adapter functions currently live in `tests/adapters.py`.

- `run_tokenize_prompt_and_output` at `tests/adapters.py:13`
- `run_get_response_log_probs` at `tests/adapters.py:52`
- `run_compute_rollout_rewards` at `tests/adapters.py:88`
- `run_compute_group_normalized_rewards` at `tests/adapters.py:120`
- `run_compute_policy_gradient_loss` at `tests/adapters.py:159`
- `run_aggregate_loss_across_microbatch` at `tests/adapters.py:206`
- `run_grpo_train_step` at `tests/adapters.py:238`

Optional safety/RLHF functions appear later in `tests/adapters.py`, but they are outside the GRPO core orientation.

## Existing Scripts and Runtime Utilities

- `scripts/evaluate_safety.py`: safety evaluation script, not the main GRPO training loop.
- `cs336_alignment/modal_utils.py`: Modal helper template. Its example references `scripts/grpo.py`, but that file is not present in the current checkout.
- `cs336_alignment/vllm_utils.py`: vLLM server lifecycle, completion generation, and NCCL weight sync helpers for GPU/full-model experiments.
- `cs336_alignment/drgrpo_grader.py`: math answer grading and answer extraction utilities used for verified rewards.

## Missing or Student-Created Experiment Surface

- A full `scripts/grpo.py` training loop is expected by the handout/modal example but is not present yet.
- The current CPU test surface is centered on `tests/test_grpo.py` through `tests/adapters.py`.

## Baseline Test Command

Command:

```sh
uv run pytest -q tests/test_grpo.py
```

Result:

- 19 failed.
- Failure cause: each GRPO adapter raises `NotImplementedError`.
- First run also created `.venv` and installed 66 packages, including PyTorch and Transformers.


## 2026-09-14 — Standard GRPO 最新状态

- cs336_alignment/grpo.py：七个标准 on-policy 正式实现；variants/off-policy 保持未实现。
- tests/adapters.py：保留官方测试 hook 与 docstring，薄 wrapper 转发到正式模块。
- notes/experiments/O2-standard-grpo/：正式 checkout、环境验证、组件测试、手算和可重跑 CPU sanity 脚本。
- 云端正式目录：/root/cs336/assignment5-alignment-checkout，branch learning/grpo-foundations，HEAD 2267287 + 未提交 adapter 补丁。
- 原 /root/cs336/assignment5-alignment 文件副本保留。
- 本地和云端完整 tests/test_grpo.py 目前各为 7 passed / 12 expected unimplemented failures；不是旧的 19 failures 状态。
- HF training-side 与 vLLM rollout-side 已分别通过单卡 smoke；下一阶段仍需双 GPU，尚无 NCCL 或 GPU end-to-end 闭环验证。
