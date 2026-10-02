---
license: apache-2.0
tags:
- sft
- instruction-tuning
- reasoning
- cs336
datasets:
- HuggingFaceH4/ultrachat_200k
- hiyouga/math12k
---

# SFT CS336 Assignment 5 Datasets

This repository contains all training and evaluation datasets for Supervised Fine-Tuning (SFT) experiments (based on CS-336 Assignment-5)

## Repository Structure

| Folder | Description |
|--------|-------------|
| [sft-instruct/](https://huggingface.co/datasets/garg-aayush/sft-cs336-assign5-datasets/tree/main/sft-instruct) | Instruction-tuning datasets |
| [sft-reason/](https://huggingface.co/datasets/garg-aayush/sft-cs336-assign5-datasets/tree/main/sft-reason) | Reasoning SFT datasets |


## SFT Instruction finetuning
Datasets for instruction-following SFT is based on UltraChat-200K + SafetyLlama.
| File | Size | Description |
|------|------|-------------|
| sft-instruct/train.jsonl  | ~200K examples | Full training dataset |
| sft-instruct/test.jsonl | ~20K | Validation dataset for intermediate evaluation |
| sft-instruct/sample_train.jsonl | 1K examples | Debug subsample |

Note: You can also find the eval data and configs for: GSM8K, MMLU, Simple Safety Tests, AlpacaEval in `sft-instruct/eval` folder. See [Readme.md](https://huggingface.co/datasets/garg-aayush/sft-cs336-assign5-datasets/blob/main/sft-instruct/README.md) for more details.

**Trained Checkpoints using this dataset**
- [llama31-8b-sft-mask](https://huggingface.co/garg-aayush/llama31-8b-sft-mask)
- [llama31-8b-sft-nomask](https://huggingface.co/garg-aayush/llama31-8b-sft-nomask)

## SFT Reasoning finetuning
Datasets for math reasoning SFT based on `hiyouga/math12k`.

| File | Examples | Description |
|------|----------|-------------|
| sft-reason/sft_gpt-oss-120b_filtered.jsonl | 3,496 | Only correct reasoning traces |
| sft-reason/sft_gpt-oss-120b.jsonl | 4,836 | Full dataset (correct + incorrect) |
| sft-reason/val.jsonl | ~5K | Validation dataset |

See [Readme.md](https://huggingface.co/datasets/garg-aayush/sft-cs336-assign5-datasets/blob/main/sft-reason/README.md) for more details.

**Trained Checkpoints using this dataset**
- [qwen-2.5-math-sft-all](https://huggingface.co/garg-aayush/qwen-2.5-math-sft-all)
- [qwen-2.5-math-sft-filtered](https://huggingface.co/garg-aayush/qwen-2.5-math-sft-filtered)
- [qwen-2.5-math-sft-filtered-res-len](https://huggingface.co/garg-aayush/qwen-2.5-math-sft-filtered-res-len)
- [qwen-2.5-math-sft-filtered-2epoch](https://huggingface.co/garg-aayush/qwen-2.5-math-sft-filtered-2epoch)

For training code and experiment details, see: [building-from-scratch/sft](https://github.com/garg-aayush/building-from-scratch/tree/main/sft)