# O1 Prompting Baselines - Writeup Draft

Status: Smoke complete; Pilot and Full not run.

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

Next step, after approval, is a small Pilot run over 20-50 shared GSM8K examples.
