# P2-C Execution Report — Derived-v2

2026-10-31，`learning/pa5-supplement`，本地 Mac CPU。**P2-C = PASS（版本化机器处理）；Data Admission = PENDING / NOT APPROVED。**

## Goal / input identity

仅将已验收 Derived-v1 Train 的 181433 行（Raw train 物理 181453 行）从 v2 Train 排除。执行前重新计算 v1 三份数据、完整 mapping、exclusions、Manifest、DATA/METADATA 清单 SHA；均与 A.2 归档一致。v1 Manifest SHA=`c9eaf0e154f073500c237d6242a3d4188cdaf15e715a183e23d164813d3c352f`。Raw train SHA=`3b72228a7976079a5c5a30249fd3289179ad01006cbb67d15c7c366d4fd25913`。目标 Raw/v1 字节行完全相同，内容为 `What is the capital of Australia?` / `The capital of Australia is Canberra.`；source_row_id、P2-B.1 候选 #3273/#3274 的文本 SHA、AlpacaEval 370 固定数据 SHA和双字段均一致。Sample Train 中该完整 pair 为0，允许继续。

## Contract / method

v2 是独立新目录。Train 顺序流式复制 v1 的所有字节行，仅跳过 1-based 第181433行；Validation 与 Sample Train 逐字节复制。完整 Raw→v2 mapping 从 Raw→v1 mapping 重算：原有0保留0，目标变0，其后非零行号减1。原有24条 v1 空字段 exclusions 原样保留；`delta-exclusion.json` 单列本轮一条，不将其伪装为 Policy v1 空字段原因。v2 Manifest 绑定 v1 文件清单、执行commit、目标身份、输出行数/bytes/SHA；DATA/METADATA 各自有校验和。不存在 tensor、训练或 GPU 配置。

## Actual results

| split | Rows | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| Train | 210325 | 532395732 | `0678b25fcfd387df125012efbf054d2379c5eff2205400c932b37414e9db21e8` |
| Validation | 23108 | 58869509 | `ae6af19e5198f058ff08e8f36ffb028f3cf26fd2d45f90f99f4d99e5fb039ffc` |
| Sample Train | 1000 | 2492043 | `b26bbe382793889ccb397e7c8afdf64ad3e52f0109d191e66c424587fba596df` |

Train mapping 210348 Raw行中23条为0（原22+本轮1），其余210325个行号连续；mapping SHA=`36c85474bc72c5c6a6217b6476594c1cb27a4678ad88a21546a56f8f8c404473`。独立验证器逐行比较 v1/v2 Train 原始字节、完整 mapping、未变的 Validation/Sample/旧 exclusions 和 v1 输入 SHA，结果PASS。AlpacaEval 370完整问答在v2 Train中余0；Sample仍为Train pair子集。v1及Raw复核后SHA不变。v2 Manifest SHA=`a3fc513614bd98deb524306b0a607bad25095a0aacbbcda7ebccee0254b11bff`。

## Tests / execution

执行代码commit `4dd8cbe8371aa2a2bc6d2e08a64fe5d9f4d65b18`。`python -m pytest tests/test_qwen_sft_v2.py -q`：4 PASS，覆盖行号/恰好一条/字节/映射/拒绝覆盖。相关 A.2、Raw、B.1 回归：58 PASS。`python -m pytest tests/test_grpo.py -q`：19个既有 `NotImplementedError` FAIL，未修改 GRPO 或测试。真实生成、独立验证、tar恢复及恢复目录复算命令/状态见[执行日志](../../../artifacts/pa5-supplement-qwen/sft/20261031-p2c/execution-log.txt)。执行与归档commit分开；归档commit由本文件Git History定位。

## Artifacts / restore

完整数据、mapping与元数据：`/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261031-p2c-derived-v2`。便携归档：`/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261031-p2c-derived-v2.tar.gz`，206364415 bytes，SHA=`f49a0e731637d1ab4ba5682a2a005dd57d7a2eb022e3c28827416216cc50e17c`。提取到全新目录后DATA/METADATA校验和与独立验证器PASS；恢复副本位于同一Mac磁盘，不代表异地备份。Git仅归档小型 manifest/delta/验证/日志/checksum，不提交完整数据。恢复时先核对tar SHA，再解压到新目录、核对两个校验和，并以v1输入运行 `scripts/verify_qwen_sft_v2.py`；不要覆盖历史版本。

## Limits / next gate

仅处理用户指定的一条完整问答重叠。其余 P2-B.1 近重复候选、语义风险、来源与人审结论仍未解决；短问答的来源因果关系也未由机器证明。本轮不修改冻结Policy、不扩大扫描或清洗。下一Gate需另行人审和正式Data Admission决策；不得因P2-C PASS进入P3/SFT/DPO/Judge。
