# Qwen zero-shot baseline 下一Gate计划

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

状态更新2026-10-03：runner已实现，CPU dry-run和43项相关测试通过，SMOKE/PILOT已获批准。7B权重下载期间SSH失联；尚未启动模型加载。见[中断记录](interruption-20261003.md)。
沿用原四任务数据：MMLU test14042、GSM8K test1319、AlpacaEval805（既有GPT4 Turbo reference）、SimpleSafetyTests100。不得使用镜像eval替代。
Base使用官方任务prompt→zero_shot_system_prompt纯文本，禁止apply_chat_template。
配置文件固定temperature0/top_p1/seed0/n1/stop # Query:；512max_tokens、4096上下文、batch4、显存0.75为拟定工程参数，非官方指定值。CPU长度审查与pilot后冻结，超长hard stop，不静默截断。

获批后：实现独立runner与manifest→CPU dry-run→7B权重固定revision下载/校验→各benchmark1条smoke→各20条pilot（MMLU分层）→停下Review。
保存输入、formatted_prompt、raw输出、finish/stop reason、token counts、评分派生文件、软件/hardware/hash/checksum。合法empty/wrong/malformed/length照常保留评分；infra异常hard stop。
AlpacaEval/Safety先生成候选，不启动72Bjudge；因此这次pilot不能产出完整judge分数。
PostSFT/DPO按官方更换外层Alpaca模板，属于显式prompt confounder；任务/数据/解析器/judge保持一致。必要时另做同模板control，不能把所有变化都归因于训练。

Next task：恢复SSH并验收权重后继续已授权SMOKE/PILOT。遇GPU infra failure hard stop；本Gate归档后等待FULL批准。
