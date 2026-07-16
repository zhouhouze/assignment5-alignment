# Learning Log

## 2026-07-15 - Repository Orientation

Component: GRPO repository map and learning sequence.

Concept learned:

- The repository is the CS336 Spring 2026 Assignment 5 fork, not the 2025 version.
- The 2026 assignment centers on reasoning RL for OLMo-2-0425-1B on GSM8K.
- Compared with 2025, the 2026 version adds MaxRL and GSPO and shifts the main task from MATH/Qwen to GSM8K/OLMo.
- The core implementation surface is the `run_*` adapter API in `tests/adapters.py`.

Files changed:

- Added `notes/repository-map.md`.
- Added `notes/learning-log.md`.
- Added `notes/concept-map.md`.

Tests run:

```sh
uv run pytest -q tests/test_grpo.py
```

Result:

- 19 failed.
- All failures are expected baseline failures from `NotImplementedError` in `tests/adapters.py`.

Bugs encountered:

- No implementation bugs investigated yet.
- Environment note: first `uv run` created `.venv` and downloaded dependencies before running tests.

Final implementation decision:

- No core functions implemented in this orientation round.
- Do not modify tests, snapshots, handout PDFs, or official source files.

Remaining questions:

- Where should the eventual student implementation live: directly in `tests/adapters.py`, or should adapters call a new module under `cs336_alignment/`?
- Should the eventual GRPO experiment script be named `scripts/grpo.py` to match `modal_utils.py`?
- Which metric logging schema should be used for later experiments under `notes/experiments/`?

Learner explanation status:

- Not checked yet. First checkpoint should focus on group-normalized rewards before code changes.

## 2026-07-15 - Progress Switch to O1 Prompting Baselines

Component: `prompting_baselines` experiment preparation.

Concept learned:

- Progress switched away from `compute_group_normalized_rewards_grpo` before implementation.
- `compute_group_normalized_rewards_grpo` is paused until after `prompting_baselines` and `baseline_calcs`.
- Local macOS arm64 environment has no CUDA and no local vLLM installation, so full OLMo/GSM8K generation should not be run locally.
- GSM8K train/test files exist and contain `question` and `answer`; ground truth answer is extracted after `####`.

Files changed:

- Updated `notes/assignment-requirements.md`.
- Added `notes/experiments/O1-prompting-baselines/experiment-card.md`.
- Added `notes/experiments/O1-prompting-baselines/environment-check.md`.
- Added `notes/experiments/O1-prompting-baselines/error-analysis.md`.
- Added `notes/experiments/O1-prompting-baselines/writeup-draft.md`.

Tests run:

- None. This was experiment preparation only.

Bugs encountered:

- No code bugs investigated.
- Environment blocker: no CUDA GPU and no local vLLM binary.
- Modal blocker: `SUNET_ID` is still `TODO` in `cs336_alignment/modal_utils.py`.

Final implementation decision:

- No GRPO adapter TODO implemented.
- No prompting evaluation script implemented before learner predictions.

Remaining questions:

- Confirm OLMo-2-0425-1B model source/path for the intended GPU environment.
- Decide whether smoke/pilot will run on local Linux GPU, cloud GPU, or Modal.
- Learner predictions pending for prompt accuracy, format rate, question-only failure modes, and parser false negatives.

Learner explanation status:

- Pending.


## 2026-07-16 - O1 Full Reliability Patch

Component: `prompting_baselines` Full evaluation reliability.

Concept learned:

- A model can legally return an empty completion; that should be scored by the official grader rather than treated as an infrastructure failure.
- Evaluation scripts should persist results incrementally so a later failure does not erase already completed batches.
- True hard failures are missing completions, output-count mismatches, generation exceptions, CUDA OOM, and JSONL write/read failures.

Files changed:

- Updated `scripts/prompting_baselines.py` to append `predictions.partial.jsonl` after each batch, update `progress.json`, and atomically rename to `predictions.jsonl` only after prompt completion.
- Added `tests/test_prompting_baselines_reliability.py`.
- Updated Full Attempt 1 notes to preserve the failure evidence.

Tests run:

```sh
uv run python -m py_compile scripts/prompting_baselines.py tests/test_prompting_baselines_reliability.py
uv run pytest -q tests/test_prompting_baselines_reliability.py
git diff --check
```

Result:

- Reliability mock tests passed.
- Empty completions are persisted and graded.
- Short output batches and missing completions hard-fail while preserving partial progress.

Bugs encountered:

- Attempt 1 failed on `question_only` example 55 because the old script raised on `completion.text == ""`.

Final implementation decision:

- Do not retry or skip empty completions.
- Keep model, prompt, grader, and generation parameters unchanged.
- Rerun Full from a fresh output directory only after committing and syncing the reliability patch.

Learner explanation status:

- Pending.

## 2026-07-16 - O1 Prompting Baselines Smoke

Component: `prompting_baselines` smoke test on AutoDL RTX 5090.

Concept learned:

- A smoke test should validate the experiment pipeline before making claims about model quality.
- `uv sync --no-install-package flash-attn` and later O1 setup can still require network access to direct wheel/model metadata.
- vLLM can load `allenai/OLMo-2-0425-1B` on one RTX 5090 with conservative `gpu_memory_utilization=0.75`.
- Hugging Face Xet downloads can stall; setting `HF_HUB_DISABLE_XET=1` avoided the stalled OLMo weight download path without changing model or generation settings.
- `top_p` must be explicitly passed into vLLM request construction; it was missing from `cs336_alignment/vllm_utils.py`.

Files changed:

- Updated `cs336_alignment/vllm_utils.py` to pass `top_p`.
- Added `scripts/prompting_baselines.py` for O1 smoke/pilot/full scaffolding.
- Updated O1 experiment notes with smoke-only results.

Tests run:

```sh
uv run python -m py_compile scripts/prompting_baselines.py cs336_alignment/vllm_utils.py
```

```sh
uv run python scripts/prompting_baselines.py --mode smoke --prompt-name all --model-id allenai/OLMo-2-0425-1B --dataset-path data/gsm8k/test.jsonl --seed 0 --batch-size 1 --output-dir /root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-114549/smoke --gpu-memory-utilization 0.75
```

Result:

- Smoke completed with exit code 0.
- Three JSONL outputs were re-read successfully.
- All three prompts produced non-empty responses.
- All three smoke responses were Category 2 on the first GSM8K test example.

Bugs encountered:

- `top_p` was not forwarded by `cs336_alignment/vllm_utils.py`.
- First OLMo load stalled through Hugging Face Xet; restarted with `HF_HUB_DISABLE_XET=1`.

Final implementation decision:

- Keep changes minimal and limited to O1 prompting smoke support.
- Do not run Pilot, Full, or GRPO without approval.

Remaining questions:

- Whether to commit the O1 smoke script and `top_p` fix before Pilot.
- What Pilot limit to use: 20, 30, or 50 examples.

Learner explanation status:

- Pending; discuss smoke observations before Pilot.


## 2026-07-16 - O1 Prompting Baselines Pilot

Component: `prompting_baselines` 20-example Pilot on AutoDL RTX 5090.

Concept learned:

- A Pilot can pass pipeline validation while still failing the experiment-readiness gate.
- `question_only` can generate long, drifting continuations and hit `max_tokens=512` frequently.
- R1-style prompts improved format adherence in this Pilot, especially the three-shot prompt, but did not improve answer accuracy on the first 20 GSM8K test examples.
- `uv run --no-sync` avoided an unnecessary metadata re-resolution path during experiment launch after the environment was already synchronized.

Files changed:

- Added `notes/experiments/O1-prompting-baselines/pilot-plan.md`.
- Added `notes/experiments/O1-prompting-baselines/pilot-results.md`.
- Added `notes/experiments/O1-prompting-baselines/pilot-audit.md`.
- Updated O1 error-analysis and writeup notes with Pilot observations.

Tests run:

```sh
uv run --no-sync python scripts/prompting_baselines.py --mode pilot --prompt-name all --model-id allenai/OLMo-2-0425-1B --dataset-path data/gsm8k/test.jsonl --limit 20 --seed 0 --batch-size 4 --output-dir /root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot --gpu-memory-utilization 0.75
```

Result:

- Pilot completed with exit code 0.
- 60 rows were generated and validated.
- No residual vLLM process remained after completion.
- `pyproject.toml` and `uv.lock` were unchanged.

Bugs encountered:

- Not a code bug, but a validation finding: several R1 outputs did not retain `</answer>` despite the recorded stop config requesting it.

Final implementation decision:

- Stop at the Pilot gate until explicit Full approval.
- Do not run GRPO without a separate review and approval.

Remaining questions:

- After Pilot audit, should the approved Full run keep the same fixed configuration?
- Should the baseline remain at `temperature=1.0`, or should deterministic decoding be considered as a separate controlled experiment?
- Are these prompts intended for a base model without instruction tuning, or should prompt wording be revisited before Full?

Learner explanation status:

- Pending.
