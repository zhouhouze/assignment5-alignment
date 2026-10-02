# SFT processed dataset来源调查（未训练、未替换数据）

日期2026-10-02。官方Spring2026 Supplement §4.1指定：课程Modal `cs336-a5-supplement`（environment `cs336-shared-data`）中的 `data/safety_augmented_ultrachat_200k_single_turn/{train,test}.jsonl.gz`。每行prompt/response；test文件作为课程SFT开发验证集，不是GSM8K测试集。

## 查到的证据

- 本地与新智星云均无该预处理数据；未挂载课程Modal共享卷，没有对其权限作成功声明。本地也未发现标准Modal配置文件或环境认证变量，未发起共享卷认证请求。
- 官方仓库树API返回`c2734a26308710949fe13226960a1e8cece94b7e`，未发现名为ultrachat/safety_augmented/preprocess的数据或处理入口；搜索结果仅有SFT模板/测试夹具。该树结果不能证明课程其他位置没有处理脚本。
- [UltraChat-200K官方卡片](https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k)是含messages的原始来源之一，包含train_sft/test_sft及gen splits；本次metadata revision=`8049631c405ae6576f93f445c6b8166f76f5505a`。未下载parquet，未取得原始文件SHA256。
- [SafetyTunedLlamas官方仓库](https://github.com/vinid/safety-tuned-llamas)提供`data/training`中的instruction-output文件；本次revision=`36a4b8d5c2177ed165bf61f59b590161394f7f12`。目录中有不同混合规模文件及`safety_only_data_Instructions.json`。并未确认课程选用哪一个，未下载或混合。
- API来源、文件名与上游声明大小保存在`sft-sources.json`；API revision不是数据内容SHA256，不混称。

## 恢复优先级

1. 首选获得课程共享卷的正式访问途径或由用户提供官方导出文件，校验来源、大小、SHA、行数/schema、train/val分离，再进入20–50例审计。
2. 如果课程数据不可获得，先申请批准重建替代版；固定原始source revision、选定safety文件、对话转单轮方式、配比、过滤/去重/截断规则、split seed及污染检查。产物另命名，报告明确非课程原始预处理数据。
3. 不在本轮擅自登录/计费使用Modal，不以随机镜像或原始UltraChat替代，不进入Gate C的数据质量结论。

当前结论：**来源定位完成，processed文件内容及SHA仍UNKNOWN，SFT data readiness=NO**。这不妨碍独立完成baseline parser，但阻止忠实复现SFT。
