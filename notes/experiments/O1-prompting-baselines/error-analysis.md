# O1 Prompting Baselines - Error Analysis

Status: Smoke-only observations. Pilot/Full error analysis has not been run.

## Manual Review Requirements

- Review at least 10 Category 2 examples if available.
- Review at least 10 Category 3 examples if available.
- Count outputs that are actually correct but not parsed properly.
- Save representative prompts/responses.

## Categories

- Category 1: formatted and correct.
- Category 2: formatted but incorrect.
- Category 3: unformatted and incorrect.
- Unexpected: unformatted but answer-correct; record separately if observed.

## Notes

Do not fill parser false-negative counts before Pilot or Full generation outputs exist.

## Smoke Samples Observed

All smoke samples used the first GSM8K test example. The extracted ground truth was `18`.

### `question_only`

- Category: 2.
- Finish reason: `length`.
- Observed behavior: the response contained boxed fragments but did not produce the correct final answer before hitting `max_tokens=512`.
- Interpretation: validates that the prompt path and grader run, but does not establish the prompt's real failure rate.

### `r1_zero`

- Category: 2.
- Finish reason: `stop`.
- Observed behavior: the output retained `</answer>` and was formatted, but the answer content was not correct.
- Interpretation: validates stop-string retention and the `r1_zero_reward_fn` path for a formatted incorrect response.

### `r1_zero_three_shot_gsm8k`

- Category: 2.
- Finish reason: `stop`.
- Observed behavior: the output retained `</answer>` and was formatted, but answered `$120` instead of `18`.
- Interpretation: validates few-shot prompt rendering and stop-string retention, not model quality.

## Not Yet Done

- No 20-50 example Pilot run.
- No Full GSM8K run.
- No manual Category 2/3 false-negative audit beyond the three smoke outputs.
