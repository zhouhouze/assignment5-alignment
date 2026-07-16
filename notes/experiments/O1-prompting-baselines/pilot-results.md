# O1 Prompting Baselines - Pilot Results

Status: Pilot complete. Full GSM8K and GRPO were not run.

## Run

- Output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot`
- Log: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/logs/o1-prompting-pilot-20260716-142558.log`
- Metrics sidecar: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot/pilot_metrics.json`
- Review sidecar: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot/pilot_review_samples.json`
- Commit: `4af419ed9694301fa4a82b86de6c0e55b585e271`
- Model: `allenai/OLMo-2-0425-1B`
- Examples: GSM8K test ids `0-19`
- Prompts: `question_only`, `r1_zero`, `r1_zero_three_shot_gsm8k`
- Batch size: `4`
- GPU memory utilization: `0.75`
- Start time: `2026-07-16T14:25:58+08:00`
- Last output file time: `2026-07-16 14:27:30 CST`

## Metrics

| Prompt | Total | Cat1 | Cat2 | Cat3 | Unexpected | Accuracy | Format rate | Avg tok | Median tok | Max tok | Finish reasons | Length count | Avg latency s | Runtime s | Throughput ex/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| `question_only` | 20 | 0 | 9 | 11 | 0 | 0.0% | 45.0% | 323.6 | 385.0 | 512 | {'length': 8, 'stop': 12} | 8 (40.0%) | 1.4299 | 7.304 | 2.738 |
| `r1_zero` | 20 | 0 | 13 | 7 | 0 | 0.0% | 65.0% | 123.6 | 84.0 | 512 | {'stop': 19, 'length': 1} | 1 (5.0%) | 0.6164 | 3.295 | 6.070 |
| `r1_zero_three_shot_gsm8k` | 20 | 0 | 19 | 1 | 0 | 0.0% | 95.0% | 104 | 99.0 | 255 | {'stop': 20} | 0 (0.0%) | 0.3812 | 2.087 | 9.584 |

## Validation

- JSONL readback: passed for all three prompt outputs.
- Row counts: 20 rows per prompt, 60 rows total.
- Example IDs: all prompts used ids `0-19`.
- Responses: all non-empty.
- Generation parameters: `temperature=1.0`, `top_p=1.0`, `max_tokens=512`, `seed=0` recorded for every row.
- Stop configuration: recorded as expected in `generation_parameters`.
- Official reward/category consistency: recomputing with `question_only_reward_fn` and `r1_zero_reward_fn` matched stored categories.
- Validation checks passed: 22/24.

Problems observed:

- r1_zero answer closing tag included: missing </answer> in at least one response
- r1_zero_three_shot_gsm8k answer closing tag included: missing </answer> in at least one response

## Observed Facts

- No prompt achieved a correct answer in this 20-example Pilot.
- `question_only` had 8 length-terminated responses and the highest average response length.
- `r1_zero` had 1 length-terminated response.
- `r1_zero_three_shot_gsm8k` had no length-terminated responses and the highest format rate.
- Some R1 responses did not include `</answer>` even though the stop config requested `include_stop_str_in_output=True`.
- `question_only` often drifted into unrelated prompt-like continuations or empty `\boxed{}` answers.

## Inferences

- The Pilot pipeline is operational for generation, persistence, readback, and grading.
- The three-shot R1 prompt controlled output format better than the other prompts on this sample.
- `question_only` is risky for token cost and truncation under `max_tokens=512`.
- The observed accuracy is too low to justify a Full run without first reviewing whether the prompt/grader pair is suitable for this base model.

## Unverified Hypotheses

- The 1B base model may be too weak or insufficiently instruction-following for these prompt formats at `temperature=1.0`.
- Some R1 missing-close cases may be caused by model emitting malformed tags or early EOS behavior rather than vLLM stop handling.
- Lower temperature or stronger answer-only extraction might change measured accuracy, but that would be a new experiment and was not run here.

## Preliminary Parser Review

Category 2 samples:

- `question_only` id 0: gt `18`, grader candidate `(15* ?)+\\cdot\\cdot\\cdot`, finish `length`, tokens 512, boxed_count 5. Inference: appears incorrect from final extracted answer.
- `question_only` id 1: gt `3`, grader candidate ``, finish `stop`, tokens 223, boxed_count 2. Inference: appears incorrect from final extracted answer; ground-truth numeral appears somewhere in response but not as a clearly parsed final answer.
- `question_only` id 2: gt `70000`, grader candidate ``, finish `stop`, tokens 274, boxed_count 5. Inference: appears incorrect from final extracted answer.
- `question_only` id 6: gt `260`, grader candidate ``, finish `stop`, tokens 473, boxed_count 2. Inference: appears incorrect from final extracted answer.
- `question_only` id 7: gt `160`, grader candidate ``, finish `length`, tokens 512, boxed_count 1. Inference: appears incorrect from final extracted answer.

Category 3 samples:

- `question_only` id 3: gt `540`, grader candidate `None`, finish `stop`, tokens 10, boxed_count 0. Inference: appears incorrect from final extracted answer.
- `question_only` id 4: gt `20`, grader candidate `None`, finish `stop`, tokens 97, boxed_count 0. Inference: appears incorrect from final extracted answer; ground-truth numeral appears somewhere in response but not as a clearly parsed final answer.
- `question_only` id 5: gt `64`, grader candidate `None`, finish `length`, tokens 512, boxed_count 0. Inference: appears incorrect from final extracted answer.
- `question_only` id 8: gt `45`, grader candidate `None`, finish `stop`, tokens 435, boxed_count 0. Inference: appears incorrect from final extracted answer.
- `question_only` id 9: gt `460`, grader candidate `None`, finish `stop`, tokens 335, boxed_count 0. Inference: appears incorrect from final extracted answer.

Strict parser bug and unscorable-answer check:

- Observed: no `strict_parser_bug` was found in the sampled Category 2/3 examples.
- Observed: the later full Pilot audit identified `question_only` id 19 as `human_correct_but_unscorable`, not a parser bug.
- Observed: the later full Pilot audit identified `r1_zero_three_shot_gsm8k` id 1 as `correct_intermediate_missing_or_wrong_final`, not a correct final answer.
- Caveat: the sampled review was superseded by `pilot-audit.md` for the final Pilot audit taxonomy.

## Recommendation

Stop at the Pilot gate. Do not run Full yet. Review prompt suitability, R1 tag failures, and whether `temperature=1.0` is appropriate for a measurement baseline before approving a larger run.
