# Qwen Baseline 最小保存与复算

适用：SUP-QWEN-01，PA5 Supplement Adapted Reproduction，`directly_comparable_to_official=false`。
本说明不会自行启动实验。SMOKE/PILOT完成后必须停下，FULL需要新的授权。
当前状态（2026-10-03）：下载期间SSH失联，尚未启动GPU generation；下文smoke/pilot路径是已经准备的目标run路径，不能视为已经完成的产物。只有完整run及其checksum已归档后，才执行以下复算步骤。

## 最少保留哪些内容

- Git分支`learning/pa5-supplement`的代码、配置、官方prompts、原始benchmark、依赖锁文件、报告及实验索引。
- 各run的manifest、selected_examples、原始逐条JSONL及SHA、runtime/VRAM、生成日志、scored/metrics、review packet、执行状态和checksum。
- 权重与tokenizer的固定revision、文件大小与SHA256，以及恢复脚本。基础权重不用复制进Git或本地；这条原则不适用于未来不可重新下载的训练checkpoint。
- 人工复核未完成的字段保留pending/null；AI分析独立标记。

模型与tokenizer固定为`Qwen/Qwen2.5-7B@d149729398750b98c0af14eb82c78cfe92750796`。实际云端权重目录为`models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796`。权重下载清单记录7个文件，逐一核验上游LFS SHA256或git blob ID；不以文件名或文件大小代替完整性校验。

## 先恢复证据，再考虑模型

克隆上述分支并定位报告对应的归档commit。历史preflight的SHA256SUMS可能包含当时的可变文档，校验历史档案应使用该档案对应commit，不能拿最新README替代旧版本。新run的checksum从仓库根目录校验：

```sh
sha256sum -c artifacts/pa5-supplement-qwen/baseline/pilot/20261003-pilot-02/SHA256SUMS
```

macOS可使用`shasum -a 256 -c`。只阅读结果不需要GPU、模型权重或optimizer。

## 无GPU重新评分

在含运行代码和原始benchmark的仓库根目录，使用已安装依赖的Python。每次评分使用新的版本目录，不覆盖旧派生产物：

```sh
python -m cs336_alignment.qwen_baseline validate \
  --run-dir artifacts/pa5-supplement-qwen/baseline/pilot/20261003-pilot-02
python -m cs336_alignment.qwen_baseline score \
  --run-dir artifacts/pa5-supplement-qwen/baseline/pilot/20261003-pilot-02 \
  --score-version v3-rescore
```

validate会检查代码、配置、prompt、benchmark、选题与raw的hash及ID。若将来源码发生变化，先恢复manifest指定的版本和文件hash，不能删掉校验绕过。复算仅调用既有MMLU/final-number parser；不会加载模型，也不会重新生成。AlpacaEval/Safety仍是candidate，未运行Judge时不能得到winrate或safe-output proportion。

## 新机器恢复环境和模型

先按`SUP-00-environment`及Qwen preflight环境报告准备Python/CUDA/依赖；查看本run manifest中的实际版本。`scripts/restore_qwen_preflight_assets.py`恢复固定tokenizer/配置与已登记的SFT镜像（baseline推理本身不使用SFT数据）；只需复算时无需执行该恢复脚本。

在获准进行新GPU run、CPU gate通过后，可用以下命令恢复7B权重：

```sh
python scripts/download_qwen_baseline_weights.py --transport aria2
```

需要安装aria2。下载脚本固定7B revision及文件白名单，不下载72B；已有weights-manifest时拒绝覆盖，应按已有manifest核验并复用。下载网络中断与GPU generation failure要分开记录：前者可在模型加载前恢复未完成传输；后者触发本Gate的hard stop，不得自动重试。

## 新run与旧raw的边界

若未来另获授权重新生成，prepare使用全新run目录；先CPU，再SMOKE，通过后才PILOT。不要对已完成run删除raw后重跑。即使greedy、seed和版本相同，不同硬件/批次/依赖仍可能改变输出，不承诺逐token重现。

本阶段没有optimizer、梯度或训练checkpoint。后续训练可按脚本重建optimizer配置，但若要从训练中断点精确继续，还需要实际optimizer state和RNG/checkpoint，不能仅靠base模型下载恢复。
