"""Prepare the authorized, fixed P2 review packet; never write to source data."""

import argparse
import gzip
import hashlib
import json
import random
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def records(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def selected_lines(path, wanted):
    found = {}
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if number in wanted:
                found[number] = json.loads(line)
                if len(found) == len(wanted):
                    break
    if set(found) != set(wanted):
        raise ValueError(f"Missing selected rows in {path}")
    return found


def mapping(path, wanted_source=None, wanted_derived=None):
    found = {}
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        next(stream)
        for line in stream:
            source, derived = map(int, line.rstrip("\n").split("\t"))
            if wanted_source is not None and source in wanted_source:
                found[source] = derived
            if wanted_derived is not None and derived in wanted_derived:
                found[derived] = source
    if set(found) != set(wanted_source if wanted_source is not None else wanted_derived):
        raise ValueError("Incomplete mapping")
    return found


def write_jsonl(path, rows):
    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    pre = root / "artifacts/pa5-supplement-qwen/preflight/20261002/acceptance-v2"
    maps = root / "artifacts/pa5-supplement-qwen/sft/20261028-p2a2"
    raw = root / "data/qwen-sft-mirror/sft-instruct"
    derived = Path("/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1")
    expected = {
        raw / "train.jsonl": "3b72228a7976079a5c5a30249fd3289179ad01006cbb67d15c7c366d4fd25913",
        raw / "test.jsonl": "ce84dd834a7bbfc622cb3b50dc6c233e7dd91e002fd84f7cf86f70762a2c9ed9",
        derived / "train.jsonl": "f83a631d5072b714d111bdedd54a849d40f0c386806039b4f9571c4249bc990f",
        derived / "validation.jsonl": "ae6af19e5198f058ff08e8f36ffb028f3cf26fd2d45f90f99f4d99e5fb039ffc",
    }
    if any(digest(path) != sha for path, sha in expected.items()):
        raise ValueError("Source SHA mismatch")
    train = records(pre / "review-packet.jsonl")
    diagnostic = records(pre / "refusal-targeted-review.jsonl")
    ai = records(pre / "codex-review-annotations.jsonl")
    if len(train) != 20 or len(diagnostic) != 3 or len(ai) != 20:
        raise ValueError("Historical packet count mismatch")
    if {x["example_id"] for x in train} != {x["example_id"] for x in ai}:
        raise ValueError("AI packet identity mismatch")
    source_rows = {x["example_id"] + 1 for x in train + diagnostic}
    train_map = mapping(maps / "train.mapping.tsv.gz", wanted_source=source_rows)
    raw_train = selected_lines(raw / "train.jsonl", source_rows)
    derived_train = selected_lines(derived / "train.jsonl", set(train_map.values()))
    def train_entry(row, group):
        source = row["example_id"] + 1
        position = train_map[source]
        if row["line_number"] != source or position == 0 or any(
            obj[k] != row[k] for obj in (raw_train[source], derived_train[position]) for k in ("prompt", "response")
        ):
            raise ValueError(f"Train lineage/content mismatch: {source}")
        return dict(group=group, sample_id=f"train-raw-{source}", source_sha256=expected[raw / "train.jsonl"],
                    source_row_id=f"{expected[raw / 'train.jsonl']}:train:{source}", raw_line=source,
                    derived_line=position, prompt=row["prompt"], response=row["response"],
                    human_label=None, severity=None, human_notes=None, reviewer_id=None, reviewed_at=None,
                    human_review_status="pending")
    train_out = [train_entry(x, "historical_random_train") for x in train]
    diagnostic_out = [train_entry(x, "targeted_refusal_diagnostic") for x in diagnostic]
    positions = sorted(random.Random(0).sample(range(1, 23109), 20))
    val_map = mapping(maps / "validation.mapping.tsv.gz", wanted_derived=set(positions))
    val_derived = selected_lines(derived / "validation.jsonl", set(positions))
    val_raw = selected_lines(raw / "test.jsonl", set(val_map.values()))
    validation_out = []
    for position in positions:
        source = val_map[position]
        obj = val_derived[position]
        if obj != val_raw[source]:
            raise ValueError(f"Validation content mismatch: {position}")
        validation_out.append(dict(group="random_validation_derived_v1", sample_id=f"validation-derived-{position}",
            source_sha256=expected[raw / "test.jsonl"], source_row_id=f"{expected[raw / 'test.jsonl']}:validation:{source}",
            raw_line=source, derived_line=position, selection_probability="20/23108", prompt=obj["prompt"],
            response=obj["response"], human_label=None, severity=None, human_notes=None,
            reviewer_id=None, reviewed_at=None, human_review_status="pending"))
    args.output.mkdir(exist_ok=False, parents=False)
    write_jsonl(args.output / "train-20.jsonl", train_out)
    write_jsonl(args.output / "validation-20.jsonl", validation_out)
    write_jsonl(args.output / "diagnostic-refusal-3.jsonl", diagnostic_out)
    (args.output / "after-independent-review").mkdir()
    write_jsonl(args.output / "after-independent-review/ai-initial-analysis-train-20.jsonl", ai)
    manifest = dict(status="PREPARED_HUMAN_PENDING", branch="learning/pa5-supplement",
        train_sampling="Historical random.Random(0) sample of 20 from 210348 Raw rows; preserved IDs",
        validation_sampling="sorted(random.Random(0).sample(range(1, 23109), 20))",
        validation_derived_lines=positions, validation_selection_probability="20/23108",
        diagnostic_sampling="Historical 3 refusal-prefix candidates; separate from random samples",
        raw_and_derived_sha256={str(k): v for k, v in expected.items()},
        source_packet_sha256={name: digest(pre / name) for name in
            ("review-packet.jsonl", "refusal-targeted-review.jsonl", "codex-review-annotations.jsonl")},
        files={str(p.relative_to(args.output)): dict(bytes=p.stat().st_size, sha256=digest(p)) for p in sorted(args.output.rglob("*.jsonl"))})
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(status="PASS", train=len(train_out), validation=len(validation_out), diagnostic=len(diagnostic_out),
                          validation_lines=positions, output=str(args.output))))


if __name__ == "__main__":
    main()
