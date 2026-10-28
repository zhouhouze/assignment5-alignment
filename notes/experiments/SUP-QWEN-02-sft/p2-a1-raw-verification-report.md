# P2-A.1 Execution Report

Date: 2026-10-28 (Asia/Shanghai). **P2-A.1 = PASS**. Raw verification only; complete Data Admission=PENDING.

## Goal

Execute the user-authorized P2-A.1 CPU verification on learning/pa5-supplement. No filtering, derived-v1, human review, training, generation or GPU operations.

## Relevant Official Sources

2026 personal Supplement track. [Frozen Policy v1](../SUP-QWEN-data-flywheel/sft-data-quality-plan.md), [historical acceptance](data-acceptance.md), [archive policy](../archive-policy.md). SHA references come from Policy v1; bytes/physical rows/unique anomaly expectations come from acceptance-v2. Third-party mirror revision ac710ef808346bf458d7b093bfe4586cb15699d9; directly_comparable_to_official=false.

## Concept and Formula

Read-only Raw → pinned identity → schema → four field reasons → anomaly provenance → report. Physical rows = nonempty rows + unique anomaly rows. Reasons are exclusive within each field, not across fields. Two erroneous fields still identify one row. No training records are written.

## Tensor Shapes

Not applicable: JSON objects, strings, counters and file digests; no tensors.

## Planned Change / Changes Made

Added scripts/validate_qwen_sft_raw.py and tests/test_qwen_sft_raw.py. Old preflight/adapters/tests remain byte-identical to the pre-task commit (checked during archival). New validator checks SHA before parsing, hashes scanned bytes and rehashes the path after scanning. Requires new output directory outside Raw, including resolved symlink paths; writes outputs exclusively. Schema errors stop processing and save FAIL/error plus completed-file evidence. Reason labels distinguish empty from whitespace-only under Python strip semantics, without modifying strings.

## Risks and Edge Cases

Synthetic tests cover both fields, empty/ASCII/Unicode whitespace, dual anomalies, nonempty padding preservation and zero-width non-whitespace, malformed/blank/nonobject/missing/nonstring/invalid-UTF8/nonstandard-JSON input, SHA-before-schema, bytes/row/anomaly mismatch, no-final-newline counting, output reuse and Raw symlink destination. Raw must remain quiescent; SHA checks detect content changes, not malicious concurrent filesystem races. No claim of semantic quality or contamination clearance.

## Tests Run

Interpreter: /Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python (3.12.13). Working directory: /Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement.

- `python -m pytest tests/test_qwen_sft_raw.py -q`: **23 PASS**, 0.02s.
- `python -m pytest tests/test_qwen_preflight.py -q`: **10 PASS**, 0.43s; original assertions unchanged.
- `python -m pytest tests/test_grpo.py -q`: **19 FAIL**, 0.13s, all pre-existing NotImplementedError in unchanged adapters. These are not passing tests or new validator regressions. No repair in this Gate.

Tests ran before code commit against 9c57bed8b8775c1427cb9d78abb12c61ba27e0c6 plus the new files; exact source hashes and raw logs are in [test evidence](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2a1-tests). Those fingerprints were rechecked against the committed source before archival. No snapshots changed.

## Actual CPU Execution

`python scripts/validate_qwen_sft_raw.py --output artifacts/pa5-supplement-qwen/sft/20261028-p2a1-raw`

Execution code commit: `c66bebc87666b5c1d3658b72cdd13ae30cbd9acf`. Exact executable, argv, timestamps, Python/platform, git status, policy/source SHA and trusted references are in raw-verification.json. Untracked test/run evidence during execution is disclosed in git_status; source was committed.

## Result

SHA/bytes/physical row checks, schema and Raw unchanged checks: **PASS** for all three files.

| Split | Bytes | Physical rows | empty_prompt | whitespace_only_prompt | empty_response | whitespace_only_response | Unique anomaly rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 532421064 | 210348 | 1 | 0 | 21 | 0 | 22 |
| validation | 58872258 | 23110 | 0 | 0 | 2 | 0 | 2 |
| sample_train | 2492043 | 1000 | 0 | 0 | 0 | 0 | 0 |

- train: `3b72228a7976079a5c5a30249fd3289179ad01006cbb67d15c7c366d4fd25913`
- validation: `ce84dd834a7bbfc622cb3b50dc6c233e7dd91e002fd84f7cf86f70762a2c9ed9`
- sample_train: `b26bbe382793889ccb397e7c8afdf64ad3e52f0109d191e66c424587fba596df`

Total 234,458 rows; 24 anomalous rows, all strict empty strings. Nonempty rows train=210326, validation=23108, sample_train=1000 are measured counts, not generated Derived counts. No schema failure or unexplained count difference occurred.

## Raw Artifact Paths / Reproducibility

Raw remains data/qwen-sft-mirror/sft-instruct/{train,test,sample_train}.jsonl, excluded from Git. Restore via the existing pinned restore procedure in data-acceptance.md, then rerun this committed tool into a fresh directory. An existing output is refused.

[Run evidence](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2a1-raw): raw-verification.json contains all 24 source-row IDs, split, source SHA, physical line and reasons; execution.log records per-file progress. independent-sha256.txt and independent-wc.txt were produced with `shasum -a 256` and `wc -lc` over train/test/sample_train in that order. Independent comparison verified these outputs against the run and historical SHA, all historical anomaly rows/reasons, unique IDs and row conservation; result in independent-check.json. This is not a second independent four-way classifier or a new overlap audit.

## Explanation for the Learner / Product Interpretation

The old scanner merged two categories; the new scan shows that all 24 known rows are strict empty strings. The four-way distinction still matters for future diagnostics. Passing this component establishes source identity and structural evidence, not fitness for training or answer quality. A dual-field example yields two reasons and one anomaly row; its source identity must remain stable for later mapping.

## Learning Check / Remaining Gaps

Learner explanation status=PENDING. Suggested check: explain why reason counts can exceed anomaly rows, why nonempty whitespace must be preserved, and what Raw PASS does not establish about training quality.

P2-A.2 derivation, exclusions as applied filtering, full source-row mapping, Derived SHA, new train/validation exact isolation audit, contamination review and complete Data Admission remain **PENDING / NOT EXECUTED**. No new authorization inferred. No execution failure in this run; the 19 legacy GRPO test failures are preserved separately.

## Next Gate

Stop after small-evidence Git archival and remote verification. No automatic P2-A.2. Archive commit is identified by Git history rather than self-referential SHA.
