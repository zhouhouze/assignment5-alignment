# SFT mirror 数据验收

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

## 结论

下载/校验完成；sample_train结构验收PASS；**完整train/test准入BLOCKED**：train22条、test2条不满足非空要求。原文未修改、未过滤、未训练。

Repo：`garg-aayush/sft-cs336-assign5-datasets`；revision：`ac710ef808346bf458d7b093bfe4586cb15699d9`。
仅下载指定三份数据；额外读取两份README作为来源证据，没有加载mirror eval或sft-reason数据。

Third-party mirror of the Stanford CS336 safety-augmented UltraChat 200k single-turn dataset; exact bitwise equivalence to the Spring 2026 Modal copy has not been independently verified.

镜像README历史下载链接年份为2024；2026 Modal copy SHA未知。来源与字节等价性分开。

| Split | 行数 | bytes | malformed | 空prompt | 空response | 重复对象 / 精确pair / 重复prompt |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| train | 210,348 | 532,421,064 | 0 | 1 | 21 | 0 / 0 / 4 |
| test | 23,110 | 58,872,258 | 0 | 0 | 2 | 0 / 0 / 0 |
| sample_train | 1,000 | 2,492,043 | 0 | 0 | 0 | 0 / 0 / 0 |

三份文件无缺失键、非字符串或非object；valid非空记录分别210326/23108/1000。
重复对象以canonical JSON计数，pair以未清洗的(prompt,response)计数，prompt按未清洗字符串计数，均为首条以外出现次数。
train/test共有精确pair=0，共有prompt=0；sample1000条全部存在于train、不在test。此检查不证明不存在语义近重复或benchmark污染。

## SHA256

- train: `3b72228a7976079a5c5a30249fd3289179ad01006cbb67d15c7c366d4fd25913`
- test: `ce84dd834a7bbfc622cb3b50dc6c233e7dd91e002fd84f7cf86f70762a2c9ed9`
- sample_train: `b26bbe382793889ccb397e7c8afdf64ad3e52f0109d191e66c424587fba596df`

## 长度分布

以Unicode字符计、所有字符串记录含空值；p50/p90/p99采用排序后floor((n-1)*q)。完整值与每条错误行号见 `acceptance-v2/dataset-acceptance.json`。旧acceptance仅统计非空记录长度，保留为初次审计，不作为最终验收口径。
train prompt p50/p90/p99/max=478/2351/5430/14884，response=1309/3484/5526/11013。
test prompt=483/2415/5420/14888，response=1310/3484/5537/6713。

## 不修改raw的处理建议

先核查24条错误行是否原始来源缺损。建议后续经明确确认采用版本化的派生数据过滤规则，仅剔除空字段，保存excluded IDs、reason、source SHA、derived SHA与前后计数；不要补写答案，也不改写raw。
本轮仅建议，无清洗产物。四个重复prompt可能对应不同response，不能未经审阅删除。随机样本质量问题保留为数据偏差证据，不自动全量筛选。

## Tokenization / packing CPU验收

sample1000篇：519206 tokens（含每篇EOS），平均519.206；p50/p90/p99/max=460/960/1274/2442。
512长度下算术可形成1014组input/next-token target；519168 token-pairs，37枚尾部余数，利用率99.9929%。保留lookahead，不能把统计误写成已实现或通过官方Dataset。
full train/test token总量：尚未计算；准入解决后在正式运行manifest补记，不按字符比例猜。

## 复现与存储

raw位于本地`data/qwen-sft-mirror/sft-instruct/`，不入Git；21项完整小文件+数据inventory和SHA在Git。
执行 `python scripts/restore_qwen_preflight_assets.py` 从固定commit逐项恢复并校验；已有文件hash不符hard stop，不覆盖。
总计三份593785365 bytes（约566.28 MiB），模型权重零下载。

Next task：人工确认数据审计及空字段方案后才能进入完整SFT；baseline独立数据不受此阻塞。
