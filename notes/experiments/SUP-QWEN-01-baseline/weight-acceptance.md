# Qwen7B 权重验收

日期：2026-10-03。Experiment：SUP-QWEN-01，PA5 Supplement Adapted Reproduction；`directly_comparable_to_official=false`。

## Objective / Model / Configuration

验证已有权重可用于本轮已授权SMOKE/PILOT，不重新下载权重。模型与tokenizer均固定`Qwen/Qwen2.5-7B@d149729398750b98c0af14eb82c78cfe92750796`。验收及GPU运行前云端HEAD固定`f5f4050de424a2b371da83e792fa5a4a81279084`，分支`learning/pa5-supplement`，工作区干净。

云端缓存：`/root/cs336/pa5-supplement/models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796`。tokenizer沿用`models/qwen-preflight/Qwen2.5-7B`。

## Evaluation Method / Results

**Weight acceptance PASS**。4个safetensors分片、config、generation_config、index共7个文件，总15,231,300,464 bytes（约15.23 GB）。上游HF metadata锁定到同一revision；分片核对上游LFS SHA256及bytes，小文件核对上游git blob SHA1及bytes，同时记录本地SHA256。index引用的恰好是4个通过验收的分片。

tokenizer及其配置按已归档preflight inventory逐项检查固定revision、bytes、SHA256。模型目录的config/generation_config也与preflight文件逐字节一致。AutoConfig/AutoTokenizer使用local_files_only加载成功，model_type=qwen2，EOS ID=151643。

验收前无下载进程。旧HF传输留下的partial/lock等文件在确认无进程、lock可非阻塞获得后，连同bytes/SHA清单移到仓库外`/root/pa5-supplement-setup/20261003-gpu-gate/download-residuals/`保留，没有删除或重下已验收权重。验收后模型目录无这些残留。磁盘空闲140,062,781,440 bytes；GPU空闲15 MiB、0%利用率。

## Evidence / Reproducibility

机器可读证据：`artifacts/pa5-supplement-qwen/baseline/weight-acceptance.json`；包含固定上游URL、每文件bytes/SHA、tokenizer inventory、残留保留路径及硬件信息。验收脚本和日志归档在本轮gate-audit目录；权重本身不进入Git。后续迁移可以固定revision重新下载并校验，不能把仅有文件大小当完整性证明。

## Limitations / Next Gate

权重验收不等于模型加载/生成成功；GPU实际证据另见smoke-report.md与pilot-report.md。没有下载72B权重，也没有进行SFT、DPO或O2训练。SFT的24条空字段保持原状。
