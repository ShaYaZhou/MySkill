## Context

`video-transcript` 和 `yt-dlp-download` 当前把 `yt-dlp` 作为视频站点解析入口，这是合理的默认方案，但它也意味着 metadata、字幕和媒体地址三个阶段都依赖站点网页抓取能力。最近验证 Bilibili 视频时，网页 metadata 阶段返回 `HTTP Error 412: Precondition Failed`，但公开视频的公开接口仍可返回标题、aid、cid、分 P、时长和播放地址。这说明我们需要一个站点公开接口 fallback 机制，用来处理“网页抓取失败，但站点存在公开、免登录接口”的情况。

这个变更会横跨两个视频类 skill：`video-transcript` 需要在 metadata、字幕、音频转写输入上 fallback；`yt-dlp-download` 需要在 metadata、下载计划和媒体地址上 fallback。两者必须保持相同的边界、日志字段和用户提示，避免同一个 URL 在不同 skill 中出现互相矛盾的解释。

约束：

- `yt-dlp` 仍是第一入口，公开接口只在失败、缺失或用户显式要求时介入。
- 公开接口必须由 adapter registry 显式声明，不对未知网站硬猜接口。
- 不使用登录 cookie、私有 token、签名绕过、付费/DRM/地区限制绕过。
- 当接口提示需要登录、风控或人工介入时，进入 Web Access checkpoint，而不是继续绕过。
- 面向人的文档、OpenSpec、skill 说明和 reference 均使用中文。

## Goals / Non-Goals

**Goals:**

- 为视频类 skill 增加统一的公开接口 fallback 架构。
- 对所有网站采用同一策略：有已声明 adapter 的站点可以 fallback；没有 adapter 的站点明确标记不可用或需要 Web Access。
- 首批 adapter 覆盖 Bilibili，并支持公开 metadata、字幕探测和公开播放地址探测。
- 在 `metadata.json`、`run-summary.json`、`download-summary.json` 中记录 fallback 事实源和失败原因。
- 在 `--dry-run` 中展示 fallback 计划和结果，在 `--doctor` 中展示已注册 adapter 与依赖状态。
- 保持 `video-transcript` 和 `yt-dlp-download` 的术语、字段、用户提示和安全边界一致。

**Non-Goals:**

- 不把所有网站都做成万能解析器；没有公开接口 adapter 的网站不做猜测。
- 不替代 `yt-dlp`，也不默认跳过 `yt-dlp` 的成熟解析能力。
- 不绕过登录、会员、付费、DRM、地区限制、风控或下载限制。
- 不把 cookie、API key、完整带签名查询参数的播放地址写入 summary 或日志。
- 不要求第一阶段一次性覆盖所有视频网站；新增站点必须逐个验证公开接口并补文档。

## Decisions

### 1. 使用显式 adapter registry，而不是临时 URL 猜测

每个站点 adapter 必须声明域名匹配、支持阶段、接口标签、公开/免登录边界、必要请求头、限速策略、返回字段映射和失败分类。运行时只在 URL 命中 adapter 后调用对应接口。

备选方案是遇到失败后按站点拼接常见接口路径，但这会扩大误用风险，也难以维护。显式 registry 能让“所有网站使用 fallback”变成同一套策略，而不是对所有网站盲试接口。

### 2. fallback 分成 metadata、subtitle、media 三个阶段

三个阶段的失败原因和后续动作不同：

- `metadata`：`yt-dlp --dump-single-json` 失败或只得到不完整信息时，用公开 metadata 接口补齐标题、时长、分 P、封面、作者等。
- `subtitle`：人工字幕缺失或探测失败时，用公开字幕接口确认是否存在字幕；如果接口提示 `need_login_subtitle` 或类似状态，只记录需要登录。
- `media`：需要下载音频、视频或转写输入，而 `yt-dlp` 下载失败时，用公开播放地址接口获取临时媒体 URL 或音频流候选。

这样可以避免一个阶段成功被误解为全流程成功。例如 Bilibili metadata 可以公开返回，但字幕可能仍要求登录。

### 3. `yt-dlp` 仍为第一路径，公开接口为受控 fallback

默认流程保持不变：先让 `yt-dlp` 处理格式选择、字幕提取、播放列表、分 P、断点续传和站点兼容性。公开接口仅在失败、字段缺失或用户显式指定时介入。

这样能继续利用 `yt-dlp` 的站点覆盖面，同时解决少数站点网页抓取失败但公开 API 可用的问题。

### 4. 两个 skill 先共享行为契约，代码可先局部复用

理想状态是新增共享 helper，例如 `scripts/public_api_fallbacks.py`，由两个 skill 调用。若当前仓库结构不适合立刻抽公共包，也可以先在两个 skill 中保持最小重复实现，但必须共用同一份 reference、字段命名和 adapter 语义。

这个决策降低一次性改造风险，同时保留后续抽公共模块的空间。

### 5. Bilibili 是首批必须 adapter

Bilibili adapter 需要支持：

- 从 `BV`/`av` URL 中提取视频标识。
- 通过 `x/web-interface/view` 获取 metadata、aid、cid、分 P、标题、时长、封面、简介和 owner。
- 通过 `x/player/v2` 探测字幕状态；如果返回需要登录或字幕为空，记录真实状态。
- 通过 `x/player/playurl` 获取公开视频的播放地址或音频流候选；记录 URL 有效期、Referer 要求和使用限制，不把完整临时 URL 写入摘要。

首批只把已经验证为公开、免登录的能力纳入 adapter。

### 6. summary 使用脱敏字段记录事实源

新增或补齐字段：

- `metadata_source`
- `public_api_fallback_used`
- `public_api_adapter`
- `public_api_stage`
- `public_api_endpoint_label`
- `public_api_status`
- `public_api_requires_login`
- `public_api_uses_cookie`
- `requires_web_access`
- `subtitle_state`
- `media_url_state`
- `fallback_failures`

`public_api_endpoint_label` 只记录 host/path 或稳定标签，不记录完整查询参数、cookie、token、签名或临时媒体 URL。

### 7. `--dry-run` 与 `--doctor` 必须能解释 fallback

`--dry-run` 不下载媒体、不上传转写 API，但必须显示命中的 adapter、计划调用的阶段、公开接口探测结果和后续会怎么处理。`--doctor` 必须展示已注册 adapter、支持域名、支持阶段和本地依赖状态。

这样用户可以在真正下载或转写前理解风险和边界。

## Risks / Trade-offs

- 公开接口变化 → adapter 必须有清晰错误分类和回退日志，后续通过 reference 与测试样例维护。
- 播放地址有时效 → summary 只记录状态和标签，不把临时 URL 当成长期可复用产物。
- 字幕接口可能要求登录 → 记录 `requires_web_access`，提示用户选择 Web Access 或进入 API 转写，不伪装成人工字幕成功。
- 不同站点公开接口质量不一致 → registry 中逐站声明支持阶段，不能用一个 adapter 的能力推断所有网站。
- 增加代码路径 → 用 mock 测试覆盖 metadata/subtitle/media 成功、缺失、登录要求、限流和失败分类。
- 法务与平台条款边界 → 文档明确只使用公开、免登录、非绕过访问控制的接口；涉及 cookies 和登录态时必须进入 checkpoint。

## Migration Plan

1. 新增公开接口 fallback reference，说明 adapter 注册格式、字段、脱敏规则、安全边界和站点扩展示例。
2. 新增或整理脚本内 adapter registry/helper，先实现 Bilibili adapter。
3. 接入 `video-transcript` 的 metadata、字幕探测、音频下载 fallback、`--dry-run`、`--doctor` 和 summary 写入。
4. 接入 `yt-dlp-download` 的 metadata、下载计划、媒体地址 fallback、`--dry-run`、`--doctor` 和 summary 写入。
5. 更新两个 skill 的 `SKILL.md`、示例、输出契约和安装后的文档。
6. 添加 mock 测试和本地验证命令，覆盖成功、失败、需要登录、无 adapter 和脱敏日志。
7. 重新安装/同步 skill 后，用 Bilibili 公开 URL 做 dry-run 验证。

回滚策略：保留 `yt-dlp` 默认路径不变，若 fallback 代码出现问题，可通过配置或参数禁用公开接口 fallback，回到原有下载/转写行为。

## Open Questions

- 共享 helper 放在两个 skill 的 `scripts/` 下各自复制，还是新增仓库级公共模块后由安装脚本同步？
- 首批除 Bilibili 外还要优先支持哪些网站，需要逐站确认公开接口来源和边界。
- 是否需要为每个 adapter 增加独立 reference 文件，记录接口来源、字段映射、示例响应和维护日期。
