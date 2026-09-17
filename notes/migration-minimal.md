# PA5 最小迁移与实验进展（2026-09-18）

## 当前进展

| 实验 | 已完成 | 尚未完成 |
| --- | --- | --- |
| O1 历史正式实验，2026-07-16 | 三种 prompt 的 GSM8K test 全量结果及报告 | 旧 AutoDL 逐题原始文件无法恢复 |
| O1 归档复现，2026-09-14 | 3×1319 raw、metrics、manifest、日志、checksum、review packet | 新抽样的 Cat2/3 各12条人工复核 |
| O2 Standard On-Policy GRPO | 7项标准组件测试、数学/梯度 sanity、HF训练侧与vLLM生成侧独立单卡 smoke | 双卡共存、NCCL同步、真实闭环、50步pilot、200步×4 seeds、最终报告 |

O1 历史 accuracy/format：question_only 0.08%/16.91%，r1_zero 0.08%/63.68%，three-shot 17.82%/95.15%。复现分别为 0.08%/16.91%、0.08%/63.68%、18.57%/94.09%。新结果不替换历史结果，也不声称逐题复现。

O2 完整 GRPO 测试历史结果为7 passed/12 failed；12项是未实现的后续变体，并非整套通过。没有正式训练模型或可续训 optimizer checkpoint；现有 smoke 只能证明两侧独立工作。

## 保存原则

保留：Git代码、测试、prompt、grader、依赖锁、GSM8K小数据、真实raw输出、指标、配置、日志、人工复核材料、校验和。配置不能重新生成已经发生的随机实验结果，因此 raw 必须保存。

不新增保存：基础模型权重、tokenizer缓存、`.venv`、uv/pip缓存、vLLM编译缓存、CUDA安装包。按固定版本重建。已有大文件不在本轮删除。

未来训练后的权重不能从基础模型下载恢复：每个正式seed保留最终权重；需要续训时保留最新完整checkpoint（模型、optimizer、scheduler、RNG、步数及数据/rollout进度）。optimizer超参数可以重建，动量状态不能。

## Git版本与脚本清单

仓库：<https://github.com/zhouhouze/assignment5-alignment>。

| 内容 | 分支及固定提交 | 入口 |
| --- | --- | --- |
| O2标准组件及单卡验证 | `learning/grpo-foundations`，`9321c61d2814fa3db464690ccfe68b199057d39d` | `cs336_alignment/grpo.py`、`tests/adapters.py`、`scripts/o2_single_gpu_smoke.py` |
| O1复现归档 | `learning/o1-reproduction-20260914`，`96b14809b08927516cfd049cfc6ddb33cd3f115c` | `scripts/prompting_baselines.py`、`notes/experiments/O1-prompting-baselines/reproduction-report.md` |
| O1实际生成代码 | `a75ef3db48e3bbf293def0441f0229f6d1371254` | `scripts/prompting_baselines.py` |

O1后处理脚本保存在 `artifacts/O1-prompting-baselines-reproduction/20260914-190540/manifests/o1_reproduction_archive.py`；这是当时归档脚本快照，迁移后先检查其路径常量。O1/O2分支分别恢复，不将一个分支误认为包含另一分支全部成果。

O2证据位于 `artifacts/O2-standard-grpo/single-gpu/` 与 `notes/experiments/O2-standard-grpo/`。O1证据位于O1分支的 `artifacts/O1-prompting-baselines-reproduction/`，包括raw和完整压缩包；这些已归档内容保留现状，不额外复制一套进O2分支。

## 环境与重新下载版本

2026-09-18通过SSH读取包元数据：Ubuntu 22.04、Linux x86_64、Python 3.12.7（Anaconda构建）、uv 0.12.13、Torch 2.10.0+cu129、Transformers 5.7.0、vLLM 0.19.1、FlashAttention 2.8.3、huggingface-hub 1.13.0。历史已验证CUDA runtime 12.9、驱动595.71.05、RTX5090 32607MiB。

以仓库 `pyproject.toml` 和 `uv.lock` 为依赖真源。FlashAttention使用pyproject内固定的社区wheel URL，后续下载仍需校验lockfile；不是官方wheel。Python换成同版本的其他发行构建时，应记录差异并重新验证。

基础模型与tokenizer：`allenai/OLMo-2-0425-1B`，revision `a1847dff35000b4271fa70afc5db10fd29fedbdf`；缓存历史约5.6GiB。模型下载可用性未在本轮重新验证。

GSM8K直接保留仓库的 `data/gsm8k/train.jsonl` 和 `test.jsonl`，避免上游版本漂移；test为1319条，SHA256 `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`。更多文件指纹见同目录 `migration-files.json`。

## 新机器恢复示例（本轮未执行安装、下载或GPU实验）

在新目录恢复，避免覆盖旧云端有未提交改动的checkout：

```bash
git clone --branch learning/grpo-foundations https://github.com/zhouhouze/assignment5-alignment.git pa5
cd pa5
git worktree add --detach ../pa5-o1 96b14809b08927516cfd049cfc6ddb33cd3f115c
# O2代码精确快照，如需独立比对：
git worktree add --detach ../pa5-o2-checkpoint 9321c61d2814fa3db464690ccfe68b199057d39d
```

Linux x86_64，先安装uv 0.12.13并提供Python 3.12.7；可按uv安装工具的包版本固定安装 `uv==0.12.13`。在要运行的worktree中：

```bash
uv sync --python 3.12.7 --frozen --extra gpu --no-install-package flash-attn
uv sync --python 3.12.7 --frozen --extra gpu
export HF_HOME="$PWD/.huggingface"
uv run --no-sync python -c 'from huggingface_hub import snapshot_download; print(snapshot_download("allenai/OLMo-2-0425-1B", revision="a1847dff35000b4271fa70afc5db10fd29fedbdf"))'
```

snapshot_download打印固定revision的本地目录；运行O2 smoke时将该目录传给 `--model-id`，避免默认模型名解析到将来变化的main。安装后的命令使用 `uv run --no-sync`，避免默认同步移除GPU extras。

先运行标准组件CPU测试：

```bash
uv run --no-sync pytest tests/test_grpo.py -k 'tokenize_prompt_and_output or get_response_log_probs or compute_rollout_rewards or compute_group_normalized_rewards_grpo or test_compute_policy_gradient_loss_on_policy or aggregate_loss_across_microbatch_sequence or grpo_train_step_standard_on_policy'
```

GPU准备好且CPU测试通过后，两个smoke顺序运行，MODEL_SNAPSHOT设为下载命令输出目录，RUN_DIR设为全新结果目录：

```bash
uv run --no-sync python scripts/o2_single_gpu_smoke.py training --model-id "$MODEL_SNAPSHOT" --output-dir "$RUN_DIR"
uv run --no-sync python scripts/o2_single_gpu_smoke.py rollout --model-id "$MODEL_SNAPSHOT" --output-dir "$RUN_DIR"
```

O1已有结果不需要再次生成；在O1 worktree的 `artifacts/O1-prompting-baselines-reproduction/` 目录中用 `shasum -a 256 -c SHA256SUMS` 校验。O2在 `artifacts/O2-standard-grpo/single-gpu/` 中用 `shasum -a 256 -c SHA256SUMS` 校验。

## 实验配置与下一步

O1：seed0、temperature1、top_p1、max_tokens512、batch4、GPU利用率预算0.75；question_only无answer停止词，两个R1 prompt用 `stop=["</answer>"]` 并保留停止字符串。prompt/grader指纹和完整配置在O1 manifest。合法空答、错答、格式错误、长度截断均保留，不重采样。

O2计划配置（尚未完成正式训练）：6400 train、1024 val、200 rollout steps、4 seeds、lr1e-5、AdamW betas(0.9,0.95)、weight_decay0、max_grad_norm1、rollout/train batch256、group8、32 prompts×8、grad accumulation32、temperature1、top_p1、max_tokens512、r1_zero。正式运行前还需固定seed列表、数据划分、scheduler/warmup及完整训练入口；不能将本配置表当作已经可运行的训练程序。

下一步：人工填写O1 review packet；O2准备双GPU后验证one-step闭环，再做50步pilot、复核、4seed full。当前一张5090不满足既定双卡架构。

## 存储与安全边界

最小长期归档不需要保存约13GiB虚拟环境或5.6GiB模型缓存。仓库已包含小数据和实验输出；本轮新增内容仅文档与JSON清单。恢复时另预留环境、模型和训练checkpoint空间。SSH密码、访问token不入Git；迁移说明不依赖固定SSH端口。
