# SFT Instruct Dataset

This folder contains the instruction-tuning dataset and evaluation data used for supervised fine-tuning experiments.

## Dataset Files

| File | Description | Size |
|------|-------------|------|
| `train.jsonl` | Training dataset (~200k examples) used for fine-tuning | 508 MB |
| `test.jsonl` | Validation dataset used for intermediate evaluation | 57 MB |
| `sample_train.jsonl` | 1,000-example subsample of train data for debugging training scripts | 2.4 MB |

## Alternative Download Links

You can also download the train and test datasets directly from Stanford:

- **Train**: https://nlp.stanford.edu/data/nfliu/cs336-spring-2024/assignment5/safety_augmented_ultrachat_200k_single_turn/train.jsonl.gz
- **Test**: https://nlp.stanford.edu/data/nfliu/cs336-spring-2024/assignment5/safety_augmented_ultrachat_200k_single_turn/test.jsonl.gz

## Evaluation Data

The `eval/` subfolder contains evaluation datasets and configs for running benchmarks:

| Eval | Description |
|------|-------------|
| GSM8K | Grade school math reasoning |
| MMLU | Massive multitask language understanding |
| Simple Safety Tests | Safety evaluation |
| Alpaca Eval | Instruction-following evaluation |

**Structure:**
- `eval/eval_configs/` - YAML config files for each evaluation dataset
- `eval/eval_data/` - Actual evaluation data files (csv, jsonl)

## Dataset Source

This dataset is the safety-augmented UltraChat 200k single-turn dataset from Stanford CS336 Assignment 5.
