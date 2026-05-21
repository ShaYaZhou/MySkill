---
name: yt-dlp-download
description: 当用户提供一个或多个视频或播放列表 URL，并希望用 yt-dlp 下载视频、音频、人工字幕或缩略图时使用。默认偏向 MP4 兼容输出，保留字幕和缩略图 sidecar，并用 archive 避免重复下载。
---

# yt-dlp Download

## 概览

通过封装脚本调用 yt-dlp 下载视频或播放列表。默认行为适合日常下载：优先 MP4 兼容格式，只下载人工字幕，保存缩略图，支持播放列表，并通过 archive 文件跳过重复条目。

## 默认流程

在本 skill 目录运行：

```powershell
python scripts/download.py "VIDEO_OR_PLAYLIST_URL"
```

多个 URL 可以一次传入：

```powershell
python scripts/download.py "URL_1" "URL_2"
```

脚本会在 skill 目录内维护独立 `.venv`，并在其中安装或更新 `yt-dlp[default]`。默认下载到 `~/Downloads/yt-dlp`。

## 下载策略

- 优先 MP4 兼容输出，同时保持可行的最佳质量。
- 默认只下载人工字幕，不下载自动生成字幕。
- 字幕优先中文，其次英文；没有匹配人工字幕时继续下载媒体。
- 默认下载缩略图。
- 播放列表按批量下载处理。
- 使用输出目录中的 `.yt-dlp-archive.txt` 跳过已下载视频。
- 字幕和缩略图保留为 sidecar 文件，不默认嵌入媒体。

## 常用选项

```powershell
python scripts/download.py --output-dir "D:\videos" "URL"
python scripts/download.py --audio-only "URL"
python scripts/download.py --no-thumbnail "URL"
python scripts/download.py --sub-lang zh-Hans "URL"
python scripts/download.py --cookies-from-browser chrome "URL"
python scripts/download.py --update "URL"
python scripts/download.py --doctor
python scripts/download.py --dry-run "URL"
python scripts/download.py --force "URL"
```

`--doctor` 只诊断依赖和环境。`--dry-run` 只预览 metadata、输出模板、字幕候选、archive 和风险，不下载媒体。`--force` 表示允许覆盖或重跑，需要先确认覆盖风险。

## 检查点

以下情况先停下来确认计划：

- 需要浏览器 cookie 或登录态。
- 请求含糊，需要 agent 自行选择下载范围。
- 非默认输出目录且存在覆盖风险。
- 大型播放列表可能生成大量文件。
- 网站可能涉及 DRM、付费限制或访问控制。

## 输出契约

每次运行应尽量写入 `download-summary.json` 或等价机器可读报告，记录输入 URL、下载/跳过/失败项、输出文件、字幕、缩略图、archive skip、警告和重试建议。

## 引用地图

只有请求需要细节时才继续读取：

- [`references/OUTPUT-AND-CHECKS.md`](references/OUTPUT-AND-CHECKS.md)：输出结构、`download-summary.json` schema、doctor/dry-run、自检和退化菜单。

## 完成检查

- 成功项有明确媒体文件或 archive skip 记录。
- 选定字幕和缩略图的路径写入 summary；缺失时有原因。
- 失败项有错误、重试建议和是否阻塞的状态。
- 不确定路径、被跳过项目和覆盖行为不能被汇报成确定成功。
