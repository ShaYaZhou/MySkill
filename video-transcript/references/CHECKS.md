# 检查点与自检

默认公开视频 Markdown 转写可以直接执行。只有高影响或高成本选择需要停下来确认。

## 需要确认的情况

- 使用浏览器 cookie 或登录态。
- 下载音频/视频后上传到 API。
- 付费后端、隐私敏感上传或大型播放列表。
- 非默认输出位置且存在覆盖风险。
- MiniMax endpoint、模型或 key 区域不明确。

确认模板：

```text
我准备这样处理：
- 输入：<URL / playlist>
- 输出目录：<path>
- 计划后端：<human_subtitle/openai/kimi-video/minimax-api>
- 是否下载媒体：<yes/no>
- 是否上传到 API：<yes/no>
- 可能费用/隐私风险：<short note>
- 已有产物处理：<skip/retry/force>

确认后我再执行。
```

## `--doctor`

用于本地诊断，不处理媒体：

- Python venv 是否可用。
- `yt-dlp`、`openai`、`requests` 是否可 import。
- `ffmpeg` / `ffprobe` 是否在 PATH。
- `OPENAI_API_KEY`、`MOONSHOT_API_KEY`、`MINIMAX_API_KEY` 是否存在。
- Moonshot / MiniMax endpoint 配置是否可见。

不要把 key、token、cookie 或 session value 输出到日志或 summary。

## `--dry-run`

用于预览，不下载媒体、不上传 API、不转写：

- 解析 URL metadata。
- 预览播放列表条目。
- 预览人工字幕是否可用。
- 预览将选择的后端。
- 预览输出目录和 metadata 路径。
- 标注 cookie、登录态、付费、隐私上传或大批量风险。

## 自检

完成前逐项检查：

- `metadata.json` 可解析。
- `original.md` 非空。
- `zh.md` 状态与 `needs_zh_translation` 一致。
- `source`、模型、语言状态和错误字段清楚。
- 公式保留风险已标记。
- 可恢复失败已安全重试。

## Reviewer Handoff

需要独立 reviewer 时，传入：

- 产物路径。
- `metadata.json` / `run-summary.json` 路径。
- 本检查清单。
- 风险边界：不得读取或输出 secret、cookie、token。
- 禁止修改范围。

要求 reviewer 返回：

- pass/fail。
- 证据。
- 修复建议。
- 是否阻塞汇报。

## 反馈回流

用户反馈后先定位层级：

- 转写文本。
- 后端选择。
- 公式。
- 翻译。
- metadata / summary。
- 输出路径或运行方式。

只修改最小相关文件，并说明哪些派生产物需要重建。
