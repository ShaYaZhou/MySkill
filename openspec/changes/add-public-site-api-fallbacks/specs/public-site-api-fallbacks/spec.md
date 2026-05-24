## ADDED Requirements

### Requirement: 公开接口 fallback registry

系统 MUST 为视频类 skill 提供显式的站点公开接口 fallback registry，用于声明每个站点可使用的公开、免登录、非绕过访问控制的接口能力。

#### Scenario: 命中已注册站点

- **WHEN** 用户输入的视频 URL 匹配某个 adapter 的域名或 URL 规则
- **THEN** 系统 MUST 识别该 adapter，并读取其支持的 `metadata`、`subtitle`、`media` 阶段能力

#### Scenario: 未命中已注册站点

- **WHEN** 用户输入的视频 URL 没有匹配任何 adapter
- **THEN** 系统 MUST 不猜测站点接口，并将 fallback 状态记录为 `unsupported-public-api`

#### Scenario: adapter 声明边界

- **WHEN** 系统加载 adapter registry
- **THEN** 每个 adapter MUST 声明域名匹配、支持阶段、endpoint label、公开/免登录说明、必要请求头、限速策略、字段映射和失败分类

### Requirement: fallback 触发条件

系统 MUST 在 `yt-dlp` 默认路径失败、字段缺失或用户显式要求时，才进入公开接口 fallback。

#### Scenario: metadata 阶段失败后 fallback

- **WHEN** `yt-dlp` metadata 获取失败或返回的信息不足以继续执行
- **THEN** 系统 MUST 检查是否存在该站点的 `metadata` adapter，并在存在时调用公开 metadata 接口

#### Scenario: 字幕阶段失败后 fallback

- **WHEN** 人工字幕探测失败、字幕为空或 `yt-dlp` 无法读取字幕列表
- **THEN** 系统 MUST 检查是否存在该站点的 `subtitle` adapter，并在存在时调用公开字幕接口确认字幕状态

#### Scenario: 媒体地址阶段失败后 fallback

- **WHEN** 流程需要音频、视频或转写输入，且 `yt-dlp` 媒体下载或地址探测失败
- **THEN** 系统 MUST 检查是否存在该站点的 `media` adapter，并在存在时调用公开播放地址接口获取候选媒体流

#### Scenario: 用户显式禁用 fallback

- **WHEN** 用户通过参数或配置显式禁用公开接口 fallback
- **THEN** 系统 MUST 跳过 adapter 调用，并记录 fallback 被用户禁用

### Requirement: Bilibili adapter

系统 MUST 首批提供 Bilibili 公开接口 adapter，并覆盖公开 metadata、字幕探测和公开视频播放地址探测。

#### Scenario: Bilibili metadata fallback

- **WHEN** Bilibili URL 的网页 metadata 获取失败但 URL 中包含有效 `BV` 或 `av` 标识
- **THEN** 系统 MUST 调用 Bilibili 公开 metadata 接口获取标题、aid、cid、分 P、时长、封面、简介和 owner 信息

#### Scenario: Bilibili 字幕状态探测

- **WHEN** Bilibili 人工字幕无法通过默认路径获取
- **THEN** 系统 MUST 调用 Bilibili 公开字幕相关接口探测字幕状态，并区分可用、为空、需要登录和接口失败

#### Scenario: Bilibili 字幕需要登录

- **WHEN** Bilibili 字幕接口返回需要登录、需要 cookie 或字幕列表为空但标记需要登录
- **THEN** 系统 MUST 将字幕状态记录为需要 Web Access 或 API 转写，不得把该结果记录为人工字幕成功

#### Scenario: Bilibili 公开视频播放地址 fallback

- **WHEN** Bilibili 公开视频需要媒体输入且默认下载路径失败
- **THEN** 系统 MUST 调用公开播放地址接口获取候选音频或视频流，并记录 Referer 要求、时效状态和媒体类型

### Requirement: Web Access checkpoint

系统 MUST 在公开接口无法继续且需要登录态、cookie、人工浏览器或风控验证时提示 Web Access checkpoint。

#### Scenario: 公开接口要求登录

- **WHEN** adapter 返回 `requires-login`、`requires-cookie`、`blocked` 或等价状态
- **THEN** 系统 MUST 停止公开接口 fallback，并提示用户可选择 Web Access、提供 cookie、改用 API 转写或跳过该资源

#### Scenario: 用户拒绝 Web Access

- **WHEN** 用户拒绝或未授权 Web Access 方案
- **THEN** 系统 MUST 将对应阶段记录为 `blocked` 或 `skipped`，并继续执行可用的后续安全方案

### Requirement: summary 和 metadata 事实记录

系统 MUST 在输出摘要中记录公开接口 fallback 的事实源、状态和边界，并对敏感信息脱敏。

#### Scenario: fallback 被使用

- **WHEN** 任一阶段使用公开接口 fallback
- **THEN** 系统 MUST 在 `metadata.json`、`run-summary.json` 或 `download-summary.json` 中记录 `public_api_fallback_used`、`public_api_adapter`、`public_api_stage`、`public_api_endpoint_label` 和 `public_api_status`

#### Scenario: fallback 未被使用

- **WHEN** 默认路径成功且未调用公开接口 adapter
- **THEN** 系统 MUST 在摘要中保留可判断来源的字段，例如 `metadata_source` 或等价字段

#### Scenario: 敏感信息脱敏

- **WHEN** 系统记录公开接口 endpoint、播放地址、请求头或失败上下文
- **THEN** 系统 MUST 不写入 cookie、API key、完整签名查询参数、临时媒体 URL 或其他可复用凭据

### Requirement: dry-run 和 doctor 可观测性

系统 MUST 在 dry-run 和 doctor 模式中展示公开接口 fallback 的可用性和计划。

#### Scenario: dry-run 展示 fallback 计划

- **WHEN** 用户使用 `--dry-run` 处理命中 adapter 的视频 URL
- **THEN** 系统 MUST 展示命中的 adapter、支持阶段、将尝试的公开接口、探测结果和后续动作，且不得下载媒体或上传转写 API

#### Scenario: doctor 展示 adapter 状态

- **WHEN** 用户运行 `--doctor`
- **THEN** 系统 MUST 展示已注册 adapter、支持域名、支持阶段、本地依赖状态和公开接口 fallback 是否启用

### Requirement: video-transcript 与 yt-dlp-download 行为一致

`video-transcript` 与 `yt-dlp-download` MUST 使用一致的 fallback 术语、状态字段、安全边界和用户提示。

#### Scenario: 同一 URL 在两个 skill 中命中同一 adapter

- **WHEN** 用户分别用 `video-transcript` 和 `yt-dlp-download` 处理同一个命中 adapter 的 URL
- **THEN** 两个 skill MUST 使用相同的 adapter 标识、endpoint label、fallback 状态分类和 Web Access 提示口径

#### Scenario: 一个 skill 只需要部分阶段

- **WHEN** 某个 skill 只需要 metadata、subtitle 或 media 中的部分阶段
- **THEN** 系统 MUST 只调用必要阶段，并在摘要中清晰记录未调用阶段的原因

### Requirement: 安全边界

系统 MUST 只使用公开、免登录、非绕过访问控制的接口作为 fallback，并遵守最小请求和可审计记录原则。

#### Scenario: adapter 需要非公开凭据

- **WHEN** 某个接口需要私有 token、登录 cookie、签名破解、DRM 绕过或付费权限
- **THEN** 系统 MUST 不把该接口登记为公开接口 fallback

#### Scenario: 公开接口请求失败

- **WHEN** 公开接口返回限流、风控、地区限制、付费限制或不可解析响应
- **THEN** 系统 MUST 记录明确失败分类，并停止该阶段 fallback

### Requirement: 验证覆盖

系统 MUST 为公开接口 fallback 提供可重复的本地验证，覆盖成功、失败、脱敏和 checkpoint 场景。

#### Scenario: mock 测试覆盖 adapter

- **WHEN** 开发者运行本地验证命令
- **THEN** 测试 MUST 覆盖 adapter 命中、metadata 成功、字幕为空、需要登录、媒体 URL 获取失败、无 adapter 和敏感信息脱敏

#### Scenario: 真实网络探测不作为硬性测试

- **WHEN** 本地环境没有网络或公开视频接口临时不可用
- **THEN** 核心测试 MUST 仍可通过 mock 响应验证行为契约
