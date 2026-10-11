# P1B-1 real FULL evidence

Four task-specific runs; run_code_commit `47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726`. Adapted reproduction, directly_comparable_to_official=false. Original manifests and formal metrics are copied byte-for-byte; AI INITIAL ANALYSIS and human PENDING are separate.

- `runs/*/source-inventory.json.gz` and `quiescent-source-snapshot.json.gz` decompress to the exact original cloud/backup JSON; they enumerate external artifact bytes/SHA.
- `full-bundle-SHA256SUMS` refers to paths in the **external full finalized bundle**, not this reduced Git directory. `SHA256SUMS` at this evidence root covers files actually included here.
- Raw/scored/selected inputs/attempt details/complete VRAM samples remain in verified Mac CAS, independent restored directories and portable archive. See external-artifacts.json and the repository registry. Downloadable weights/tokenizer/config/environment are pinned, not archived as weights.
- `execution-helpers/` records external orchestration/reporting source used this session; it was outside the clean inference tree and is **not** falsely attributed to run_code_commit. It calls the existing runner/backup implementation, implements no new inference path and must not be rerun as a new experiment without authorization.
- `analysis/review_packet.jsonl`: preserve exact raw original response, reference and frozen score; human fields null/PENDING. Use physical LF JSONL iteration, not Unicode str.splitlines().
- All holdout questions stay evaluation-only. Routing ledger labels are provisional where examined, UNKNOWN elsewhere; no SFT/DPO/Judge was run.

Reports: ../../../../../notes/experiments/SUP-QWEN-evaluation/p1b-full-baseline-report.md and qwen-base-behavior-profile.md.

Generation/score logs are stored as `.log.gz` because the repository ignores generic `.log`; gzip decompresses to exact original bytes, whose SHA is also in source/snapshot or score-log transfer evidence. No original cloud/Mac run log was modified.
