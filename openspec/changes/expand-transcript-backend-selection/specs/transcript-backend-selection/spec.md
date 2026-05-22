## ADDED Requirements

### Requirement: 无人工字幕后端选择检查点
`video-transcript` 必须 在没有人工字幕且将进入音视频下载、API 上传、付费后端或代理转写路径前，提供可审阅的后端选择 checkpoint。

#### Scenario: 没有人工字幕且未显式选择后端，也没有默认 provider
- **当** 输入视频没有可用人工字幕，且用户没有通过 CLI 参数或当前对话明确选择转写 provider
- **则** agent 必须展示后端选择 checkpoint，列出推荐方案、可用 provider、不可用原因、是否下载媒体、是否上传 API、费用/隐私/区域风险和退化选项，并要求用户选择是否保存为默认 provider 后再继续

#### Scenario: 用户已通过 CLI 明确选择 provider
- **当** 用户运行时提供 `--transcribe-provider`、`--transcribe-mode` 或等价明确参数
- **则** `video-transcript` 视为后端选择已确认，但仍必须在 dry-run、metadata 或 summary 中记录选择来源、模型、请求类型和风险提示

#### Scenario: 已存在用户默认 provider
- **当** 输入视频没有可用人工字幕，用户没有显式选择 provider，且本机存在可用的用户默认 provider 偏好
- **则** `video-transcript` 必须直接使用该默认 provider 执行转写，不得再次因为 provider 选择本身打断用户；但大型播放列表、登录/cookie、覆盖已有产物、endpoint 区域不明、默认 key 缺失或 provider 能力不支持等独立风险仍必须按各自 checkpoint 处理

#### Scenario: 用户拒绝 API 上传
- **当** 用户在 checkpoint 中拒绝下载媒体后上传 API 或代理
- **则** `video-transcript` 必须 提供退化选项，包括用户上传字幕/音频、只保存 metadata、改用本地工具、跳过该视频或报告无法完成的部分

#### Scenario: 有人工字幕
- **当** 输入视频存在可用人工字幕
- **则** `video-transcript` 必须 优先使用人工字幕，并不得因为存在 API key 而强制触发后端选择 checkpoint

### Requirement: 默认 Provider 与凭据复用
`video-transcript` 必须 支持用户级默认 provider 偏好，使用户第一次选择后，后续无人工字幕转写可以默认复用该选择。

#### Scenario: 首次选择默认 API 凭据
- **当** 用户第一次进入无人工字幕 API/代理转写路径，且没有显式 provider，也没有已保存默认 provider
- **则** checkpoint 必须 要求用户从可用 provider 中选择一个默认 API 凭据，并说明该选择以后会默认复用，除非用户显式改选或清除默认值

#### Scenario: 默认凭据不保存 secret
- **当** `video-transcript` 保存默认 provider 偏好
- **则** 偏好文件 必须 只记录 provider id、mode、认证环境变量名、模型名或模型环境变量、endpoint label 或脱敏 host、选择来源和更新时间，不得记录真实 API key、cookie、token、session value 或带鉴权 query 的完整 endpoint

#### Scenario: 显式选择覆盖默认值
- **当** 用户通过 CLI 参数、本轮对话或配置显式选择不同 provider、mode、model、base URL 或 endpoint
- **则** 显式选择 必须 覆盖用户默认 provider；除非用户明确要求设为新的默认值，否则不得改写已保存默认偏好

#### Scenario: 默认值失效
- **当** 已保存默认 provider 的 key 缺失、endpoint 缺失、区域不明确、能力不支持或 adapter 不可用
- **则** `video-transcript` 必须 将默认 provider 标记为 `blocked` 或 `requires-confirmation`，并重新展示 provider 选择 checkpoint

#### Scenario: 清除或忽略默认值
- **当** 用户要求清除默认 provider，或通过等价参数请求本次忽略默认 provider
- **则** `video-transcript` 必须 不使用已保存默认值，并回到显式选择或 checkpoint 流程

### Requirement: Provider Registry
`video-transcript` 必须 使用 provider registry 描述转写 provider 的能力、配置、风险和执行状态，而不是只依赖固定三后端 fallback 链。

#### Scenario: 内置 provider 列表
- **当** agent 或脚本展示可选 provider
- **则** provider registry 必须 至少包含 OpenAI、Moonshot/Kimi、MiniMax、DeepSeek、GLM、Gemini、Claude、OpenAI-compatible 代理和 custom-proxy

#### Scenario: Provider 能力声明
- **当** provider 被列入 registry
- **则** registry 必须 声明该 provider 的 `capability_type`，例如 `audio-asr`、`video-understanding`、`audio-to-llm`、`openai-compatible`、`custom-proxy` 或 `unsupported-direct`

#### Scenario: Provider 配置声明
- **当** provider 被列入 registry
- **则** registry 必须 声明认证环境变量、可选 base URL/endpoint 环境变量、默认模型来源、是否下载媒体、是否上传媒体、付费/额度风险、区域风险和主要限制

#### Scenario: Provider 不支持直接转写
- **当** provider 只支持文本生成或当前配置无法直接处理音频/视频
- **则** `video-transcript` 必须 将该 provider 标为 `unsupported-direct`、`requires-proxy` 或 `blocked`，不得把它伪装成可直接执行的 ASR 后端

### Requirement: Provider 与 Mode 参数
`video-transcript` 必须 提供显式 provider/mode 配置，并保持旧 `--transcribe-backend` 参数兼容。

#### Scenario: 新参数显式选择
- **当** 用户传入 `--transcribe-provider`、`--transcribe-mode`、`--transcribe-model`、`--transcribe-base-url` 或 `--transcribe-endpoint`
- **则** 脚本 必须 按新参数选择 provider、请求类型、模型和 endpoint，并在 summary 中记录脱敏后的选择

#### Scenario: 旧 backend 映射
- **当** 用户继续使用 `--transcribe-backend openai`、`--transcribe-backend kimi-video` 或 `--transcribe-backend minimax-api`
- **则** 脚本 必须 将旧 backend 映射到对应 provider/mode，并保持现有行为兼容

#### Scenario: 参数冲突
- **当** 用户同时提供互相冲突的 `--transcribe-backend` 与 provider/mode 参数
- **则** 脚本 必须 报告冲突并要求用户明确选择，不得静默使用任一配置

#### Scenario: 环境变量自动推荐
- **当** 用户没有显式选择 provider，但环境变量中存在多个可用 API key
- **则** 如果用户默认 provider 不存在，checkpoint 必须 展示可用 provider 和推荐默认值，并要求用户选择是否保存默认 provider，而不是静默按环境变量顺序外发媒体

### Requirement: 多厂商与代理转写支持
`video-transcript` 必须 支持多厂商 API 和代理方案，但必须按能力边界执行或阻塞。

#### Scenario: OpenAI-compatible 代理
- **当** 用户选择 OpenAI-compatible 代理或自定义 base URL
- **则** `video-transcript` 必须 使用代理配置的 endpoint/model 执行，并在 metadata 或 run manifest 中记录脱敏 host、provider id、proxy_used 和是否上传媒体

#### Scenario: Custom proxy endpoint
- **当** 用户选择 custom-proxy
- **则** `video-transcript` 必须 要求明确 endpoint、认证环境变量、请求格式或适配器类型；缺少这些配置时该阶段状态 必须 为 `blocked`

#### Scenario: DeepSeek/GLM/Gemini/Claude 通过代理或兼容接口接入
- **当** DeepSeek、GLM、Gemini 或 Claude 通过 OpenAI-compatible、企业网关、自定义 endpoint 或用户自带代理提供可用音频/视频转写能力
- **则** `video-transcript` 必须 允许用户选择该 provider/proxy，并按 registry 声明的 mode 执行

#### Scenario: DeepSeek/GLM/Gemini/Claude 仅支持文本
- **当** DeepSeek、GLM、Gemini 或 Claude 的当前配置仅支持文本输入
- **则** `video-transcript` 必须 标记为 `unsupported-direct` 或 `requires-proxy`，并提示用户提供字幕、音频转文本代理、本地 ASR 或换用支持音视频的 provider

#### Scenario: 理解式转写不是逐字 ASR
- **当** provider 使用 `video-understanding` 或 `audio-to-llm` 方式生成讲稿式转写
- **则** 输出 metadata 和完成汇报 必须 标明该结果不是专用逐字 ASR，并提示精确措辞可能需要人工复核

### Requirement: Dry-run 和 Doctor 展示后端选择
`video-transcript` 必须 在 `--dry-run` 和 `--doctor` 中展示 provider 可用性、风险和配置状态，且不得泄露 secret。

#### Scenario: Doctor 检查 provider 配置
- **当** 用户运行 `python scripts/transcript.py --doctor`
- **则** 输出 必须 显示各 provider 的 key 是否存在、base URL/endpoint 是否配置、必要二进制和 Python 包是否可用、能力状态和不确定项，但不得输出任何 key/token/cookie/session value

#### Scenario: Dry-run 预览 provider 选择
- **当** 用户运行 `--dry-run` 且视频无人工字幕
- **则** dry-run summary 必须 预览候选 provider、推荐默认、是否下载/上传、可能分片、费用/隐私/区域风险、阻塞项和用户可选退化路径

#### Scenario: Dry-run 不执行外发
- **当** 用户运行 `--dry-run`
- **则** 脚本 必须 不下载媒体、不上传 API、不调用转写 provider，只输出可审阅计划和 summary

### Requirement: 后端选择记录与脱敏
`video-transcript` 必须 在运行事实源中记录后端选择、风险和降级状态，同时禁止记录敏感值。

#### Scenario: Metadata 记录 provider
- **当** API、代理或理解式转写被用于生成 `original.md`
- **则** `metadata.json` 必须 记录 `transcribe_provider`、`transcribe_mode`、`transcribe_model`、`provider_capability_type`、`provider_selection_source`、`default_provider_used`、`default_credential_label`、`media_downloaded`、`media_uploaded`、`proxy_used` 和 `selection_warnings`

#### Scenario: Summary 记录阻塞或跳过
- **当** 某 provider 因缺 key、缺 endpoint、能力不支持、用户拒绝外发或区域不明确而无法执行
- **则** `run-summary.json` 或 `run-manifest.json` 必须 记录 `blocked`、`skipped`、`requires-proxy` 或 `unsupported` 状态及原因

#### Scenario: 禁止敏感字段
- **当** 写入 metadata、summary、manifest、日志或完成汇报
- **则** 内容 不得 包含真实 API key、cookie、token、session value、完整敏感浏览器 profile 路径、私密 HTML 或带鉴权 query 的完整 endpoint

#### Scenario: Endpoint 脱敏记录
- **当** 需要记录 provider endpoint 或代理
- **则** 只能记录脱敏 host、provider id、配置变量名或用户可识别的 endpoint label，不得记录 secret-bearing URL

### Requirement: 默认路径与用户体验
`video-transcript` 必须 保持默认 Markdown 转写路径轻量，同时在高成本或外发阶段给出清楚选择。

#### Scenario: 普通公开视频 Markdown 转写
- **当** 输入是公开视频，存在人工字幕，且用户只要求 Markdown 转写
- **则** agent 必须 直接执行默认流程，不得引入多 provider checkpoint、富格式 checkpoint 或截图 checkpoint 打断用户

#### Scenario: 无人工字幕但用户要求快速推荐
- **当** 用户要求“你帮我选”或“用推荐方案”
- **则** agent 必须 根据可见配置、隐私风险、准确率需求和成本选择一个推荐 provider，并在执行前用一句话说明将使用的 provider/mode、是否上传媒体，以及是否将其保存为后续默认 provider

#### Scenario: 大型播放列表
- **当** 输入是大型播放列表且缺少人工字幕
- **则** agent 必须 在 checkpoint 中提示预计条目数、可能 API 调用量、成本风险、并发/分批策略和只处理部分视频的选项

