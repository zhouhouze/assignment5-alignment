# Supplement分阶段路线

本轮仅完成A审计与B计划。每个Gate独立验证、记录并checkpoint commit，不force push、不提交凭据/模型缓存；大模型和环境按revision/lock重建，训练权重与原始实验输出必须保留。

| Gate | 内容 | 放行条件 / 停止点 |
| --- | --- | --- |
| A | 环境/仓库/模型权限/数据/测试审计 | 当前报告已完成但环境未就绪；等待批准修环境与进入B |
| B | Base四benchmark；先8B generation，再另安排70B judge | parser测试、smoke、pilot、full、raw重算、每benchmark≥10人工样本；Baseline Review后停止 |
| C | 课程混合SFT数据审计 | 取得准确预处理数据/hash；seed0抽20–50例，任务/风格/错误/幻觉/拒答/配比；回答“模仿后会是什么产品” |
| D | packed dataset、batching、LM loss、梯度累积、validation、checkpoint | 官方test_data通过；形状input_ids/labels=[B,L]、int64、next-token对齐、EOS/packing/尾块；不使用Trainer |
| E | SFT 10–50 optimizer steps smoke | BF16/FA2、forward/backward、finite loss/grad、clip、save/reload、val、tokens/s/peak VRAM均通过 |
| F | SFT pilot后full | 8B全参，context512、effective batch32、1epoch、lr2e-5、cosine、warmup3%、wd0.1、clip1；先锁optimizer与validation/checkpoint周期；按显存实测准入 |
| G | Post-SFT四benchmark | 同数据/parser/生成参数/judge，官方Alpaca外层模板；Base/SFT/Δ、长度/parse failures、10组原文对照；Review后停 |
| H | HH preference审计 | 四来源分别统计，排除不符要求多轮，保留instruction/chosen/rejected/source/过滤理由；helpful≥10、harmless≥10人工判偏好并记录分歧 |
| I | per-instance DPO loss | 官方test_dpo通过，验证chosen/rejected/reference logprob、beta、符号、mask/EOS；policy有梯度、reference冻结 |
| J | DPO 10–50步smoke/pilot | 两卡policy/ref，同SFT checkpoint；约200例独立val；effective batch64、beta0.1、lr1e-6、RMSprop；无NaN/OOM，检查val与margin |
| K | DPO 1epoch | 按预先定义的最高val classification accuracy保存best，另保留必要resume；模型/tokenizer/manifest/logs完整 |
| L | Post-DPO四benchmark | Base/SFT/DPO表，至少10组SFT/DPO原文对照；区别能力、格式、风格、安全与evaluator问题；最终Review |

DPO loss：`-log sigmoid(beta * [(logπ(chosen)-logπ(rejected)) - (logπref(chosen)-logπref(rejected))])`。后续实现前逐行核对官方docstrings/tests，不提前填adapter。

指标需避免歧义：手册§6.4文字把classification accuracy描述为policy chosen logprob高于rejected；同时所谓implicit-reward margin还涉及reference修正。计划同时记录policy preference accuracy与reference-corrected margin/accuracy，分别命名；best checkpoint默认按手册文字的前者，若调整先在Gate J明确，不能看到结果后换指标。

## 硬件租用

- CPU/现有5090：仓库、parser、数据审计、8B baseline；先完成CPU准备再计费跑GPU。32GB全参SFT资源不足时报告，不自行改量化/LoRA/offload。
- SFT：80GB或更大显存实例；先核对optimizer state dtype、master weights和activation，再smoke定容量。80GB不作无条件保证。
- DPO：2张大显存GPU分别policy/ref；70B judge分时使用足够总显存、支持tensor parallel的双卡实例。无需从头到尾租双大卡。
- 官方标注SFT约3 B200 GPU小时、DPO约1 B200 GPU小时仅作课程参考；本地无吞吐实测，不能推导5090/A100总完工时间。pilot后按实际tokens/steps吞吐估算，并计入下载、judge和人工复核。

## 结果与产品分析

SUP-02-sft/data-audit.md记录数据质量；SUP-03-dpo/hh-data-audit.md记录偏好来源。最终生成product-evaluation.md与data-flywheel.md：规则评估负责可验证知识/数学答案，judge与人工评估辅助质量/安全；拆分capability、instruction following、safety和evaluator失败。

SFT飞轮：失败→人工核验的理想回答→demonstrations。DPO飞轮：prompt→多个回答→可靠偏好→chosen/rejected。Evaluation飞轮：原始输出→错误分类→针对性eval→回归。评估集不得直接回流训练；需独立训练样本与去重审计，避免污染。

alignment tax只在能力指标下降且排查模板、解析、长度上限、数据泄漏和judge变化后讨论；不把单次点估计波动直接当结论。人工复核不由自动分析代签。
