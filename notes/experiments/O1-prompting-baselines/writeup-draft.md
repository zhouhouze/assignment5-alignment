# O1 Prompting Baselines - Writeup Draft

Status: Smoke, Pilot, and Pilot audit complete; Full not run in this notes commit.

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
