# O1 Prompting Baselines - Writeup Draft

Status: Full metrics and required sampled human review complete; O1 writeup draft ready for final editing.

## Problem

Evaluate OLMo-2-0425-1B on GSM8K using:

- `question_only`
- `r1_zero`
- `r1_zero_three_shot`

## Metrics To Report

- Total examples
- Category 1 count
- Category 2 count
- Category 3 count
- Answer accuracy
- Format rate
- Average response length
- Generation runtime
- Throughput if available

## Learner Predictions

Pending. Record the learner's original predictions before smoke/pilot/full generation.

## Results

Smoke-only result on the first GSM8K test example:

| Prompt | Category | Answer reward | Format reward | Notes |
| --- | --- | ---: | ---: | --- |
| `question_only` | Category 2 | 0.0 | 1.0 | Hit `max_tokens=512`; no `</answer>` stop was used. |
| `r1_zero` | Category 2 | 0.0 | 1.0 | Stopped on `</answer>` and retained the stop string. |
| `r1_zero_three_shot_gsm8k` | Category 2 | 0.0 | 1.0 | Stopped on `</answer>` and retained the stop string. |

Smoke output path:

```text
/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-114549/smoke
```

## Commentary

The smoke run verifies plumbing: model load, prompt rendering, stop configuration, `top_p`, ground-truth extraction, grader routing, JSONL readback, and GPU memory behavior. It does not support any conclusion about full GSM8K accuracy or prompt ranking.

Pilot review gate is complete. Full GSM8K can be run only after explicit approval using the fixed Pilot configuration.


## Pilot Results

Pilot output path:

```text
/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot
```

| Prompt | Cat1 | Cat2 | Cat3 | Accuracy | Format rate | Avg tokens | Length terminations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `question_only` | 0 | 9 | 11 | 0.0% | 45.0% | 323.6 | 8 |
| `r1_zero` | 0 | 13 | 7 | 0.0% | 65.0% | 123.6 | 1 |
| `r1_zero_three_shot_gsm8k` | 0 | 19 | 1 | 0.0% | 95.0% | 104.0 | 0 |

Observed:

- The Pilot generated 60 non-empty responses over the same 20 GSM8K test examples for all prompts.
- No correct final answers were observed by the official reward functions.
- `question_only` had substantial truncation and drift.
- `r1_zero_three_shot_gsm8k` had the best format rate and no length termination.

Interpretation:

- This Pilot is evidence that the pipeline works, not evidence that a Full run is ready.
- A larger run may simply amplify the same failure modes unless the prompt/grader/model suitability is reviewed first.

## Pilot Audit Clarification

The Pilot audit separates three cases that should not be conflated:

- `strict_parser_bug`: formatted correct final answer, but parser/grader fails. Pilot count: 0.
- `human_correct_but_unscorable`: human-visible final answer is correct but the output violates the required format. Pilot example: `question_only` id 19.
- `correct_intermediate_missing_or_wrong_final`: correct value appears in reasoning, but the final answer is empty, unclosed, or wrong. Pilot example: `r1_zero_three_shot_gsm8k` id 1.

This means the Pilot did not reveal a systematic parser bug, but it did reveal format and final-answer failures that can make human-visible partial success unscorable.

<!-- full-v2-review-gate-writeup -->

## Full Attempt 2 Results Draft

Full output path:

```text
/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-153611/full-v2
```

| Prompt | N | Cat1 | Cat2 | Cat3 | Unexpected | Official accuracy | Format rate | Avg tok | Median tok | P95 tok | Empty | Length | Runtime | Throughput |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `question_only` | 1319 | 1 | 222 | 1096 | 0 | 0.08% | 16.91% | 259.4 | 229 | 512.0 | 30 | 454 | 398.6s | 3.31/s |
| `r1_zero` | 1319 | 1 | 839 | 479 | 0 | 0.08% | 63.68% | 94.8 | 74 | 218.1 | 0 | 11 | 164.8s | 8.00/s |
| `r1_zero_three_shot_gsm8k` | 1319 | 235 | 1020 | 64 | 0 | 17.82% | 95.15% | 110.1 | 97 | 202.1 | 0 | 3 | 169.3s | 7.79/s |

Observed:

- Full Attempt 2 completed with exit code `0`.
- The official grader awarded Category 1 to `1/1319` question-only outputs, `1/1319` R1 zero outputs, and `235/1319` three-shot R1 outputs.
- Three-shot R1 had the highest observed format rate: `95.15%`.
- `question_only` had substantially more empty and length-terminated outputs than the two R1 prompts.

Inference:

- The R1 prompt structure appears to improve format and termination behavior in this run.
- The three-shot prompt appears stronger under official grader metrics, but final writeup claims need human review of Category 2/3 examples.

Pending:

- Human-adjusted accuracy is not computed.
- Final O1 conclusion and GRPO handoff are not approved yet.

<!-- full-human-review-writeup-closeout -->

## Assignment Requirement Coverage

Completed:

- Ran all three prompting baselines on the full GSM8K test set of `1319` examples.
- Preserved fixed model, dataset, seed, temperature, top-p, max-token limit, and prompt definitions.
- Reported Category 1, Category 2, and Category 3 counts for each prompt.
- Reported official accuracy and format rate for each prompt.
- Reported length, empty-output, and stop-behavior differences.
- Manually reviewed `12` Category 2 examples and `12` Category 3 examples.
- Checked whether sampled failures were parser bugs or human-correct-but-unscorable outputs.
- Recorded representative failure cases, including `category_3-09` and `category_3-10`.

Final official metrics:

| Prompt | Cat1 | Cat2 | Cat3 | Official accuracy | Format rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `question_only` | 1 | 222 | 1096 | 0.08% | 16.91% |
| `r1_zero` | 1 | 839 | 479 | 0.08% | 63.68% |
| `r1_zero_three_shot_gsm8k` | 235 | 1020 | 64 | 17.82% | 95.15% |

Human review conclusion:

- Category 2 sampled review found `0/12` actual-correct-but-unscored cases.
- Category 3 sampled review found `1/12` actual-correct-but-unscored case.
- Strict parser bug count was `0/24`.
- Official accuracy remains unchanged; no human-adjusted accuracy is computed.

Draft interpretation:

- `question_only` performs poorly as an interface to this base model: low format rate, high truncation, and many unparseable or empty outputs.
- `r1_zero` improves delivery format and stopping behavior without materially improving official answer accuracy.
- `r1_zero_three_shot_gsm8k` improves both format adherence and official answer accuracy under the fixed Full configuration.
- These claims are scoped to the tested model, dataset, prompts, and sampling parameters.
