# DPO 训练与下游评估计划

状态：NOT RUN。假设：HH偏好优化改变helpfulness/harmlessness取舍；可能提高Judge偏好，同时产生数学/知识下降或正常请求误拒。没有下游配对证据就不能宣称产品变好。

## 初始化与课程设置

policy与frozen reference从**同一个已验收SFT checkpoint**加载，记录相同权重SHA/tokenizer。reference eval/no_grad/requires_grad=False且optimizer排除其参数，定期hash/数值抽查不变；policy保留梯度。不可用Base代替reference。

依据2026 handout §6：自实现per-instance DPO + gradient accumulation；建议一GPU policy、一GPU reference；RMSprop（非AdamW）；effective batch64，beta=.1，lr=1e-6，1epoch；约200例隔离validation；按最高validation classification accuracy保存checkpoint。betas不适用于RMSprop，需冻结alpha/eps/momentum/centered/weight_decay等实际参数；seed0提案、最大长度和超长处理均待P7审批，不能擅自继承SFT的512截掉偏好关键部分。

## Loss、shape与诊断定义

对prompt x和chosen y+ / rejected y−，定义 sθ±=sum_t log pθ(y±_t|x,y±_<t)，含response EOS；sref±同理。
Δpolicy=sθ+−sθ−；Δref=sref+−sref−；z=beta×(Δpolicy−Δref)；loss=−logsigmoid(z)，每pair scalar，积累后optimizer step。

同一个prefix的概率在差中抵消，课程允许用完整拼接序列的logprob差；mask实现则需用真实token边界，不能假定分别tokenize再拼接完全相同。padding不计loss；不按response长度平均来偷偷换目标。输入通常[1,T±]，logits[1,T±,V]，gather后[T±−1]；loss回到policy设备。reference跨设备的值可移动，不能detach policy。

| 训练指标 | 明确定义 |
| --- | --- |
| train/val DPO loss | 同版loss的每pair均值；验证no_grad，训练/验证分开 |
| handout policy classification accuracy | 1[Δpolicy>0]的验证均值；tie按不正确并单列；按handout文字口径作为checkpoint选择指标 |
| reference-adjusted reward accuracy | 1[z>0]均值，另名诊断，不能与上项混称；tie单列 |
| logprob/margin | sθ+、sθ−、sref+、sref−、Δpolicy、Δref、z；按来源/长度分层，保留sum及token长度 |
| 工程诊断 | lr、clip前后grad_norm（clip策略待冻结）、pairs/s、tokens/s、step时间、峰值allocated/reserved/设备显存 |

课程称implicit reward的classification却以chosen/rejected logprob说明；这里显式保存两种口径，P7确认checkpoint选用handout直述的policy口径，不能事后换更高的那个。初始policy=ref时z=0、loss=ln2，reward-adjusted margin没有偏好；policy margin未必0。

## 验证和GPU Gate

未来先 `uv run pytest tests/test_dpo.py::test_per_instance_dpo_loss`（官方fixture目标0.9104），再测试reference无梯度、policy有梯度、交换chosen/rejected、相同响应、EOS、padding/长短、跨设备、梯度积累尾组、恢复一致性；按项目规则分类跑GRPO回归，不改snapshot掩盖失败。

P8a 1–2 optimizer step smoke → P8b 固定seed0的最多2048个训练pair、按四来源分层的单次遍历pilot（有效batch64时最多32step；不足则记录实际步数，不循环凑数） → **重新批准P8c** 1epoch Full。RMSprop状态和两个模型分别预算；policy卡仍含权重/grad/optimizer/激活，不假定5090能容纳。reference BF16仅权重约2P bytes，加forward和logits临时空间。两卡路由不能当任意显存池。先实测最长chosen/rejected峰值再报价，不通过量化/LoRA自动绕开。

OOM、非finite、reference变化、mask/梯度/数量异常、无法恢复则停止。RMSprop过早state分配需在首step实测。最高val准确率checkpoint选择：建议同分取更低val DPO loss、仍同分取更早step；必须先冻结规则，不看benchmark选择。

## 下游与归档

P9用与SFT相同Alpaca外层及冻结generation，对四任务同IDs评估；Base/SFT/DPO使用同版Judge/固定reference，全部raw保留。分别看Alpaca/Safety收益、MMLU/GSM alignment tax、benign误拒和长度成本；训练accuracy改善不代表泛化改善。

保存两个初始化SHA、HH派生manifest、validationIDs、训练日志/曲线、best/final checkpoint身份、选择理由、raw/评分/review与checksum。时间估算用实际valid HH pair数、64有效batch、pilot每step/验证/保存耗时；课程1 B200 hr不是本项目保证。P8/P9 GPU预算与审批独立。
