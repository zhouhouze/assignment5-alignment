# O1 Prompting Baselines - Full Plan

Status: Attempt 1 failed before producing official results. Reliability patch is required before Full Attempt 2.

## Configuration

- Commit: `858f64562a31cf318b2f3ad9833ac146dc90d0e7`
- Branch: `learning/prompting-baselines`
- Model: `allenai/OLMo-2-0425-1B`
- Tokenizer: `allenai/OLMo-2-0425-1B`
- Dataset: `data/gsm8k/test.jsonl`
- Dataset SHA256: `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`
- Sample count: `1319`
- Example IDs: `0-1318`
- Prompts: `question_only`, `r1_zero`, `r1_zero_three_shot_gsm8k`
- Prompt SHA256: `{'question_only': 'bff41d4d354078f7c7adde76fabf70c086aa54a29fd4fb0e15a8f32b3ed27501', 'r1_zero': '56213732da87e12ace60a2b88a16df0af18280fb0563a957cbecc938a6a2ac0e', 'r1_zero_three_shot_gsm8k': '91788d4fb0e8d81ec17066dc122572f02a6d2ec3ed762174c7b70fcf5fdf6193'}`
- Grader SHA256: `f88b29b0e76b3c28f969cb8b2f945e01b70aed2753306445d30822a192c54ec7`
- Seed: `0`
- Temperature: `1.0`
- Top-p: `1.0`
- Max tokens: `512`
- Batch size: `4`
- GPU memory utilization: `0.75`
- Launcher: `HF_HUB_DISABLE_XET=1 uv run --no-sync`

## Output

- Output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-150640/full`
- Log path: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/logs/o1-prompting-full-20260716-150640.log`
- Manifest: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-150640/full/full_manifest.json`

## Command

```sh
HF_HUB_DISABLE_XET=1 uv run --no-sync python scripts/prompting_baselines.py --mode full --prompt-name all --model-id allenai/OLMo-2-0425-1B --dataset-path data/gsm8k/test.jsonl --limit 1319 --seed 0 --batch-size 4 --output-dir /root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-150640/full --gpu-memory-utilization 0.75
```

## Stop Conditions

- CUDA OOM.
- vLLM generation exception.
- Missing completion object.
- Completion count differs from prompt count.
- ID mismatch.
- JSONL write/read failure.
- Parameter, model, prompt, grader, or commit mismatch.
- Data disk free space below 15GB.
- `pyproject.toml` or `uv.lock` changes.
- More than one inference process.
- Any GRPO path or non-O1 experiment starts.

## Empty Completion Policy

A successful vLLM request with an existing completion object and `completion.text == ""` is a valid model output, not a retry condition:

- Record `response=""`.
- Record `empty_response=true`.
- Record `generation_status="completed_empty"`.
- Record `error_type="empty_response"`.
- Pass the empty string to the official grader.
- Continue the run.

Do not retry or skip the example.
