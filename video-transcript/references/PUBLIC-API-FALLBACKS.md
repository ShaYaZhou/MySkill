# 公开接口 fallback

本文档定义视频类 skill 在 `yt-dlp` 或网页 metadata 失败时，如何使用站点公开、免登录、非绕过访问控制的接口做受控 fallback。本文档适用于 `video-transcript` 和 `yt-dlp-download`，两者必须使用一致的状态字段、脱敏规则和用户提示口径。

## 基本原则

- `yt-dlp` 仍是第一路径。公开接口只在 metadata、字幕或媒体地址阶段失败、缺失，或用户显式要求时介入。
- 所有站点都走同一个 adapter registry 机制：命中已注册 adapter 才调用公开接口；没有 adapter 时记录 `unsupported-public-api`，不猜测接口。
- adapter 只能登记公开、免登录、非绕过访问控制的接口。需要登录 cookie、私有 token、签名破解、会员权限、DRM 或地区绕过的接口不得登记。
- 请求默认不带 cookie，不读取浏览器 profile，不输出或保存 cookie、token、session value、API key。
- 接口提示需要登录、风控、cookie 或人工浏览器时，停止公开接口 fallback，进入 Web Access checkpoint 或转到 API/代理转写退化方案。

## Registry 契约

每个 adapter 至少声明：

```json
{
  "id": "bilibili",
  "display_name": "Bilibili",
  "domains": ["bilibili.com", "b23.tv"],
  "stages": ["metadata", "subtitle", "media"],
  "public": true,
  "requires_auth": false,
  "uses_cookie": false,
  "rate_limit": "small retry count; no parallel burst",
  "endpoint_labels": {
    "metadata": "api.bilibili.com/x/web-interface/view",
    "subtitle": "api.bilibili.com/x/player/v2",
    "media": "api.bilibili.com/x/player/playurl"
  }
}
```

`endpoint_labels` 只能记录 host/path 或稳定标签，不记录完整查询参数、签名、临时媒体 URL 或凭据。

## 支持阶段

- `metadata`：当 `yt-dlp --dump-single-json` 失败或信息不足时，补齐标题、id、分 P、时长、封面、简介、作者和必要平台 id。
- `subtitle`：当人工字幕列表为空或无法探测时，确认是否存在公开字幕，并区分 `available`、`empty`、`requires-web-access`、`api-failed`。
- `media`：当需要音频/视频输入且默认下载失败时，获取临时媒体流候选。summary 只记录 `available`、`empty`、`api-failed`、`requires-web-access` 等状态，不记录完整媒体 URL。

## 统一状态字段

`metadata.json`、`run-summary.json`、`download-summary.json` 中的公开接口字段保持一致：

- `metadata_source`：`yt_dlp`、`public_api` 或同等事实源。
- `public_api_fallback_used`：是否实际调用公开接口 fallback。
- `public_api_adapter`：adapter id，例如 `bilibili`。
- `public_api_stage`：本次涉及的阶段，例如 `metadata`、`subtitle`、`media`。
- `public_api_endpoint_label`：脱敏接口标签列表。
- `public_api_status`：`not-used`、`planned`、`ok`、`partial`、`disabled`、`unsupported-public-api`、`invalid-url`、`api-failed`。
- `public_api_requires_login`：公开接口是否明确提示需要登录。
- `public_api_uses_cookie`：公开接口 fallback 是否使用 cookie；默认必须为 `false`。
- `requires_web_access`：是否需要转入 Web Access checkpoint。
- `subtitle_state`：`unknown`、`available`、`empty`、`requires-web-access`、`missing-cid`、`api-failed`。
- `media_url_state`：`unknown`、`available`、`empty`、`requires-web-access`、`missing-cid`、`api-failed`。
- `fallback_failures`：脱敏失败原因列表。

## Bilibili adapter

首批 adapter 覆盖 Bilibili：

- 从 URL 提取 `BV` 或 `av` 标识。
- `metadata` 调用 `api.bilibili.com/x/web-interface/view`，映射标题、aid、cid、分 P、时长、封面、简介和 owner。
- `subtitle` 调用 `api.bilibili.com/x/player/v2`，若字幕公开可用则作为人工字幕候选；若返回需要登录或字幕列表为空且标记登录要求，记录 `requires-web-access`。
- `media` 调用 `api.bilibili.com/x/player/playurl`，获取公开视频的临时音频或视频流候选。下载时需要带公开 Referer 和桌面浏览器 User-Agent；summary 不记录完整流地址。

## dry-run 与 doctor

`--dry-run` 必须展示命中的 adapter、支持阶段、公开接口状态、字幕状态、媒体地址状态和后续动作。它不下载媒体、不上传 API、不写入最终媒体产物。

`--doctor` 必须展示公开接口 fallback 是否启用、已注册 adapter、支持域名、支持阶段和本地依赖状态。用户可以通过 `--no-public-api-fallback` 或环境变量 `VIDEO_SKILL_PUBLIC_API_FALLBACK=0` 禁用该机制。

## Web Access checkpoint

出现以下状态时，不继续尝试公开接口：

- 公开接口返回需要登录、cookie、验证码、风控或地区限制。
- 资源属于会员、付费、DRM 或访问控制内容。
- 用户明确要求使用浏览器登录态、课程页、内部站点或私有页面。

此时给出 Web Access checkpoint，说明访问范围、登录态类型、本地残留文件和脱敏记录；用户拒绝时只使用公开可访问资料，或记录无法完成的部分。
