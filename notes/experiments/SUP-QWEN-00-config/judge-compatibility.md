# Qwen 72B Judge 兼容方案

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

配置/tokenizer/rendering READY；GPU inference与AlpacaEval真实标注/LC拟合 BLOCKED（未执行、无72B权重，需大显存）。

## AlpacaEval

官方Llama模板的system/user内容逐字抽取并保存 `judge-semantic-messages.json`；仅替换chat包装为固定revision Qwen tokenizer.apply_chat_template(add_generation_prompt=True)。包括原rubric中“list”与“Python dictionary”的措辞不一致也保留，不擅自改题。
新配置 `scripts/alpaca_eval_vllm_qwen2_5_72b_fn/` 独立命名；native `<|im_start|>...<|im_end|>`，assistant前缀，EOS151645；额外stop_token_ids=[151645,151643]沿用Qwen原生generation_config的两个结束ID；无Llama headers。is_chatml_prompt=false，已渲染模板不能重复apply_chat_template。
保持candidate与现有GPT4Turbo reference、官方ranking_parser；temp0/top_p1/maxnew100、context7000、TP2、batch900沿用原配置；seed0、revision/tokenizer_revision固定、generation_config=vllm排除模型默认采样干扰。实查alpaca-eval0.6.6源码，batch_size会被传入LLM的max_num_seqs，故900会影响调度/显存；这只是继承配置，下一硬件pilot必须验证，必要调整另建版本。
下一Gate先用无模型mock检查ranking格式/invalid/tie/order与annotator发现，再大显存1条judge smoke，记录raw/parsed/invalid，full计算winrate和length-controlled winrate。
使用 `alpaca_eval --annotators_config scripts/alpaca_eval_vllm_qwen2_5_72b_fn/configs.yaml ...` 前须核实库版本路径解析/registry行为。本轮没有执行此命令，不能称72B端到端ready。

## Safety

原rubric通过AST读取字符串，避免import原脚本引入vLLM；保存semantic messages和Qwen rendered placeholder prompt。
未来Qwen入口显式AutoTokenizer(revision=judge_tokenizer_revision)，LLM(revision=judge_revision,tokenizer_revision=...,generation_config='vllm')；nativechat、temp0/top_p1/max16/context6144。
同时输出official_compat_safe（复现旧非true→safe逻辑）和strict_label=True/False/invalid、raw文本。正式主安全指标需预先定义分母：有效safe/全部N，invalid单列；valid-only比例只能作为辅助。invalid>0不通过Review Gate，保留raw后检查infra/parser，不自动重采样漂亮分数。
与原实现相比这是无效输出处理审计增强；必须与模型替换一起披露，不能隐瞒evaluator行为差异。

## 证据

CPU roundtrip验证每段语义内容完整保留、native前缀/EOS、无Llama tokens；实际logits/判断能力和跨judge标尺不能由tokenizer检查证明。
不加载或下载72B权重。参数json、rendered模板及源文件SHA归档。

Next task：在独立获批的大显存Judge Gate实现runner和invalid处理，先mock+1条再pilot。
