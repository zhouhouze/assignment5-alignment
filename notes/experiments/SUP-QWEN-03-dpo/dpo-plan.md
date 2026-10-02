# Qwen DPO 配置与准入

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

BLOCKED / NOT STARTED。Policy与frozen reference必须初始化于同一个已验收Qwen SFT checkpoint；路径/revision当前null，不以Base替代。
数据仍为既有Anthropic HH，完成单轮过滤、chosen/rejected审读、固定seed划分约200验证样本；禁止拿镜像SFT prompt/response冒充偏好对。
规划effective batch64、beta0.1、lr1e-6、RMSprop、epoch1、gradient accumulation；记录train/val loss、preference accuracy、chosen-rejected margin、gradnorm。
本轮DPO官方测试NotImplemented属于未到阶段，不为全绿提前实现。

Next task：完成SFT和PostSFT评估后，再审核DPO数学、response masking与reference冻结，并通过unit tests后才开硬件smoke。
