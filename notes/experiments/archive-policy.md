# PA5长期实验档案规范

生效日期：2026-10-02。适用Main与Supplement后续所有实验。用户授权的Gate范围不因本规范扩大。

GitHub仓库 `https://github.com/zhouhouze/assignment5-alignment` 是唯一实验索引入口。代码、配置、原始/派生产物引用、指标、人工复核材料、分析、环境版本及校验和必须可追溯；云盘和本地只能是副本或明确登记的持久化存储。

## 目录与分支

优先沿用 `notes/experiments/O1-prompting-baselines`、`O2-standard-grpo`、`SUP-00-environment`、`SUP-01-baseline`、`SUP-02-sft`、`SUP-03-dpo`、`SUP-final`；没有实际内容时不机械创建目录。O2-grpo-foundations等既有草稿不移动或合并。

Main历史保留在原分支/提交，统一索引使用不可变GitHub链接，不复制进Supplement。Supplement在learning/pa5-supplement提交和推送，Main未来变更在其所属分支checkpoint后更新统一索引。不得直接merge main/master。

artifacts沿用现有根目录；Supplement使用 `artifacts/pa5-supplement/`。baseline按benchmark/run_id；SFT/DPO各自run_id下分manifests/metrics/samples/review等。已有计划中的`safety`目录语义等同于建议的`simple_safety_tests`，目前尚无生成目录，后续统一采用`simple_safety_tests`，不并列创建二者。audit/preflight是准备记录，不标作模型SMOKE/PILOT/FULL。

## Manifest契约

每个正式SMOKE/PILOT/FULL建立唯一run_id，不覆盖旧run。记录：experiment_id、experiment_stage、date、git_branch、git_commit、dirty状态和源码hash；模型与tokenizer名称/revision；dataset_name/split/hash；prompt_name/hash；evaluator_name/version/hash；seed；generation_params（temperature/top_p/max_tokens/batch_size/stop/include_stop）；training_params（lr/optimizer/batch/grad_accum/epoch/beta/scheduler/clip）；hardware（GPU/count/VRAM/driver）；software（Python/Torch/CUDA/Transformers/vLLM/FA2）。

stage使用SMOKE/PILOT/FULL；status另记planned/running/completed/failed/partial，避免把阶段名当成功标志。未适用字段为null且在not_applicable说明原因；unknown与not applicable必须区别。初始化后只允许追加运行状态/终止时间等元数据，配置变化必须另建run。模板见 `manifest.template.json`，不得把模板填充前当正式manifest。

执行commit与归档commit分开：先固定运行代码commit；运行后归档产物commit在索引中定位。若测试发生于dirty树，保存准确源码hash/patch及来源提交，不谎称执行时树干净。checksum不包含自己，最终提交号无需写进自身导致循环；可用git log追踪文件所属归档提交。

## 原始与派生数据

baseline/eval逐题保留example_id、input/question、formatted_prompt、raw_response、ground_truth、parsed_answer、score、parse_failure、finish_reason、token_count。推荐generation raw只保存输入/原始输出，评分写 `scored-<evaluator-version>.jsonl`；旧schema保留不改写。原始文本禁止事后清洗覆盖。

judge额外保存prompt/candidate/reference、judge prompt/version、raw output、parsed result和invalid状态。Safe/Unsafe或偏好判断无效时必须显式记录；不让缺失结果默认提升指标。

SFT保存数据来源/revision/SHA/数量/split/preprocessing/模板/packing/seq_len/审计样本与质量分析，训练配置及loss/val/lr/grad/throughput/VRAM曲线、checkpoint metadata。DPO另存policy/reference revision、HH来源/过滤/验证划分、chosen/rejected样本、beta、optimizer和margin/preference accuracy。完整训练数据不必复制入Git，但必须可定位与核验。

合法空答、错答、格式错误、length输出全部保留；infra失败hard stop，failed/partial单列。指标文件明确metrics-smoke/pilot/full，或在run路径与manifest中同等明确。禁止把debug/pilot写成full。没有进行generation的准备记录不伪造raw或metrics。

## 报告与人工复核

正式阶段Markdown至少包含Objective、Configuration、Dataset、Model、Evaluation Method、Results、Raw Artifact Paths、Error Analysis、Representative Examples、Limitations、Reproducibility、Product Interpretation、Next Gate。

人工包保留原文、评分、抽样seed及human字段；未人工看过的字段null/pending。Baseline区分capability与parser问题；SFT区分风格/指令遵循与能力；DPO解释偏好数据的“好回答”定义以及安全、helpfulness、alignment tax。最终维护Base/SFT/DPO对照和SUP-final/data-flywheel.md。

## 大文件与提交

逐项git add，先检查大小，严禁git add所有文件。小型文档/JSON/manifests/review/checksum直接Git；raw先看大小，合理小可gzip，大文件用已授权LFS或持久存储（先确认服务可用和配额）。不为省空间丢弃唯一raw。

外部产物registry必须包含artifact name、storage location、bytes、SHA256、created_at、run_id、access/restore instruction和durability状态。云实例临时路径不能独立充当持久化证据。

禁止提交HF/API/WandB token、密码、SSH私钥、.env、基础模型/70B权重、缓存、venv、大型临时checkpoint和无关系统日志。正式训练权重在持久存储保留并登记，不能通过重新下载base恢复。

稳定Gate结束：记录测试状态→更新索引/报告/registry/checksum→检查staged文件大小和secrets→git diff --check/status/diff --stat→独立commit→push→核对远端commit。push失败明确记为未完成归档，不声称同步。回滚只revert相关commit，不重写历史。

## 现有历史证据边界

O1历史2026-07-16 raw丢失；2026-09-14复现单独登记，不替换历史。O1复现human review仍pending。O2仅单卡两侧独立smoke；训练侧完整启动日志曾未保存，保留实际summary而不补造日志。新规范不追溯伪造旧缺项；索引必须披露缺失。
