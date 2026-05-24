## 背景

`video-transcript` 和 `yt-dlp-download` 当前主要依赖 `yt-dlp` 先取得站点页面 metadata；当源站页面触发反爬或返回 412/403 等错误时，即使该站点存在公开、无鉴权、可稳定调用的 metadata / player / subtitle API，脚本也不会主动 fallback。Bilibili 的 `x/web-interface/view`、`x/player/v2`、`x/player/playurl` 已验证可在公开视频场景返回基础信息和播放地址，因此需要把“公开接口 fallback”抽象成所有站点可复用的机制。

## 变更内容

- 新增站点公开接口 fallback 架构：当 `yt-dlp` metadata 阶段失败、字幕探测失败或媒体地址探测失败时，按域名进入公开接口 adapter registry。
- 对所有网站使用统一 fallback 策略：只要站点 adapter 声明了公开、无鉴权、非绕过访问控制的接口，就允许 fallback；没有 adapter 或接口不公开时，必须记录为 `unsupported-public-api`、`requires-web-access` 或 `blocked`，不得硬猜私有接口。
- 首批实现必须覆盖 Bilibili：从 BV/av URL 提取 id，调用公开 metadata 接口取得标题、aid、cid、分 P、时长、封面、简介和 owner；尝试公开字幕接口；无人工字幕时尝试公开播放地址中的音频流作为后续转写输入。
- 将 fallback 事实写入 `metadata.json`、`run-summary.json` 或 `download-summary.json`：记录 adapter、接口类型、脱敏 endpoint host/path label、状态、失败原因、是否公开、是否需要登录、是否使用 cookie、是否上传媒体。
- `--dry-run` 必须展示公开接口 fallback 计划和结果，不下载媒体、不上传 API；`--doctor` 必须展示已注册 adapter 和依赖状态。
- `video-transcript` 与 `yt-dlp-download` 都要复用同一套策略和文档口径；具体代码可以先各自实现或共享 helper，但行为契约必须一致。
- 不允许把公开接口 fallback 变成绕过登录、付费、DRM、地区限制、下载限制或站点风控的工具；涉及登录/cookie 时仍走 Web Access checkpoint。

## 能力变更

### 新增能力

- `public-site-api-fallbacks`：定义视频类 skill 在 `yt-dlp` 或网页 metadata 失败时，如何按站点公开接口 registry 进行安全 fallback、记录事实源、处理字幕/播放地址、脱敏接口信息并触发 Web Access 退化。

### 修改能力

- 无。

## 影响范围

- 影响 `video-transcript/scripts/transcript.py` 的 metadata 获取、字幕探测、音频下载 fallback、dry-run、doctor、metadata/run-summary 写入。
- 影响 `yt-dlp-download/scripts/download.py` 的 metadata 获取、下载计划、download-summary 写入和 dry-run 行为。
- 影响两个 skill 的 `SKILL.md`、references、examples、manifest 和验证规则。
- 可能新增共享 reference，例如 `references/PUBLIC-API-FALLBACKS.md`；也可能新增脚本内 adapter registry 或共享 helper。
- 首批 adapter 以 Bilibili 为必须项；其它站点只能在确认公开接口并写明边界后加入 registry。
