# O2 Standard On-Policy GRPO — 软件准备阶段

日期：2026-09-14。

本轮目标：恢复正式云端 Git checkout、按锁文件验证环境、逐个实现七个标准 GRPO 组件并完成 CPU 验证。

架构：GSM8K question → r1_zero → rollout（未来阶段）→ reward → group advantage → tokenization → log_probs → sequence loss → 累积梯度 → 一次 optimizer step → 权重同步（未来阶段）。本轮只实现中间 CPU 组件。

完成：Git clone 和 O1 祖先验证；CUDA matmul；核心依赖导入与 FlashAttention kernel；正式 GRPO 模块与薄 adapter；七个 targeted tests；本地和云端完整 CPU tests；手算/梯度/累积 sanity checks；HF training-side 与 vLLM rollout-side 两个互斥的单卡 smoke。

禁止且未执行：OLMo/vLLM 双模型启动、one-step GPU 端到端 smoke、50/200-step 训练、4 seeds、调参和所有算法 variants。未重新运行 O1。

当前分支 learning/grpo-foundations，基线 2267287；本轮完成后创建独立软件 checkpoint。旧云端副本和本地已有笔记保留。

详细证据：environment.md、component-tests.md、component-sanity-results.json、full-cpu-test-output.txt、single-gpu-smoke.md 及 `artifacts/O2-standard-grpo/single-gpu/`。

下一步：由用户决定准备双 GPU 硬件；完成学习检查后另行授权端到端 smoke。

Software ready for Two-GPU One-Step Smoke: YES。当前硬件仍不 ready：只有一张 GPU，且没有端到端闭环验证。
