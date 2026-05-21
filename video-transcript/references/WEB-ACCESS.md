# 网页访问检查点（Web Access Checkpoint）

本文档定义 `video-transcript` 在需要网页登录、cookie、动态页面或浏览器交互时的受控调用规则。所有生成文档、交接记录和汇报必须使用中文。

## 触发条件

进入 Web Access checkpoint 的情况：

- 公开视频流程无法直接获取视频、字幕、章节、标题、缩略图或必要截图，且原因疑似登录、cookie、动态渲染、地区限制页面或浏览器交互。
- 用户明确要求使用网页登录态、浏览器 cookie、会员页、课程页、内部站点或需要网页操作的来源。
- 准备使用 `--cookies-from-browser` 或等价浏览器登录态参数。
- 需要从页面读取截图候选、章节目录、课件附件或动态生成的字幕地址。

不触发的情况：

- 普通公开视频可以直接通过人工字幕或公开 metadata 生成 Markdown 转写。
- 用户只要 Markdown 转写，且没有登录、cookie、动态页面、截图或富格式素材需求。
- 页面失败原因与登录态无关，且可以通过换公开 URL、人工字幕或 API 转写解决。

## 确认模板

执行前向用户展示以下中文模板，并等待确认：

```text
我需要进入 Web Access checkpoint 才能继续：

- 目标网站：<domain / site>
- 访问范围：<只访问哪些 URL、视频页、字幕页或附件页>
- 目的：<获取字幕 / 视频信息 / 截图候选 / 章节 / 附件>
- 登录态类型：<无需登录 / 浏览器已有登录态 / 用户现场登录 / cookie 读取，仅写脱敏类型>
- 授权范围：<仅本次运行 / 指定 URL / 指定课程或播放列表>
- 本地残留文件：<可能产生的临时 HTML、截图、缓存、下载片段和路径>
- 隐私与版权风险：<是否含私密页面、会员内容、个人信息、受版权保护内容>
- 清理方式：<运行后删除临时文件 / 保留指定产物 / 用户手动清理>
- 降级方案：如果你拒绝，我会只使用公开可访问信息，或汇报无法完成的部分。

请回复“确认 Web Access”，或说明要限制/跳过哪些访问。
```

如果用户最初已经明确授权某个登录来源，也仍要用短确认复述访问范围和本地残留文件；不得把一次授权扩展到未提到的网站、账号、播放列表或私密区域。

## 安全边界

必须遵守：

- 不保存、输出或写入密码、cookie、token、session value、验证码、完整敏感浏览器 profile 路径或私密 HTML 内容。
- 不要求用户把密码、cookie、token 或 API key 写入 skill 文件、模板、示例、日志或聊天回复。
- 不绕过访问控制、付费墙、DRM、水印、地区限制、下载限制或网站明确禁止的行为。
- 不静默扩大访问范围；需要访问新域名、新账号区域、新播放列表或新类型文件时重新确认。
- 默认不嵌入私密登录页截图；如确需使用，必须先说明用途、脱敏方式、外发限制和替代方案。
- 任何临时文件都应放入产物目录或 `.work/`，并在完成前记录清理状态。

## 结果交接格式

Web Access 完成后，用中文交接给转写或富格式阶段：

```markdown
## Web Access 结果交接

- 状态：ok / skipped / blocked / failed
- 访问时间：<ISO 8601 或本地时间>
- 来源页面：<脱敏 URL 或域名 + 页面类型>
- 授权范围：<用户确认的范围>
- 登录态类型：<none / browser-session / user-interactive-login / cookies-from-browser / other-redacted>
- 抓取到的信息：
  - 字幕：<路径 / 语言 / 是否人工字幕 / 未获取原因>
  - 视频信息：<标题 / 时长 / 章节 / metadata 路径>
  - 截图候选：<时间戳 + 理由，或无>
  - 附件或素材候选：<路径 / 用途 / 风险>
- 本地文件：
  - <path>：<用途 / 是否保留 / 清理状态>
- 未完成项：<原因和下一步>
```

## `run-manifest.json` 脱敏记录

当运行包含 Web Access、截图或富格式输出时，产物目录下的 `run-manifest.json` 应记录脱敏事实：

```json
{
  "web_access": {
    "status": "ok",
    "confirmed_at": "2026-01-01T00:00:00Z",
    "accessed_at": "2026-01-01T00:01:00Z",
    "target_site": "example.invalid",
    "source_pages": ["https://example.invalid/course/<redacted>"],
    "authorization_scope": "仅本次运行的指定视频页",
    "credential_context": "browser-session",
    "captured": {
      "subtitles": [{"language": "zh", "path": "subtitles/zh.vtt", "kind": "human"}],
      "video_info": "metadata.json",
      "screenshot_candidates": ["00:03:12", "00:08:40"]
    },
    "local_residue": [
      {"path": ".work/web-access-summary.md", "purpose": "结果交接", "cleanup": "kept"}
    ],
    "redactions": ["cookies", "tokens", "private_html", "profile_path"],
    "privacy_notes": "未记录密码、cookie、token、session value 或私密 HTML。"
  }
}
```

禁止字段值包含真实 cookie、token、session value、密码、完整浏览器 profile 敏感路径、私密页面 HTML 或未经脱敏的个人信息。`credential_context` 只能写登录态类型，例如 `none`、`browser-session`、`user-interactive-login`、`cookies-from-browser`、`api-auth-present`、`other-redacted`。

## 用户拒绝或能力缺失时

用户拒绝 Web Access、拒绝登录态或当前 agent 缺少 Web Access 能力时：

- 继续使用公开可访问字幕、metadata、公开视频下载或用户提供的文件。
- 可询问用户是否愿意上传字幕文件、视频文件、截图或公开替代链接。
- 将相关阶段写为 `skipped` 或 `blocked`，并说明哪些内容无法完成。
- 不尝试绕过访问控制，不猜测私密页面内容，不生成伪造截图或伪造来源证据。
