# P2-A.2 Execution Report

2026-10-28 (Asia/Shanghai). **P2-A.2 = PASS — machine derivation acceptance only. Full Data Admission = PENDING, NOT APPROVED.**

## Goal

Produce derived-v1 under the explicit P2-A.2 CPU authorization. No P2-B, human review, P3, SFT, inference or GPU operations. Branch learning/pa5-supplement.

## Relevant Official Sources

[Policy v1](../SUP-QWEN-data-flywheel/sft-data-quality-plan.md), [A.1 report](p2-a1-raw-verification-report.md), [archive policy](../archive-policy.md), branch AGENTS.md personal fork override. This is the Spring 2026 adapted Supplement route; no official equivalence claim. Policy bytes remain unchanged: `d841242f8f770c6b6e87988107885cf7402531cce193efe7f2d3295e8aed3389`. A.1 report identity verified against archive 5d91c3b: `c81445523482acc5f1894c1ceab394850b8836720c98fd1b972a3653c9f559fc`.

## Concept and Formula

Raw → freshly verified SHA/schema/A.1 anomalies → keep physical bytes unless an approved empty-field reason applies → complete mapping/exclusions → manifest → independent disk verifier. Raw rows = Derived rows + unique excluded rows. Multiple reasons belong to one source row. There is no shuffle, trim, deduplication, truncation or answer rewriting.

## Tensor Shapes

Not applicable: JSONL records, physical line numbers, byte streams and counters; no tensors/models.

## Planned Change / Changes Made

Added scripts/derive_qwen_sft.py, scripts/verify_qwen_sft_derived.py, tests/test_qwen_sft_derived.py. Existing Raw validator, old preflight, tests and Policy unchanged. Generator reuses tested Raw schema verification; independent verifier imports neither generator nor classifier, uses a separate whitespace check and reads all disk artifacts. Source lines are copied byte-for-byte, preserving extra fields, JSON formatting, order and repeated records.

Mappings are per-split TSVs with one entry per Raw physical line, columns source_line and derived_line. Value 0 means excluded; retained derived lines are contiguous 1-based. Source SHA + split in manifest plus source_line reconstruct source_row_id for every entry. Raw and mapping rows: 210348 / 23110 / 1000, total 234458; retained rows total 234434; excluded 24.

## Risks and Edge Cases

SHA/schema/A.1 discrepancies, incorrect counts/reasons/content/mapping, existing output or Raw destination, and independent verification disagreement stop processing. Partial outputs/failure.json are retained; no automatic data repair. Full output is outside the Git tree; resolved paths prevent aliasing Raw. Operations assume quiescent local files; SHA guards do not promise protection from a malicious concurrent filesystem actor.

## Tests Run

Interpreter `/Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python`; working directory `/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement`.

- `python -m pytest tests/test_qwen_sft_derived.py -q`: **15 PASS**, 0.06s. Four reasons, double-error unique row, extra/nonempty field preservation, repeated prompt retention, no-final-LF, complete mapping, expected sample inclusion, no-overwrite, A.1 mismatch, SHA/schema stop; tampered content, missing/duplicate/reordered data, mapping, exclusions, manifest, checksums, Raw and A.1 detected.
- `python -m pytest tests/test_qwen_sft_raw.py tests/test_qwen_preflight.py -q`: **33 PASS**, 0.43s.
- `python -m pytest tests/test_grpo.py -q`: **19 FAIL**, 0.12s, pre-existing NotImplementedError in unchanged adapters. No old assertion/snapshot changed; not counted as PASS or new regressions.

Tests ran on 5d91c3b plus new source; test-provenance.json records exact source hashes, rechecked after committing code. Compressed GRPO log is lossless.

## Execution / Configuration

Execution code commit: `399448ee2a4e964706aebb38fe220a6c27c11dd5`. Raw/A.1/Policy identity revalidated at runtime. Source Git status (untracked evidence), Python, argv, timestamps and source SHA are recorded in manifest. Dataset mirror revision ac710ef808346bf458d7b093bfe4586cb15699d9; directly_comparable_to_official=false. No random sampling or model settings apply.

Actual generation command:

`/Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python scripts/derive_qwen_sft.py --output /Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1`

Actual independent verification command:

`/Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python scripts/verify_qwen_sft_derived.py --dataset /Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1 --raw-dir data/qwen-sft-mirror/sft-instruct --a1 artifacts/pa5-supplement-qwen/sft/20261028-p2a1-raw/raw-verification.json --report artifacts/pa5-supplement-qwen/sft/20261028-p2a2/independent-verification.json`

The same verifier was run on `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-restore-check` with a new report `restored-verification.json`. Both returned exit 0/PASS. Generation manifest remains honestly GENERATED_PENDING_INDEPENDENT_VERIFICATION; its immutable hash is bound by the separate PASS verification reports and acceptance.json, rather than rewriting it after the fact.

## Results

| Derived | Actual rows | Bytes | SHA256 |
|---|---:|---:|---|
| train | 210326 | 532395833 | `f83a631d5072b714d111bdedd54a849d40f0c386806039b4f9571c4249bc990f` |
| validation | 23108 | 58869509 | `ae6af19e5198f058ff08e8f36ffb028f3cf26fd2d45f90f99f4d99e5fb039ffc` |
| sample_train | 1000 | 2492043 | `b26bbe382793889ccb397e7c8afdf64ad3e52f0109d191e66c424587fba596df` |

Raw SHA/bytes/schema: PASS before derivation and rechecked during independent verification. All retained bytes/fields/order/multiplicity: PASS. No omissions, extra records, unauthorized rewrites or mapping offsets. Exact exclusions match all A.1 fields row-by-row: train 22 (1 empty_prompt, 21 empty_response); validation 2 empty_response; sample 0. No whitespace-only anomalies in real Raw. No actual runtime/schema/identity failure occurred.

Exact overlap (unique raw-string equality, no normalization): train/validation prompt=0, pair=0; sample/train prompt=1000, pair=1000; sample/validation both=0. Sample is a training subset, not validation. Near duplicates and semantic benchmark contamination remain untested.

## Raw Artifact Paths / Lineage

- Raw unchanged: data/qwen-sft-mirror/sft-instruct/{train,test,sample_train}.jsonl.
- Full Derived and full uncompressed mappings: `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1`.
- [Small evidence](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2a2): manifest, excluded_rows, compressed complete mappings, execution log, both verification reports, tests, test-provenance, storage-restore, acceptance and archive checksums.
- DATA_SHA256SUMS covers only the three full data files. METADATA_SHA256SUMS covers mappings, exclusions and immutable manifest, relative to the external dataset directory. ARCHIVE_SHA256SUMS covers Git evidence, source and this report, relative to repo root. Metadata checksums are not rewritten to pretend gzip bytes equal TSV bytes; decompression must match manifest TSV SHA.

## Persistence / Restore

Persistent local data directory: `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1`. Full bundle archive: `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1.tar.gz`; bytes=242051745; SHA256=`8c2d70c0ba412841920a9cfcc220d607542050bbe826b83be733244ac0f75b77`. Archive extracted into `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-restore-check`; all 11 files matched original SHA and full independent verifier passed again. Data, archive and restore copy are on the same Mac disk; no off-device backup claim. No complete Raw/Derived files are committed to Git.

Restore procedure: verify archive SHA from registry; extract into a new empty directory; from that directory check DATA_SHA256SUMS and METADATA_SHA256SUMS; run the independent verifier using pinned Raw and the archived A.1 report, writing a new report. Never overwrite existing evidence. If local copies are lost, restore Raw via the existing pinned inventory/restore tool, checkout execution commit, regenerate into a new external directory, then compare the three data hashes, mapping hashes and exclusions hash to this archive. Run-specific timestamps, paths and execution metadata may differ; dataset/mapping/exclusion bytes are deterministic. Availability of the upstream mirror is an external dependency, not a permanent hosting guarantee.

## Explanation for the Learner / Product Interpretation

Mapping is a complete ledger: each original row is either kept with exactly one output position or excluded with explicit reasons. Byte comparison proves retained content was not edited even if it contains repeated prompts or questionable answers. Machine PASS does not approve content quality, safety or training use.

## Learning Check / Remaining Questions

Learner explanation status=PENDING. Explain why 24 exclusions do not imply a high-quality dataset, how an excluded row appears in mapping, and why sample/train overlap is expected while train/validation overlap is a gate issue.

P2-B near-duplicate/benchmark semantic contamination, quality auditing/human review, risk adjudication and complete Data Admission remain PENDING. P3/SFT/GPU were not started. Next Gate suggestion: separately scope and authorize P2-B audit/review; no automatic progression.

## Archival

Execution and archive commits are separate. Archive commit is resolved via this file's Git history and the final remote check; no self-referential commit SHA. Stop after push/remote verification.
