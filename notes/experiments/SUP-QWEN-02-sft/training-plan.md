# Qwen SFT 分阶段计划

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

正式SFT BLOCKED：24条跨split空字段需处理决策、人工审读pending、PackedSFTDataset/batching未实现、训练硬件未验证。
保持官方Alpaca模板、原生EOS、512上下文、全token causal LM；BF16、AdamW lr2e-5、cosine、warmup3%、wd0.1、gradclip1、effective batch32、epoch1。
不得用Trainer、LoRA/QLoRA、量化或CPU offload替代目标。microbatch/gradaccum在硬件smoke后显式固定，总batch=32。
当前sample CPU模板/tokenization与packing算术统计已完成，不等于训练数据核心实现完成。下一SFT Gate先独立实现Dataset/batching并通过官方Llama fixtures与Qwen额外sanity，再sample数据pipeline smoke，之后获批准进行10–50optimizer steps，最后才full。
formal full需要完整train/test token统计、选定checkpoint元数据、loss/val/lr/grad/throughput/VRAM曲线、原始日志与hash。先建议80GB级显存；32GB不承诺full BF16 optimizer状态可容纳。

Next task：先完成baseline Gate；不要跨过数据和硬件阻塞自动训练。
