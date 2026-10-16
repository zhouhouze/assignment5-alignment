# PM-04 design archive

Documentation-only SFT Hypothesis & Evaluation Plan v1, based on immutable Base Full and Round01 user human adjudications. No experiment run, no P2 data admission/filter/derived training data, no new diagnostic examples/ID list, no model load, GPU, Judge, SFT or DPO.

- [Main plan](../../../../notes/experiments/SUP-QWEN-evaluation/sft-hypothesis-evaluation-plan-v1.md) contains the ten requested sections, five hypothesis registers, Evaluation/Control and PM Decision matrices, human/statistics design and P2 handoff.
- `source-inventory.json` pins all twelve required sources plus machine metric/supporting evidence to source commit919e75b. They must remain byte-identical; current status comes from Full/human artifacts, not P0 historical status text.
- `verify_document.py` runs CPU stdlib document/source/fact/link/scope checks. It does not import model libraries or rescore outputs. `consistency-check.json` is only document audit evidence, not new model results or SFT-derived data.
- Hypothesis support/refutation rules are proposals for PM review; metric definitions, paired bootstrap and 2x2 identities refer to frozen v1. No product margin, sample budget, new rubric or deployment acceptance is silently approved.
- Initial archive uses PM04_DESIGN_COMPLETE=NO until successful push/remote verification. Later `archive-acceptance.json` records that first archive proof and allows design status YES; PM review remains PENDING and P2 execution NOT AUTHORIZED. Exact final commit is resolved from Git history/final sync receipt, avoiding self-reference.
- `SHA256SUMS` covers authored evidence and the plan with repository-relative paths; excludes itself. Roll back only the PM04 doc/archive commits with git revert, preserving experiment history.

Next task: stop after archive acceptance; user reviews hypotheses/decision rules/open decisions before any next Gate. This directory grants no experiment execution authorization.
