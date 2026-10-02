# Supplement前置修复、parser与GitHub归档（PREPARATION）

日期2026-10-02。本报告对应用户明确授权的environment repair / HF validation / 两个parser / 测试分类 / SFT来源调查 / 归档与push；不是baseline结果。

## Objective

建立可恢复的Supplement准备环境，并把Main/Supplement统一纳入GitHub实验索引。流程：环境/数据来源 → parser → 后续generation → immutable raw → versioned scoring → review/report → commit/push。本轮只完成前置节点与归档规则。

## Configuration

独立分支learning/pa5-supplement；官方基础c2734a2，初审36de0b7，parser实现4b6014e5aab04eac304b98122653a5fdf43a785b。工作区仍是正式tmp/pa5-supplement，不清理。修复脚本 `scripts/setup_supplement_environment.sh`，审计脚本 `scripts/audit_supplement_environment.py`。

环境验收最终状态见同目录报告末尾“Environment Verification”和preflight/environment.json；不以包下载日志代替导入或GPU验证。原始初审记录保留在20261002目录，新记录在20261002-preflight。

## Dataset

课程四类evaluation和HH文件存在于仓库，数量/hash见初审dataset-inventory。SFT课程预处理文件未获得；公开源revision与API证据已存sft-sources.json，详情见SUP-02-sft/dataset-source-investigation.md。本轮不抽样伪造data-audit结论。

## Model

8B base与70B judge固定revision沿用初审候选。本轮对各自固定revision的config.json和tokenizer_config.json执行HEAD：共4项均HTTP401。HF标准凭据未发现；不推断账号许可被拒。未下载大模型权重，未生成响应，未启动训练或judge。Git自带tiny测试夹具用于CPU测试，与下载实验模型区分。

## Evaluation Method

两个官方parser测试各2项通过；额外16项边界验证。解析协议、已知局限、示例和精确命令见parser-report.md及test-results.json。新审计脚本已通过py_compile并在本地进行无模型访问的运行检查；shell安装脚本通过bash -n。

## Results

本地Supplement+边界：20 passed / 3 failed。官方7项中4通过，3项SFT/DPO仍NotImplementedError。完整官方Main脚手架19失败是隔离分支的预期未实现状态，不是Main历史O2回归。后续云端验收结果见Environment Verification。

本轮没有模型准确率、AlpacaEval胜率、安全率或训练loss。没有SMOKE/PILOT/FULL结果可发布。

## Raw Artifact Paths

`artifacts/pa5-supplement/audit/20261002-preflight/`保存测试日志、test-results、HF访问记录、SFT源metadata、manifest/environment/checksum；本轮的raw证据是命令/测试/访问记录，不创建虚假的generation raw.jsonl。

Main历史28个产物只登记固定GitHub提交、bytes和SHA，不移动、不覆盖；总计13,541,825 bytes，包括O1复现raw与压缩包、O2单卡smoke证据。详见notes/experiments/artifact-registry.json。

## Error Analysis

1. HF401：无认证，后续需在服务器安全登录已获访问许可的账号；不要把token发送进聊天/仓库。
2. SFT源缺口：无课程混合文件/处理脚本，不能默认等价于原始UltraChat。
3. Safety helper的invalid输出默认safe问题尚未修改，在正式judge前必须单列和处理。
4. baseline runner尚未实现；parser通过不代表baseline可直接运行。

## Representative Examples

MMLU “A is tempting, but the correct answer is D.” → D；冲突A/B声明→None。GSM8K “$1,234.50”→1234.50。均为测试例子；不作为模型效果样本或人工复核。

## Limitations

CPU测试不证明8B能正常推理；包导入与小张量CUDA kernel不证明vLLM generation可运行；无HF权限时仍必须停在模型加载前。未获得真实baseline，不能讨论Base/SFT/DPO效果增减。SFT/DPO硬件门槛和数据问题保持原状。

## Reproducibility

以各manifest的代码commit/源码hash为准，归档commit由文件Git历史定位，防止自引用。raw生成不可改写，重评分另建scored文件。阶段与执行状态分离；模板不是run。

可恢复内容：Git clone指定分支 → pyproject/uv.lock重建 → 数据hash核验 → 新run验证。Base/Judge模型仅存name/revision，venv/uv缓存留服务器而不入Git。此时没有训练checkpoint需要外部保管。

## Product Interpretation

完整档案让评估数字可追溯到模型、prompt、parser和原文；现阶段最大价值是避免把未实现、访问失败或parser错误包装成模型能力结论。人审字段仍须由人填写，自动分析不代签。

## Next Gate

先解决HF登录/权限并核对环境验收；随后等待授权开发baseline runner和1条/20条验证。正式full、SFT、DPO和70B judge均未获本轮启动授权。Next task：完成可访问的8B准备后再申请下一Gate。

## Environment Verification

**环境修复与kernel验收PASS；模型访问仍BLOCKED。**

- 云端项目：`/root/cs336/pa5-supplement`，验收时代码4b6014e，工作区clean。
- Git2.43.0、uv0.12.13、独立Python3.12.13；系统默认Conda Python3.14未覆盖。
- Torch2.10.0+cu129、CUDA runtime12.9、Transformers5.7.0、vLLM0.19.1、FlashAttention2.8.3；安装命令退出0，包导入成功。
- seed0 BF16 32×32 matmul finite；FA2输入/输出[1,16,2,64]、causal=True、finite，synchronize成功。仅环境kernel验证，没有model load或generation。
- 云端Supplement+边界：20 passed/3个NotImplementedError，2.16秒；与本地一致。
- 云端179个数据文件SHA全部通过。环境修复后磁盘196G/40G used/146G available，GPU回到15MiB。
- 环境/测试/安装记录9个文件通过传输manifest SHA校验，两个审计helper和GPU检查源码与云端执行字节一致；传输包SHA：`ced3834f312dd73de8816bfc78ba83505596b5973d329068fa87529f0d252c1d`。
- 恢复示例：在Linux独立checkout安装uv0.12.13后执行 `SUPPLEMENT_UV_BIN=/root/pa5-supplement-bootstrap/bin/uv bash scripts/setup_supplement_environment.sh`；后续使用`.venv/bin/python`或`uv run --no-sync`，避免默认sync移除GPU extras。
- HF访问：两个固定revision的config/tokenizer_config均401，无凭据。登录命令可在用户自己的SSH终端使用 `.venv/bin/hf auth login`；token不得入聊天/报告/Git。登录不等于两款模型都获批，后续重新HEAD验证。
- 本轮安装日志仅记录与环境恢复相关的依赖，没有存放无关系统日志。提交前23项run checksum、28个Main历史产物指纹均通过；staged秘密模式扫描（含解压安装日志）无匹配，新增内容约115KB，无模型缓存。GitHub归档提交由索引文件的Git历史定位，push后另核对远端HEAD。
