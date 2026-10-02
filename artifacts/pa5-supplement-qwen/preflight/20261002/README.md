# Qwen CPU preflight evidence

directly_comparable_to_official=false

No Qwen weight download, generation or training. `acceptance-v2/` is the final data audit (all string rows including empties; invalid line IDs). `acceptance/` preserves first-pass derived statistics (lengths were valid nonempty rows only); raw source files never changed. Identical review IDs/token stats are intentional.

Restore: `python scripts/restore_qwen_preflight_assets.py` verifies every pinned file, with no weights allowed. Audit to a fresh output directory: `python scripts/qwen_preflight.py --output /tmp/qwen-new-audit`. Targeted supplement: `python scripts/audit_qwen_refusal_sample.py --train data/qwen-sft-mirror/sft-instruct/train.jsonl --output /tmp/qwen-new-refusal.jsonl`. Human fields remain pending.

`tests-official.txt` records initial uv cache sandbox error; `tests-official-rerun.txt` is the real test result after using a writable temporary UV cache. Tiny GPT2 fixture weights load on CPU only in official DPO tests; no Qwen weights.

Source mapping/revisions/software/limitations: manifest.json. SHA256SUMS excludes itself, covers evidence and Qwen implementation/config/docs. The archive commit is discoverable from Git history.
