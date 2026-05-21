# 转写后端策略

`video-transcript` 的默认策略是先用确定性较高、成本最低的来源，再逐步升级到需要下载、上传或付费的后端。

## 默认顺序

1. 人工字幕
2. OpenAI audio transcription
3. Kimi video transcription
4. MiniMax API transcription

不要默认使用平台自动生成字幕。只有用户明确接受，或后续单独扩展策略时，才把自动字幕作为候选。

## 阶段门

以下情况必须先向用户说明计划并等待确认：

- 使用 `--cookies-from-browser` 或任何浏览器登录态。
- 没有人工字幕，需要下载音频或视频并上传到转写 API。
- 选择付费后端或隐私敏感上传路径。
- 播放列表较大，可能产生大量文件或费用。
- MiniMax endpoint、key 区域或模型不明确。

## 后端配置

OpenAI:

- `OPENAI_API_KEY`
- 默认模型：`gpt-4o-mini-transcribe`
- 高准确率可选：`gpt-4o-transcribe`

Kimi / Moonshot:

- `MOONSHOT_API_KEY`
- 默认模型：`kimi-k2.6`
- endpoint 自动探测 `.ai` 与 `.cn`；已知 endpoint 可用 `MOONSHOT_BASE_URL` 指定。

MiniMax API:

- `MINIMAX_API_KEY`
- `MINIMAX_BASE_URL`
- `MINIMAX_TRANSCRIBE_URL`
- `MINIMAX_ASR_MODEL`
- 默认 China endpoint：`https://api.minimaxi.com/v1`
- Global endpoint 常用：`https://api.minimax.io/v1`

## 数学公式

所有 API 后端都应使用包含数学保留规则的 prompt：

- 行内公式：`$...$`
- 块级公式：`$$...$$`
- 保留变量名、单位、上下标、定理名和推导上下文。

如果公式识别风险高，在完成汇报中标为风险，不要把不确定公式描述为已验证。
