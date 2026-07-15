# O1 Prompting Baselines - Experiment Card

Status: Preparation, awaiting learner predictions.

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

- Smoke: one shared example per prompt.
- Pilot: 20-50 shared examples per prompt.
- Full: complete official evaluation only after pilot approval.

## Current Blocker

Local machine is macOS arm64 with no CUDA and no vLLM binary. Full generation should use a Linux CUDA GPU environment or Modal after setup.
