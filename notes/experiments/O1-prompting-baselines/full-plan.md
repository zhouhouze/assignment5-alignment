# O1 Prompting Baselines - Full Plan

Status: Full Attempt 2 completed, integrity validated, and human review integrated; ready for O1 closeout after commit/push.

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

<!-- full-v2-review-gate-plan -->

## Full Attempt 2 Review Gate

Observed:

- Commit: `a75ef3db48e3bbf293def0441f0229f6d1371254`
- Output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2`
- Exit code: `0`
- Prompt outputs: `3 x 1319 = 3957` prediction rows.
- Integrity validation: passed with `0` failures and `1` warning.
- Warning: tokenizer was not recorded as a separate manifest field; `model_id` is recorded and vLLM used the model tokenizer implicitly.

Pending:

- Manual semantic review of Category 2 and Category 3 review packets: completed from user-provided ChatGPT review summary.
- Full notes commit/push: pending in this closeout step.
- Do not enter GRPO until O1 closeout commit/push succeeds and the user approves moving on.

Output files:

- Full output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2`
- Log: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/logs/o1-prompting-full-v2-20260716-153611.log`
- Integrity report: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_integrity_report.json`
- Metrics: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_metrics.json`
- Cross-prompt summary: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_cross_prompt_summary.json`
- Finish reason analysis: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_finish_reason_analysis.json`
- Empty response analysis: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_empty_response_analysis.json`
- Category 2 review packet: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_category2_review_packet.md` and `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_category2_review_packet.jsonl`
- Category 3 review packet: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_category3_review_packet.md` and `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_category3_review_packet.jsonl`
- Behavior examples: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_behavior_examples.md`
- Review selection manifest: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2/full_review_selection_manifest.json`
