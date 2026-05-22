## 背景

当前 `video-transcript` 的真实行为是：优先使用人工字幕；没有人工字幕时才进入 API 转写路径。脚本已支持 `--transcribe-backend auto|openai|kimi-video|minimax-api`。其中 `auto` 会按可见环境变量自动选择：

```text
OPENAI_API_KEY 存在 -> OpenAI audio transcription
MOONSHOT_API_KEY 存在 -> Kimi video transcription
MINIMAX_API_KEY 存在 -> MiniMax API transcription
```

这个策略适合轻量自动化，但在没有人工字幕时会触发媒体下载、API 上传、费用和隐私外发风险。当前文档虽然要求 agent 在高风险路径前做 checkpoint，脚本层和配置层仍缺少明确的“用户选择哪个转写方案、是否把它作为默认凭据”的契约。

随着 DeepSeek、GLM、Gemini、Claude、OpenAI-compatible 代理和自托管网关进入常用工作流，后端选择也不能继续停留在固定三家 fallback 链。需要把后端选择升级为可审阅、可配置、可记录、可复用的 provider/proxy 模型。

## 变更内容

- 在没有人工字幕时新增后端选择 checkpoint：说明是否下载媒体、是否上传 API、候选 provider、推荐方案、费用/隐私/区域风险和退化选项。
- 第一次进入 API/代理转写路径且没有显式选择、也没有已保存默认凭据时，必须让用户选择一个默认 API 凭据/环境变量名；后续再次需要转写时，除非用户显式指定其他 provider 或清除默认值，否则可以直接使用该默认选择。
- 默认选择只能记录 provider、mode、模型、endpoint label、环境变量名或凭据标签，禁止保存真实 API key、cookie、token、session value 或带鉴权 query 的完整 endpoint。
- 将转写后端从固定 `OpenAI -> Kimi/Moonshot -> MiniMax` 扩展为 provider registry，支持 OpenAI、Moonshot/Kimi、MiniMax、DeepSeek、GLM、Gemini、Claude，以及 OpenAI-compatible 代理、自定义 endpoint 或本地/企业网关。
- 增加 `--transcribe-provider` / provider 配置语义，允许显式选择 provider、model、base URL、endpoint、认证环境变量和请求类型。
- 区分“专用音频 ASR”“视频理解转写”“通用 LLM 从音视频派生文本生成转写”“代理转发”四类能力，不把不支持原生音频/视频的模型伪装成 ASR。
- 将用户选择、默认凭据来源、降级原因、请求类型、模型、脱敏 endpoint、风险提示和未验证项写入 `metadata.json`、`run-summary.json` 或 `run-manifest.json`。
- 保留默认轻量路径：有人工字幕时不触发 API 选择；普通 Markdown 转写不因富格式 checkpoint 被强制打断。

## 能力变更

### 新增能力

- `transcript-backend-selection`：定义无人工字幕时的用户选择 checkpoint、多 provider/proxy 转写策略、默认 API 凭据复用、配置优先级、安全记录和降级行为。

### 修改能力

- 无。

## 影响范围

- 影响 `video-transcript/SKILL.md`、`video-transcript/references/BACKENDS.md`、`video-transcript/references/CHECKS.md`、`video-transcript/references/OUTPUT-CONTRACT.md` 和故障排查文档。
- 影响 `video-transcript/scripts/transcript.py` 的 CLI 参数、后端选择逻辑、默认凭据读取/写入、dry-run/doctor 输出、metadata/summary 字段和错误提示。
- 可能新增 provider registry 配置、默认 provider 偏好配置、示例 JSON、环境变量约定和代理 endpoint 说明。
- 不要求在本 change 中实现所有第三方真实 API 的完整专用 SDK；允许先用标准 OpenAI-compatible / proxy adapter 和明确的能力标记接入，无法验证的 provider 必须显示为 `blocked`、`unsupported` 或 `requires-proxy`。
- 不把默认 API 凭据写入 skill 仓库或安装包；默认配置应是用户本机的非敏感偏好，并且可以被显式 CLI 参数覆盖。
