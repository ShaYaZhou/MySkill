## 背景

`video-transcript` 当前策略是人工字幕优先，缺字幕时按可见 API key 自动选择 OpenAI、Kimi/Moonshot 或 MiniMax。这个策略适合“已有单一 key、用户接受默认外发”的轻量场景，但当多个 key 同时存在，或用户更偏好国内 endpoint、代理、自托管网关、本地工具时，按环境变量顺序静默选择就不够透明。

无人工字幕后的路径通常会触发媒体下载、API 上传、费用、区域和隐私风险。新设计应让第一次选择变成明确用户决策，并把这个决策保存成非敏感默认偏好：以后再遇到同类转写任务时，除非用户显式改选，agent 和脚本可以直接使用这个默认 provider/凭据，避免每次重复问。

新需求还要求后端不再局限于 OpenAI、Moonshot、MiniMax，而是能覆盖 DeepSeek、GLM、Gemini、Claude 和代理方案。不同厂商的能力并不等价：有的提供专用 ASR，有的支持多模态视频/音频理解，有的只支持文本或 OpenAI-compatible chat/completions。设计必须表达能力边界，不能把所有 LLM 都伪装成音频转写服务。

## 目标

- 没有人工字幕时，提供一个用户可审阅的后端选择 checkpoint。
- 第一次需要 API/代理转写且没有显式选择时，让用户选择默认 provider/API 凭据；后续默认复用该选择。
- 默认偏好只记录 provider、mode、模型、endpoint label、环境变量名或凭据标签，不记录真实 secret。
- 以 provider registry 描述后端能力、认证、endpoint、模型、请求类型、风险和降级路径。
- 支持内置 provider：OpenAI、Moonshot/Kimi、MiniMax、DeepSeek、GLM、Gemini、Claude。
- 支持代理 provider：OpenAI-compatible endpoint、自定义转写 endpoint、本地/企业网关和用户自带 CLI/API。
- 在 dry-run、doctor、metadata、run-summary/run-manifest 中记录用户选择、默认来源、后端能力、模型、脱敏 endpoint、外发风险和不确定项。
- 保持人工字幕路径不变：有人工字幕时不触发后端选择。

## 非目标

- 不在本 change 中保证每个厂商都有官方原生 ASR endpoint。
- 不绕过厂商文件大小、地区、账号权限、模型能力或安全策略限制。
- 不把平台自动字幕默认纳入候选，除非用户明确接受。
- 不把 API key、cookie、token、session value 或完整敏感 endpoint 写入任何日志、manifest 或默认偏好文件。
- 不为所有 provider 引入重量级 SDK；优先使用标准 HTTP/OpenAI-compatible adapter 和清晰的 blocked/unsupported 状态。
- 不让默认 provider 选择覆盖其它独立风险检查点；大型播放列表、登录/cookie、覆盖已有产物等风险仍按对应规则处理。

## 设计决策

### 1. 使用 provider registry，而不是固定 fallback 链

新增一个 provider registry，至少包含：

- `id`：稳定标识，例如 `openai`、`moonshot`、`minimax`、`deepseek`、`glm`、`gemini`、`claude`、`openai-compatible`、`custom-proxy`。
- `display_name`：面向用户的中文名称。
- `capability_type`：`audio-asr`、`video-understanding`、`audio-to-llm`、`openai-compatible`、`custom-proxy`、`unsupported-direct`。
- `auth_env`：认证环境变量名，不包含真实值。
- `base_url_env` / `endpoint_env`：可选 endpoint 配置。
- `default_model_env` / `default_model`：模型配置。
- `requires_media_download`、`uploads_media`、`paid_or_quota_risk`、`region_risk`。
- `recommended_when` 和 `limitations`。

理由：provider registry 可以让文档、dry-run、doctor 和实际执行共享同一组事实，避免后端扩展时到处散落硬编码。替代方案是继续扩展旧的“按环境变量顺序 fallback”函数，但那会让用户选择、代理方案和能力边界越来越模糊。

### 2. 将 `backend` 与 `provider` 分开

保留兼容性的 `--transcribe-backend`，但新增更明确的概念：

- `--transcribe-provider`：选择厂商或代理，如 `openai`、`gemini`、`claude`、`custom-proxy`。
- `--transcribe-mode`：选择执行方式，如 `audio-asr`、`video-understanding`、`proxy-asr`、`llm-from-extracted-audio`。
- `--transcribe-model`：模型名。
- `--transcribe-base-url` / `--transcribe-endpoint`：通用 endpoint 覆盖。

兼容映射：

- `--transcribe-backend openai` 等价于 `provider=openai, mode=audio-asr`。
- `--transcribe-backend kimi-video` 等价于 `provider=moonshot, mode=video-understanding`。
- `--transcribe-backend minimax-api` 等价于 `provider=minimax, mode=audio-asr` 或 registry 中配置的实际模式。

理由：`backend` 是旧脚本实现名，`provider/mode` 更适合表达 DeepSeek、GLM、Gemini、Claude 和代理。旧参数继续可用，降低迁移成本。

### 3. 第一次选择写入非敏感默认偏好

当没有人工字幕，且用户没有通过 CLI 参数或当前对话明确选择 provider/mode，且本机没有已保存默认 provider 时，agent 必须展示 checkpoint，并要求用户选择一个默认 API 凭据。这里的“API 凭据”指：

- provider id；
- mode；
- 认证环境变量名，例如 `MINIMAX_API_KEY`；
- 可选模型环境变量或模型名；
- 可选 endpoint label 或脱敏 host；
- 选择来源和更新时间。

默认偏好不得保存真实 key 值。建议使用用户本机配置文件，例如平台配置目录下的 `video-transcript/provider-default.json`，或等价的用户级非敏感配置。该文件不应进入 skill 仓库、不应随安装包分发。

示例：

```json
{
  "default_provider": "minimax",
  "default_mode": "audio-asr",
  "auth_env": "MINIMAX_API_KEY",
  "model_env": "MINIMAX_ASR_MODEL",
  "endpoint_label": "minimax-cn",
  "selection_source": "user-confirmed-default",
  "updated_at": "2026-05-22T00:00:00Z"
}
```

理由：用户明确要求“第一次选择一个作为默认 API key，之后除非显式选择，否则可以直接调用”。保存 provider/环境变量名可以满足复用诉求，同时避免 secret 落盘。

### 4. 后续默认调用只跳过 provider 选择，不跳过其它风险检查

选择优先级：

1. 当前命令显式传入的 `--transcribe-provider` / `--transcribe-mode` / endpoint。
2. 当前对话中用户明确指定的 provider 或代理。
3. 用户级默认 provider 偏好。
4. 第一次无默认时的 checkpoint 推荐。

如果默认偏好存在且对应 key/endpoint 可见，普通无人工字幕转写可以直接调用该 provider，不再因为 provider 选择本身停顿。若出现大型播放列表、登录/cookie、覆盖成功产物、endpoint 区域不明、默认 key 缺失、provider 能力不支持、用户要求换方案等独立风险，仍按对应 checkpoint 处理。

理由：这样既满足“后续直接调用”的效率要求，也不会让默认 provider 成为绕过其它安全边界的通行证。

### 5. 无人工字幕时 checkpoint 优先于环境变量自动外发

当 `choose_original_subtitle()` 找不到人工字幕，且没有显式 provider、没有本机默认偏好时，agent 必须展示 checkpoint：

- 推荐默认方案和原因。
- 可用 provider 列表：已配置、缺 key、需代理、能力不支持。
- 是否下载音频/视频。
- 是否上传到 API 或代理。
- 可能费用、隐私、地区、文件大小和模型能力风险。
- 是否把本次选择保存为默认 provider。
- 退化选项：用户上传字幕/音频、只保存 metadata、改用本地工具、跳过。

理由：没有字幕后的路径通常高成本且会外发媒体。自动选择 API key 虽然方便，但第一次不应替代用户知情选择。

### 6. 对 DeepSeek、GLM、Gemini、Claude 使用能力标记和适配器

内置 registry 可以列出 DeepSeek、GLM、Gemini、Claude，但必须根据配置和实际能力选择执行路径：

- 如果 provider 暴露 OpenAI-compatible endpoint 且代理支持音频转写，则走 `openai-compatible` 或 `custom-proxy` adapter。
- 如果 provider 支持视频/音频多模态理解，则走 `video-understanding` 或 `audio-to-llm`，并在结果中标明“理解式转写，非专用 ASR”。
- 如果 provider 只支持文本生成，直接标为 `unsupported-direct` 或 `requires-proxy`，不允许直接接受音频文件并宣称转写成功。

理由：这能满足“支持更多 API”的入口诉求，同时避免错误承诺。具体 API 能力变化频繁，registry 应允许用户覆盖 endpoint/model，并通过 doctor/dry-run 暴露不确定性。

### 7. 记录脱敏决策，而不是记录 secret

metadata/summary 新增字段建议：

- `transcribe_provider`
- `transcribe_mode`
- `transcribe_model`
- `provider_capability_type`
- `provider_selection_source`：`user-confirmed-default`、`saved-default`、`cli-explicit`、`conversation-explicit`、`dry-run-confirmed`。
- `default_provider_used`
- `default_credential_label`
- `auth_env`
- `media_downloaded`
- `media_uploaded`
- `endpoint_label` 或脱敏 endpoint host，不含 key/query。
- `proxy_used`
- `selection_warnings[]`
- `unsupported_reason`

理由：后续排错需要知道“用了什么方案”，但不能泄露 key、token、cookie 或私密 URL。

## 风险与取舍

- 风险：厂商能力和 API endpoint 变化快。缓解：registry 支持环境变量覆盖；doctor/dry-run 标记不确定项；无法验证时显示 `blocked` 或 `requires-proxy`。
- 风险：用户看到太多 provider 选项会困惑。缓解：checkpoint 只展示推荐默认、可用项和不可用原因，完整 provider 列表放 reference。
- 风险：代理方案可能转发到未知服务。缓解：必须显示 base URL/host、是否外发媒体、隐私风险和用户确认；manifest 只记录脱敏 host。
- 风险：通用 LLM 生成的“转写”可能不逐字。缓解：mode 明确标为 `video-understanding` 或 `audio-to-llm`，完成汇报提示精确度风险。
- 风险：新参数与旧 `--transcribe-backend` 混用。缓解：定义优先级为 CLI 显式 provider/mode > 旧 backend 映射 > 用户默认偏好 > 首次 checkpoint；冲突时报错或要求确认。
- 风险：默认 provider 偏好被误解为保存真实 key。缓解：文档、示例和验证脚本都必须禁止真实 secret 落盘，只允许记录 env var 名称或凭据标签。

## 迁移计划

1. 更新 `BACKENDS.md` 和 `CHECKS.md`，把无人工字幕后的阶段门改为 provider 选择 checkpoint，并加入首次默认 provider 选择。
2. 更新 `transcript.py` CLI，新增 provider/mode/base-url/endpoint 参数，同时保留旧 `--transcribe-backend`。
3. 实现 provider registry、默认 provider 偏好读取/写入、doctor/dry-run 展示和旧 backend 兼容映射。
4. 先将现有 OpenAI、Moonshot/Kimi、MiniMax 迁入 registry，确保现有流程不退化。
5. 增加 DeepSeek、GLM、Gemini、Claude、OpenAI-compatible、custom-proxy 的 registry 条目；能直接执行的走 adapter，不能直接执行的显示 requires-proxy/unsupported。
6. 更新 metadata/run-summary 示例和验证脚本，确保不记录 secret。
7. 安装到 Claude/Codex/Cursor/Mavis 后跑离线验证和 `--doctor`。

回滚方式：保留旧 `--transcribe-backend` 参数和现有三后端实现；如果 provider registry 或默认偏好出现问题，可以先把新 provider 标为 blocked，仅保留旧映射可用。

## 待确认问题

- DeepSeek、GLM、Gemini、Claude 是否需要在首版内置具体官方 endpoint，还是只通过 OpenAI-compatible/custom-proxy 接入并等待用户配置？
- 是否新增本地 ASR provider，例如 `faster-whisper` 或用户自带 CLI，作为“不外发媒体”的推荐选项？
- checkpoint 是否应在 CLI 脚本中实现交互式选择，还是由 agent 负责展示选择后再传入显式参数？
- 默认 provider 偏好文件的最终位置使用平台配置目录，还是使用 `~/Documents/video-transcripts/.config/`？
