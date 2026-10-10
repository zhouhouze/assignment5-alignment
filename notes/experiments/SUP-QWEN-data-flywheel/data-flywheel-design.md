# 离线实验与产品数据飞轮

状态：闭环与隔离规则纳入SUP-QWEN-EVAL-v1，FROZEN；新数据构建/回流/再训练 NOT RUN。核心是把“发现问题”转为经过准入的训练资产，同时保持可信评估。

```text
Immutable model outputs + run manifests
        ↓
Versioned evaluator + uncertainty/invalid audit
        ↓
Multi-label error taxonomy + AI initial analysis
        ↓
Human review / high-risk adjudication
        ↓
Routing decision + evidence + reason
        ├─ SFT candidate demonstrations
        ├─ DPO candidate preference pairs
        ├─ Evaluation/regression only
        ├─ Evaluator fix and consistent rescoring
        └─ No action / pending evidence
        ↓
Rights/privacy → dedup → split firewall → quality → version → human admission
        ↓
Approved training cycle → frozen independent re-evaluation → paired transitions
```

## PA5离线闭环

第0轮为本次Base/SFT/DPO课程链；第1轮候选只有P10提出建议，不自动追加训练。每个错误先判断是输出能力、偏好、格式还是评分器问题，再用[路由政策](data-routing-policy.md)决定。保留支持原文、错误标签、严重度、拟解决机制、预期指标、guardrail、所需样本类型、成本与验证实验。

正式MMLU/GSM8K/Alpaca/SST及本轮冻结诊断样本只做评估/回归证据，不把题目、标准答案或模型修正答案直接转入训练。对已见错误可概括技能缺口，再从独立授权来源收集新场景；需近重复/实体/数值结构人工检查，简单换数字仍可能泄漏。若确需研究benchmark训练，另设污染实验和全新干净test，不在原表宣称独立泛化。

每轮只变一个主要因素：例如独立多步骤任务SFT数据，或合理拒答DPO对；不同时换prompt、judge和数据然后归因数据。固定独立holdout与上一模型配对，新增回归集标已暴露，不把它当全新测试。冻结一个尽可能少看见的确认集、限制反复调参；必要时再收独立测试集。

飞轮效果看：候选→人工通过率、错误机制覆盖、S3未决数、泄漏拒收数、下一轮修复/回归转移、单位标注成本、能力/安全/长度guardrail；数据量增加不是成功标准。标注成本与GPU成本分开。

## 真实产品线上闭环（未来方案，不采集本轮数据）

| 信号 | 可形成的候选 | 不能直接推断 |
| --- | --- | --- |
| 用户问题/上下文 | 场景聚类、任务分布、回归覆盖 | 高频不必然高价值；需合法授权/最小化 |
| 低满意度/点踩 | 失败检测与优先审阅 | 点踩可能来自延迟、产品交互或个人偏好，不等于内容错 |
| 用户修改回答 | 经验证的SFT示范或原答/修订DPO候选 | 修改可能引入错/隐私/风格差异，不自动当GT |
| 人工偏好 | rubric明确的chosen/rejected | 需上下文完整、盲化和争议仲裁，不能取多数掩盖安全要求 |
| 任务结果 | 成功/失败的外部验证信号 | 结果受工具/用户行为/延迟等混杂，不能全归因模型 |

线上需明确数据使用授权、隐私/敏感字段脱敏、访问控制、保留期和删除流程，训练同意与产品日志同意分开记录。企业机密/个人数据不进入公开GitHub；本项目不把聊天/生产数据自动外传给Judge。无许可则拒收或仅保存去标识聚合统计。

产品上线还需独立发布流程和真实任务验证；本课程benchmark提升不等于用户满意度提升，也不授权A/B上线或实际用户数据训练。
