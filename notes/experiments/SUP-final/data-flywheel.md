# PA5 Supplement数据飞轮（持续记录，尚无训练结论）

当前只完成审计与parser准备，尚未产生Base/SFT/DPO模型对照。本文件是分类与准入规则，不是最终效果报告。

模型输出 → evaluator → error taxonomy → 人工review → 高价值失败样本 → SFT / preference data → 训练 → regression evaluation。

| 失败类型 | 去向 | 准入条件 |
| --- | --- | --- |
| 明确指令未遵守、答案组织差 | SFT demonstration | 人工核验理想回答，另取训练样本；不能直接泄漏评估题 |
| 两个回答在helpfulness/safety/完整性等可比 | DPO pair | 标注者确认偏好与理由，保留分歧；不是单靠长度选chosen |
| 新能力边界或罕见安全场景 | 独立evaluation/regression set | 保持训练隔离，固定输入与评分协议 |
| parser误提取、judge无效标签默认safe | 修复/版本化evaluator | 先重评分原始输出，不把评分器bug伪装成模型训练样本 |
| 人工意见不一致或ground truth不可靠 | 待复核隔离池 | 不直接用于SFT/DPO，先澄清任务定义 |

当前已知evaluator风险：Safety helper把非true视为safe；GSM8K最后数字不一定是语义最终答案；MMLU严格句式可能导致parse failure。以上来自代码/协议审计，尚无真实baseline失败分布。

后续每个大Gate追加：证据run_id、样本ID、错误分类、review状态、拟回流数据、数据版本、回归结果。Base/SFT/DPO行为演进报告待实际训练与评估后生成，不能提前宣称alignment tax或改进。
