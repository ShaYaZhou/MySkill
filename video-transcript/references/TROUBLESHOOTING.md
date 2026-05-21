# 故障排查

先看 `metadata.json`，再看 `run-summary.json`。不要只根据终端最后几行判断成功。

## 缺少依赖

- `requests` 缺失：MiniMax API 分支需要 `requests`。运行 `--doctor`，确认 isolated venv 中能 import `requests`。
- `ffmpeg` / `ffprobe` 缺失：音视频下载、抽音轨、格式合并可能失败。安装后确保它们在 `PATH`。
- `yt-dlp` 行为异常：优先运行 `--doctor`，必要时使用脚本提供的更新选项。

## MiniMax Endpoint

MiniMax 有国内和海外 endpoint。不能确认区域时不要静默猜测，应在 checkpoint 中说明：

- 当前可见的 `MINIMAX_BASE_URL`。
- 是否存在 `MINIMAX_TRANSCRIBE_URL`。
- 将使用的 `MINIMAX_ASR_MODEL`。
- 不确定时给出配置、换后端、跳过转写或报告阻塞的退化菜单。

## Cookie 与登录态

需要登录时优先使用最小授权范围：

```powershell
python scripts/transcript.py --cookies-from-browser chrome "URL"
```

不要记录 cookie、token、session value 或完整敏感 profile 路径。若网站涉及 DRM、付费限制或访问控制，不要尝试绕过。

## 字幕不可用

如果没有人工字幕：

1. 用 `--dry-run` 预览候选后端、输出路径和风险。
2. 向用户确认是否下载媒体并上传 API。
3. 记录 fallback 原因和最终后端。

默认不要把自动字幕当作人工字幕成功。

## 数学公式

数学内容应保留为 Markdown LaTeX：

- 行内公式：`$...$`
- 块级公式：`$$...$$`

如果公式来自听写且无法验证，在完成汇报中标为风险。不要把不确定公式写成“已核验”。

## 已有产物与重试

- 默认优先跳过已有成功产物或只补齐缺失产物。
- 只重试失败项时，不要重复上传已成功的视频。
- 使用 `--force` 前说明会覆盖哪些文件。
- 不确定输出路径时，在 summary 中标记 `uncertain_path`，不要汇报为确定成功。
