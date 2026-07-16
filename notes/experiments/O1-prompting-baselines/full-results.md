# O1 Prompting Baselines - Full Results

Status: Full Attempt 2 complete; human review integrated; ready for O1 closeout after commit/push.

## Attempt 1

- Commit: `858f64562a31cf318b2f3ad9833ac146dc90d0e7`
- Output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-150640/full`
- Log path: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/logs/o1-prompting-full-20260716-150640.log`
- Manifest: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-150640/full/full_manifest.json`
- Exit code: `1`
- Stop condition: `empty_response`

## Failure

Observed:

- The run entered vLLM generation for `question_only`.
- The script raised `RuntimeError: Empty response for prompt question_only, example 55`.
- The run exited with code `1`.
- No `predictions.jsonl` or `summary.json` files were written before the failure because the script writes per-prompt outputs after completing that prompt.
- GPU returned idle after vLLM shutdown.

Inference:

- This is a failed evaluation attempt, not a completed Full result.
- The current Full cannot be used for official accuracy, format, length, or error-analysis metrics.
- Existing logs do not record the completion object's `finish_reason`, token ids, or full request-output metadata for example 55, so Attempt 1 cannot distinguish `valid_empty_completion` from a deeper generation anomaly by evidence alone.
- The old script treated `completion.text == ""` as a hard failure before persisting partial records.

## Reliability Patch Decision

For the next run, a successful vLLM request with an existing completion object and `completion.text == ""` should be recorded as a legitimate model output:

- Do not retry.
- Do not skip the sample.
- Pass the empty string into the official grader.
- Record `empty_response=true`, `generation_status="completed_empty"`, and `error_type="empty_response"`.
- Continue to subsequent examples.

True system failures remain hard stops: generation exceptions, missing completion objects, output count mismatches, CUDA OOM, and JSONL write/read failures.

Attempt 1 is preserved as failure evidence and must not be included in official Full metrics.

<!-- full-v2-review-gate-results -->

## Attempt 2 - Full Results Review Gate

Observed:

- Commit: `a75ef3db48e3bbf293def0441f0229f6d1371254`
- Exit code: `0`
- GPU returned idle and no inference process remained after completion.
- Data disk remained above the stop threshold: `/root/autodl-tmp` had about `68G` free during review.
- Each prompt produced exactly `1319` predictions with ids `0-1318`.
- Integrity report passed: `0` failures, `1` warning.

| Prompt | N | Cat1 | Cat2 | Cat3 | Unexpected | Official accuracy | Format rate | Avg tok | Median tok | P95 tok | Empty | Length | Runtime | Throughput |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `question_only` | 1319 | 1 | 222 | 1096 | 0 | 0.08% | 16.91% | 259.4 | 229 | 512.0 | 30 | 454 | 398.6s | 3.31/s |
| `r1_zero` | 1319 | 1 | 839 | 479 | 0 | 0.08% | 63.68% | 94.8 | 74 | 218.1 | 0 | 11 | 164.8s | 8.00/s |
| `r1_zero_three_shot_gsm8k` | 1319 | 235 | 1020 | 64 | 0 | 17.82% | 95.15% | 110.1 | 97 | 202.1 | 0 | 3 | 169.3s | 7.79/s |

Observed behavior:

- `question_only` produced `30` empty responses and `454` length-terminated responses.
- `r1_zero` produced `0` empty responses and `11` length-terminated responses.
- `r1_zero_three_shot_gsm8k` produced `0` empty responses and `3` length-terminated responses.
- Official grader accuracy is not human-adjusted accuracy.

Inference:

- Three-shot R1 has much higher observed format rate and official grader accuracy than the other two prompts in this run.
- This should not be treated as a final causal claim until Category 2/3 human review checks parser false negatives and unscorable human-correct outputs.

Pending:

- Category 2 manual semantic review.
- Category 3 manual semantic review.
- Decision on whether O1 satisfies the assignment requirement and can be closed.

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

<!-- full-human-review-integration -->

## Human Review Integration

Source: user-provided ChatGPT human review summary for the Full Category 2 and Category 3 review packets. The completed `/mnt/data` files were not directly accessible in this Codex environment, so this note records the provided completed-review summary and key cases.

| Prompt | Cat1 | Cat2 | Cat3 | Official accuracy | Format rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `question_only` | 1 | 222 | 1096 | 0.08% | 16.91% |
| `r1_zero` | 1 | 839 | 479 | 0.08% | 63.68% |
| `r1_zero_three_shot_gsm8k` | 235 | 1020 | 64 | 17.82% | 95.15% |

Observed:

- Category 2 sampled review: `12` reviewed, `0` strict parser bugs, `0` human-correct-but-unscorable outputs, `0` correct-intermediate-missing-or-wrong-final outputs.
- Category 3 sampled review: `12` reviewed, `0` strict parser bugs, `1` human-correct-but-unscorable output, `2` correct-intermediate-missing-or-wrong-final outputs.
- Strict parser bug total: `0/24`.
- `category_3-09` is a format failure: the reasoning derives `3`, but `<answer>` is empty and unclosed. This is human-correct-but-unscorable, not a parser bug.
- `category_3-10` has correct intermediate quantities but a final arithmetic error: `555` instead of `595`.

Boundaries:

- Official accuracy remains unchanged.
- No human-adjusted accuracy is computed.
- The sampled human review proportions are not extrapolated to the full dataset.

Review records:

- `notes/experiments/O1-prompting-baselines/full-human-review.md`
- `notes/experiments/O1-prompting-baselines/full-human-review.jsonl`
