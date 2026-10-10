# 全参数 SFT 训练实验设计

状态：NOT RUN；补充[既有训练计划](training-plan.md)，以2026 handout §4与官方tests为约束。假设：高质量指令示范改善任务完成/格式与助手行为，但知识、数学及正常请求拒答可能回退。loss下降只是学习训练分布的证据。

## 固定设置与待定项

Qwen2.5-7B固定revision；全参数；BF16；FlashAttention2；packed L=512；effective batch=32；1 epoch；AdamW lr=2e-5；cosine；warmup=3%；weight_decay=.1；clip_grad_norm=1.0。自实现训练loop，不用Trainer/LoRA/QLoRA/量化自动替代。

seed建议0。AdamW betas/eps、参数组衰减规则、state/master/gradient dtype、foreach/fused、microbatch/grad accumulation、activation checkpointing与分布式方案在P3/P4记录并批准，不能隐藏框架默认值。主checkpoint建议完整1epoch最终保存，validation loss仅监控；如改为lowest-val选择必须事前批准，不用正式benchmark挑checkpoint。

## P3 CPU正确性（未来执行）

| 项目 | 不变量/最小证据 |
| --- | --- |
| Dataset | docstring与tests/test_data.py的fixture逐项一致；先shuffle文档再串接packing；EOS151643只按规范附加 |
| Packing/labels | 输入tokens[t:t+512]、标签tokens[t+1:t+513]；只shift一次；跨文档EOS保留，长文档连续分块，不逐文截断到512 |
| Shape/dtype/device | input/labels为[B,512] long；logits[B,512,V]；CE scalar；模型输入设备一致；B最后一批可不足 |
| Loss | 官方full-token next-token CE，prompt token也参与；不悄悄改成completion-only；直接用.logits做对齐CE，不能将已shift标签传给再次shift的HF内置loss |
| Mask | EOS与PAD相同时按真实padding位置mask，不按token值全屏蔽EOS；连续完整packing通常不需要pad |
| Accumulation | 与等效大batch梯度对照；不足32的尾组按实际token数归一化；clip在step前仅一次；scheduler按optimizer step计 |
| Validation | eval/no_grad，确定固定顺序；总NLL/有效token总数，不平均不同大小batch的mean；不让validation进入梯度 |
| Resume | weights/optimizer/scheduler/RNG/data order/cursor/step全部恢复；在optimizer step边界保存，续训与连续运行toy对照；仅能加载weights不等于精确续训 |

窄测试未来按组件执行：`uv run pytest tests/test_data.py::test_packed_sft_dataset` → batching测试 → `uv run pytest tests/test_data.py`；小CPU模型验证loss/梯度/恢复。依项目规则运行并分类 `uv run pytest tests/test_grpo.py`，独立Supplement旧19个NotImplemented不能伪装成新回归或改tests抹平；新增失败必须解释。当前三个Supplement核心接口未实现，不能启动贵GPU训练。

## 数学、规模与资源

CE = −Σ有效位置 log pθ(next_token | prefix) / 有效位置数。若全体含EOS token数为T，完整packed块 N=floor((T−1)/512)，optimizer steps≈ceil(N/32)，末组必须正确归一化并记录tail。

已有sample1000的T=519206，N=1014，1epoch约32次optimizer step；不能声称这个数据能单epoch做50个step。P4建议1–2 step smoke，然后固定该样本1epoch pilot并记录尾组：ceil(1014/32)=32步。若要更长pilot另批更大subset，不能默默重复epoch。Full T尚未统计，时间不能从文件字节直接推出。

显存按实际参数数P算：BF16参数2P、梯度若BF16为2P；AdamW两份moment若BF16共4P，若FP32共8P；可选FP32 master再加4P。仅这部分约8P/12P/16P bytes，具体实现需检查实际dtype，不宣称必然18bytes/参数。另有激活、151936词表logits、临时optimizer buffer、通信和CUDA缓存。若P约7.6B，静态最低示例8P约60.8GB十进制，FP32 moments的12P约91.2GB，尚未加激活，因此单80GB不保证足够；5090 32GB不作为传统全参AdamW默认设备。

候选：先对大显存单卡做1-step实测；不够再审批FSDP/ZeRO状态分片，记录其数值/通信变化。DDP完整复制不减少每卡状态，不用“2卡等于显存相加”预算。不得未经批准CPU/offload、改精度或降为LoRA。DPO也需独立预算。

## P4/P5 验收与输出

smoke检查finite loss/grads、更新生效、state dtype、峰值allocated/reserved和nvidia-smi、恢复一致性；pilot看warmup/step稳定性、val loss、tokens/s、step p50/p95、checkpoint写入耗时。OOM/NaN/梯度缺失/数据hash变更/无法恢复立即停，保留失败证据，不擅自调参继续Full。

Full时间=加载+数据预处理+实际step数×稳态step秒+validation+checkpoint+归档；报价=各设备小时×单价+存储/传输。P4后给低/中/高区间与余量，当前NOT MEASURED。课程3 B200 hrs是不同模型环境参考，不能当Qwen承诺。

保存train/val loss、lr、grad_norm（clip前后）、有效tokens、throughput、VRAM、epoch/cursor、checkpoint manifest及曲线；正式weights/tokenizer及resume states进持久存储，SHA登记，基础模型可下载但训练权重不可从base恢复。P5结束只申请P6，不自动评估。
