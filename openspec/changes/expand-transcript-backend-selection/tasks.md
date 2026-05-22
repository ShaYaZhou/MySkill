## 1. 文档与契约更新

- [x] 1.1 更新 `video-transcript/SKILL.md`，说明无人工字幕时必须进入 provider 选择 checkpoint，并列出 `--transcribe-provider` / `--transcribe-mode` 的常用入口。
- [x] 1.2 重写 `video-transcript/references/BACKENDS.md`，增加 provider registry 表、能力类型、内置 provider、代理 provider 和不支持直接转写的说明。
- [x] 1.3 更新 `video-transcript/references/CHECKS.md`，加入无人工字幕 checkpoint 模板、用户确认规则、快速推荐规则和拒绝外发后的退化菜单。
- [x] 1.4 更新 `video-transcript/references/OUTPUT-CONTRACT.md`，加入 provider/mode/model、selection source、media upload、proxy 和 unsupported/blocked 字段。
- [x] 1.5 更新 `video-transcript/references/TROUBLESHOOTING.md`，覆盖 DeepSeek、GLM、Gemini、Claude、OpenAI-compatible、custom-proxy 的常见配置和能力边界问题。
- [x] 1.6 更新文档，说明第一次选择默认 API 凭据时只保存 provider、mode、环境变量名、模型和 endpoint label，不保存真实 key。

## 2. Provider Registry 与 CLI

- [x] 2.1 在 `video-transcript/scripts/transcript.py` 中新增 provider registry 数据结构，覆盖 OpenAI、Moonshot/Kimi、MiniMax、DeepSeek、GLM、Gemini、Claude、OpenAI-compatible 和 custom-proxy。
- [x] 2.2 新增 CLI 参数：`--transcribe-provider`、`--transcribe-mode`、`--transcribe-base-url`、`--transcribe-endpoint`，并明确它们与旧 `--transcribe-backend` 的优先级。
- [x] 2.3 实现旧 backend 到 provider/mode 的兼容映射，确保 `openai`、`kimi-video`、`minimax-api` 的现有用法继续可用。
- [x] 2.4 实现 provider 参数冲突检测；当旧 backend 与新 provider/mode 指向不同方案时，报错并要求用户明确选择。
- [x] 2.5 对只支持文本或缺少必要 endpoint 的 provider 返回 `unsupported-direct`、`requires-proxy` 或 `blocked`，不得进入媒体上传执行路径。
- [x] 2.6 增加用户级默认 provider 偏好读取、写入、清除和本次忽略逻辑；默认偏好不得写入 skill 仓库或安装包。

## 3. 后端执行与代理适配

- [x] 3.1 将现有 OpenAI audio transcription 执行路径接入 registry 的 `audio-asr` adapter。
- [x] 3.2 将现有 Moonshot/Kimi video transcription 执行路径接入 registry 的 `video-understanding` adapter，并记录非专用 ASR 风险。
- [x] 3.3 将现有 MiniMax API transcription 执行路径接入 registry 的 `audio-asr` 或配置声明的实际 adapter。
- [x] 3.4 增加 OpenAI-compatible/custom-proxy adapter 的最小实现，支持用户配置 endpoint、model、认证环境变量和请求格式；缺配置时明确 blocked。
- [x] 3.5 为 DeepSeek、GLM、Gemini、Claude 设置默认 registry 条目；能通过兼容接口或代理执行时接入 adapter，否则显示 requires-proxy/unsupported。

## 4. Checkpoint、Dry-run 与 Doctor

- [x] 4.1 更新 `--doctor` 输出，列出每个 provider 的 key 存在性、endpoint 配置、能力类型、阻塞原因和不确定项，且不泄露 secret。
- [x] 4.2 更新 `--dry-run`，在无人工字幕时输出候选 provider、推荐默认、是否下载/上传、可能分片、成本/隐私/区域风险和退化选项。
- [x] 4.3 增加 agent-facing checkpoint 文案，确保用户可以选择 OpenAI、Moonshot/Kimi、MiniMax、DeepSeek、GLM、Gemini、Claude、代理或跳过。
- [x] 4.4 当用户要求“用推荐方案”时，按可见配置、准确率、隐私和成本生成单一推荐，并在执行前说明 provider/mode 和是否上传媒体。
- [x] 4.5 大型播放列表缺人工字幕时，checkpoint 必须包含预计条目数、成本风险、分批策略和只处理部分视频选项。
- [x] 4.6 当已存在可用默认 provider 时，普通无人工字幕转写不得再次因 provider 选择打断用户；只对大型播放列表、登录/cookie、覆盖、默认值失效等独立风险 checkpoint。

## 5. Metadata、Summary 与安全脱敏

- [x] 5.1 更新 `metadata.json` 写入逻辑，记录 `transcribe_provider`、`transcribe_mode`、`provider_capability_type`、`provider_selection_source`、`media_downloaded`、`media_uploaded`、`proxy_used` 和 `selection_warnings`。
- [x] 5.2 更新 `run-summary.json` 写入逻辑，记录 blocked/skipped/requires-proxy/unsupported 的 provider 状态和原因。
- [x] 5.3 增加 endpoint 脱敏工具，只记录 host、provider id、配置变量名或 endpoint label，不写入带鉴权 query 的完整 URL。
- [x] 5.4 扩展示例文件，新增包含 provider/proxy 字段的 metadata 和 run-summary 示例。
- [x] 5.5 确认日志、summary、metadata、manifest 和完成汇报都不输出 API key、cookie、token、session value 或私密 HTML。
- [x] 5.6 在 metadata 或 summary 中记录 `default_provider_used`、`default_credential_label`、`auth_env` 和默认选择来源，且只记录脱敏信息。

## 6. 验证

- [x] 6.1 运行 `py -3 .\scripts\validate_repo.py`，修复新增文档、JSON 示例和 Python 语法问题。
- [x] 6.2 运行 `python video-transcript/scripts/transcript.py --doctor`，确认 provider 可用性展示完整且脱敏。
- [x] 6.3 使用 `--dry-run` 对有人工字幕和无人工字幕的示例 URL 分别验证 checkpoint 预览差异。
- [x] 6.4 验证旧参数 `--transcribe-backend openai|kimi-video|minimax-api` 仍能映射到对应 provider/mode。
- [x] 6.5 将更新后的 `video-transcript` 重新安装到 Claude、Codex、Cursor、Mavis，并记录验证结果。
- [x] 6.6 验证首次选择默认 provider、后续自动复用、显式 provider 覆盖默认值、清除默认值、默认值失效回到 checkpoint 等路径。
