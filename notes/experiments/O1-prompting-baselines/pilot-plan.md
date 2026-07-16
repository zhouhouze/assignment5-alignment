# O1 Prompting Baselines - Pilot Plan

Status: Completed on 2026-07-16. Pilot results recorded in `pilot-results.md`.

## Experiment Question

Can the O1 prompting-baseline pipeline run a shared 20-example GSM8K Pilot across `question_only`, `r1_zero`, and `r1_zero_three_shot_gsm8k` with correct prompt control, grading, persistence, and comparable metrics?

## Purpose

This Pilot is an internal quality gate before the full GSM8K evaluation. It is intended to reveal systematic pipeline or prompt-control problems, estimate runtime and token cost, and produce preliminary behavior observations. It is not the official final experiment.

## Sample

- Dataset: `data/gsm8k/test.jsonl`
- Example IDs: `0-19`
- Selection rule: first 20 test examples
- The same 20 example IDs must be used for all three prompts.
- Do not replace samples based on results.

## Model And Runtime

- Model: `allenai/OLMo-2-0425-1B`
- SSH alias: `autodl-5090-new`
- Host: `autodl-container-ef994bb0c3-e9915dd2`
- GPU: NVIDIA GeForce RTX 5090, 32607 MiB
- Driver: 595.58.03
- Python: 3.12.3
- PyTorch: 2.10.0+cu129
- CUDA runtime: 12.9
- vLLM: 0.19.1
- FlashAttention: 2.8.3
- Git commit: `4af419ed9694301fa4a82b86de6c0e55b585e271`

## Prompts

- `question_only`
- `r1_zero`
- `r1_zero_three_shot_gsm8k`

## Generation Parameters

- `temperature = 1.0`
- `top_p = 1.0`
- `max_tokens = 512`
- `seed = 0`
- `batch_size = 4`
- `gpu_memory_utilization = 0.75`
- `limit = 20`

Transport setting:

- `HF_HUB_DISABLE_XET=1`

This is only a Hugging Face download/cache transport setting. It is not a model or generation parameter.

## Stop And Grader Rules

- `question_only`: no `</answer>` stop string; `question_only_reward_fn`
- `r1_zero`: `stop=["</answer>"]`, `include_stop_str_in_output=True`; `r1_zero_reward_fn`
- `r1_zero_three_shot_gsm8k`: `stop=["</answer>"]`, `include_stop_str_in_output=True`; `r1_zero_reward_fn`

Ground truth extraction:

```text
answer.split("####")[-1].strip()
```

## Output Directory

```text
/root/autodl-tmp/cs336/results/O1-prompting-baselines/<timestamp>/pilot
```

## Success Criteria

- 60 total generations.
- Exactly 20 rows per prompt.
- All three prompts use identical example IDs `0-19`.
- All responses are non-empty.
- JSONL outputs can be reread.
- Category counts sum to 20 for each prompt.
- Stop/grader configuration is correct for each prompt.
- `temperature`, `top_p`, and `max_tokens` are recorded correctly for every row.
- No CUDA OOM.
- No residual vLLM process after completion.
- `pyproject.toml` and `uv.lock` remain unchanged.

## Stop Conditions

- SSH failure.
- Wrong branch or unexpected commit.
- Dirty cloud working tree beyond this Pilot plan before launch.
- `pyproject.toml` or `uv.lock` changes.
- vLLM model load failure.
- CUDA OOM.
- Empty response.
- Prompt IDs differ across prompts.
- Incorrect stop or grader configuration.
- Fewer than 60 Pilot rows.
- JSONL readback failure.
- Data disk free space below 15GB.
- Script attempts to enter Full or GRPO.

## Not In Scope

- Full GSM8K evaluation.
- GRPO implementation or training.
- Multiple seeds.
- Prompt tuning.
- Changing official prompts, graders, or generation parameters.


## Pilot Outcome

- Completed with exit code 0.
- Output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot`
- Total rows: 60.
- Validation result: core pipeline checks passed, but R1 close-tag retention was not universal.
- Full GSM8K was not run.
