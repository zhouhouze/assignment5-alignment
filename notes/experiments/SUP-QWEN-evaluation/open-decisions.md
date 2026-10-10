# SUP-QWEN-EVAL-v1 — Open Decisions与阻塞范围

P0技术口径已冻结，决策状态见[evaluation-decision-log.md](evaluation-decision-log.md)。本页仅列剩余事项；不能把已批准SFT空白策略或已冻结accuracy再写成待讨论。

## Blocks P1

| 类型 | 待完成事项 | 状态 / 解决建议 |
| --- | --- | --- |
| 技术实现 | Full CLI/selection/manifest/保护及CPU测试 | BLOCKED；下一轮批准CPU readiness准备 |
| 恢复/规模验收 | pending/failed事故核对、immutable continuation、复合ID/计时唯一、Full规模IO | BLOCKED；先CPU无模型故障注入与规模验证，不在GPU上试错 |
| 现场检查 | 执行机HEAD、7B weights SHA、软件、GPU空闲/显存、磁盘/inodes、持久化恢复 | PENDING；启动前实查，旧云端记录不能替代 |
| 用户执行/预算 | P1生成授权、GPU租费/小时上限、最终raw持久存储位置 | PENDING USER APPROVAL；本轮仅P0，未启动Full |

准确率分母、原Prompt/512/stop、数据ID/hash、parser等已FROZEN，不需下一轮重议。详见[readiness](p1-full-baseline-readiness.md)。

## Blocks SFT

- 空串/纯空白过滤策略已FROZEN；实际P2过滤/准入执行仍待批准。
- SFT质量人审人员/规模/预算、实际派生数据SHA与隔离验收。
- Dataset/batching/training实现、optimizer状态精度、硬件/并行预算、checkpoint选择细节。

以上不阻塞P1 Base自动评分；不得凭本轮批准策略自动清洗数据。

## Blocks DPO/Judge

- DPO：SFT checkpoint、HH单轮数据准入/隔离、人审预算、RMSprop/长度/硬件细节与训练授权。
- Judge：自定义annotator运行/解析mock和统计兼容；LC Win Rate=NOT VALIDATED；真实Judge=NOT RUN。
- Judge可靠性样本规模、人审/争议裁决人员、单/双顺序Full及聚合、异家族审计资料、GPU/存储预算均PENDING USER APPROVAL。
- 旧提案位置翻转10%/人工agreement80%没有批准，不作为成功阈值。

这些不阻塞P1候选输出；P1不生成赢率、安全分或LC数值。

## Product quality decision only

可接受数学/知识退化、安全与帮助性取舍、误拒容忍、用户满意度目标、最小有用胜率提升均PENDING USER APPROVAL。缺产品场景就保持未决；**不阻塞P1观察性学习，也不阻塞P0技术完成**。不能据本实验宣称上线验收通过。

## 其他后续诊断与人工资源

2×2设计与效应公式已冻结；每任务100题样本规模、benign/harmful 50+50、自动重复探测器阈值仍PROPOSED，诊断执行须单独批准。bootstrap计算规则已冻结，不意味着批准多seed训练。

现有27条review继续pending；优先使用已有包。P1可生成并归档自动评分/待审包，人审人选/规模/预算阻塞“人工复核完成”声明而不阻塞候选生成。新争议记录只追加sidecar。
