# O1 Prompting Baselines - Experiment Card

Status: Smoke complete. Awaiting approval before Pilot.

## Official Problem

- Problem ID: `prompting_baselines`
- Points: 5
- Goal: evaluate OLMo-2-0425-1B on GSM8K with three prompt formats.

## Prompt Conditions

- `question_only`: zero-shot question plus boxed-answer instruction.
- `r1_zero`: zero-shot reasoning-format prompt with `<think>` and `<answer>` tags.
- `r1_zero_three_shot`: few-shot reasoning-format prompt with three GSM8K examples.

## Official Generation Configuration

- `temperature = 1.0`
- `top_p = 1.0`
- `max_tokens = 512`
- Use `stop = ["</answer>"]` and `include_stop_str_in_output = True` only for `r1_zero` and `r1_zero_three_shot`.
- Do not use `</answer>` stop for `question_only`.

## Required Categories

- Category 1: `format_reward=1` and `answer_reward=1`
- Category 2: `format_reward=1` and `answer_reward=0`
- Category 3: `format_reward=0` and `answer_reward=0`
- Unexpected: `format_reward=0` and `answer_reward=1`; record separately if observed.

## Required Saved Fields

- `example_id`
- `question`
- `ground_truth`
- `prompt_name`
- `formatted_prompt`
- `response`
- `finish_reason`
- `reward`
- `format_reward`
- `answer_reward`
- `category`
- `response_token_count`
- `latency` if available

## Run Levels

- Smoke: one shared example per prompt. Completed on 2026-07-16.
- Pilot: 20-50 shared examples per prompt.
- Full: complete official evaluation only after pilot approval.

## Smoke Run

- Output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-114549/smoke`
- Log: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/logs/o1-prompting-smoke-20260716-114549-disable-xet.log`
- Model: `allenai/OLMo-2-0425-1B`
- Dataset: `data/gsm8k/test.jsonl`
- Shared example: first GSM8K test example.
- Ground truth: `18`
- Seed: `0`
- Batch size: `1`
- GPU memory utilization: `0.75`
- Generation settings: `temperature=1.0`, `top_p=1.0`, `max_tokens=512`

## Smoke Results

| Prompt | Finish reason | Tokens | Format reward | Answer reward | Category |
| --- | --- | ---: | ---: | ---: | --- |
| `question_only` | `length` | 512 | 1.0 | 0.0 | Category 2 |
| `r1_zero` | `stop` | 83 | 1.0 | 0.0 | Category 2 |
| `r1_zero_three_shot_gsm8k` | `stop` | 72 | 1.0 | 0.0 | Category 2 |

## Smoke Validation

- The model loaded through vLLM on RTX 5090.
- `question_only` used no `</answer>` stop string.
- `r1_zero` and `r1_zero_three_shot_gsm8k` used `stop=["</answer>"]` with `include_stop_str_in_output=True`.
- `top_p=1.0` is now passed into the vLLM completion payload.
- JSONL outputs were re-read successfully.
- All three responses were non-empty.
- All three responses were formatted according to their reward function but answer-incorrect for this one example.
- This is only a smoke result and is not evidence for prompt-level accuracy.
