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
