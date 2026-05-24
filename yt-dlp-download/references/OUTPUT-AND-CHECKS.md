# 输出与检查

本文档定义 `yt-dlp-download` 的运行产物、summary schema 和完成前自检。

## 默认输出

默认输出根目录：

```text
~/Downloads/yt-dlp/
```

典型产物：

```text
<title> [<id>].mp4
<title> [<id>].zh-Hans.vtt
<title> [<id>].en.vtt
<title> [<id>].jpg
.yt-dlp-archive.txt
download-summary.json
```

实际扩展名由 yt-dlp、源站格式和 ffmpeg 可用性决定。若路径来自 glob 或 yt-dlp 输出推断且无法确定，在 summary 中标记 `uncertain_path`。

## `download-summary.json`

建议字段：

```json
{
  "schema_version": 1,
  "tool": "yt-dlp-download",
  "status": "partial_failure",
  "started_at": "2026-01-01T00:00:00Z",
  "completed_at": "2026-01-01T00:00:00Z",
  "cwd": "D:/git/MySkill/yt-dlp-download",
  "argv": ["scripts/download.py", "--dry-run", "https://example.invalid/watch"],
  "yt_dlp_version": "2026.01.01",
  "ffmpeg": "present",
  "output_dir": "C:/Users/name/Downloads/yt-dlp",
  "items": [
    {
      "url": "https://example.invalid/watch",
      "id": "example-id",
      "title": "示例标题",
      "status": "ok",
      "media_paths": ["C:/out/example.mp4"],
      "subtitle_paths": ["C:/out/example.zh-Hans.vtt"],
      "thumbnail_path": "C:/out/example.jpg",
      "archive_skip": false,
      "metadata_source": "yt_dlp",
      "public_api_fallback_used": false,
      "public_api_adapter": null,
      "public_api_stage": [],
      "public_api_endpoint_label": [],
      "public_api_status": "not-used",
      "subtitle_state": "unknown",
      "media_url_state": "unknown",
      "requires_web_access": false,
      "warnings": []
    }
  ],
  "failures": [],
  "warnings": []
}
```

`argv` 只能记录脱敏后的参数。不得记录 cookie、token、session value 或完整敏感 profile 路径。

## 状态 token

- `status`: `ok`、`failed`、`partial_failure`、`skipped`、`dry_run`
- `archive_skip`: `true`、`false`
- `privacy_gate`: `none`、`cookies`、`login_required`
- `path_state`: `confirmed`、`uncertain_path`
- `metadata_source`: `yt_dlp`、`public_api`
- `public_api_status`: `not-used`、`planned`、`ok`、`partial`、`disabled`、`unsupported-public-api`、`invalid-url`、`api-failed`
- `subtitle_state`: `unknown`、`available`、`empty`、`requires-web-access`、`missing-cid`、`api-failed`
- `media_url_state`: `unknown`、`available`、`empty`、`requires-web-access`、`missing-cid`、`api-failed`

## `--doctor`

诊断项：

- isolated venv 是否存在且可用。
- `yt_dlp` 是否可 import。
- `ffmpeg` / `ffprobe` 是否在 `PATH`。
- 输出目录是否可写。
- 浏览器 cookie 配置是否可尝试读取。
- archive 文件是否可创建或更新。
- 公开接口 fallback 是否启用、已注册 adapter、支持域名和支持阶段。

`--doctor` 不下载媒体，不读取或打印 cookie 内容。

## `--dry-run`

预览项：

- URL metadata 和播放列表条目。
- 命中的公开接口 adapter、支持阶段、fallback 状态、字幕状态和媒体地址状态。
- 可能的媒体格式和输出模板。
- 人工字幕语言候选。
- 缩略图候选。
- archive 文件位置和可能 skip 的条目。
- cookie、登录态、格式合并或大型播放列表风险。

`--dry-run` 不下载媒体，不写入最终媒体产物。

## 完成前自检

- 每个输入 URL 都在 summary 中有一条结果。
- 成功项有媒体路径或 archive skip 证据。
- 字幕、缩略图缺失时有原因。
- 失败项有最小可行动作，例如更新 yt-dlp、安装 ffmpeg、提供 cookie、改用 audio-only 或报告 DRM/访问限制。
- 覆盖或 force 行为已写入 warnings。

## 退化菜单

缺依赖、缺登录态或站点限制时，给出可选路径：

- 安装或配置缺失工具。
- 使用 `--cookies-from-browser` 并限定授权范围。
- 使用公开接口 fallback；若接口提示登录、cookie、风控或访问控制，则转入 Web Access checkpoint。
- 改为 `--audio-only`。
- 跳过字幕或缩略图。
- 跳过失败项，只保留成功项。
- 报告阻塞，不生成空壳产物冒充成功。
