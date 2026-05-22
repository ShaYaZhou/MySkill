# 检查点与自检

默认公开视频 Markdown 转写可以直接执行。只有高影响、高成本或首次默认 provider 决策需要停下来确认。

## 需要确认的情况

- 没有人工字幕，且用户没有显式 provider，也没有可用默认 provider。
- 用户要把本次 provider 选择保存为默认 API 凭据。
- 已保存默认 provider 的 key 缺失、endpoint 缺失、区域不明确、能力不支持或 adapter 不可用。
- 使用浏览器 cookie 或登录态。
- 下载音频/视频后上传到 API 或代理。
- 付费后端、隐私敏感上传或大型播放列表。
- 非默认输出位置且存在覆盖风险。

## 无人工字幕 Provider Checkpoint

```text
没有检测到可用人工字幕。我需要选择转写 provider 后才能继续：
- 输入：<URL / playlist>
- 输出目录：<path>
- 推荐 provider：<provider / reason>
- 可用 provider：<provider -> key present / mode / endpoint label / risk>
- 不可用 provider：<provider -> missing key / requires proxy / unsupported direct>
- 是否下载媒体：<yes/no>
- 是否上传到 API/代理：<yes/no>
- 可能费用/隐私/区域风险：<short note>
- 保存为后续默认 provider：yes（首次无默认时必选）
- 退化选项：上传字幕/音频、本地 ASR、只保存 metadata、跳过

确认后我再执行。
```

第一次选择默认 API 凭据时，只能保存 provider、mode、认证环境变量名、模型、endpoint label 和更新时间，不能保存真实 key。

## 快速推荐

如果用户说“你帮我选”或“用推荐方案”，agent 可以根据可见配置、准确率、隐私和成本推荐一个 provider。首次无默认 provider 时，该推荐需要保存为默认 provider；仍要用一句话说明：

- provider/mode。
- 是否下载媒体。
- 是否上传媒体。
- 将保存为默认 provider。

如果用户已经保存了可用默认 provider，普通无人工字幕转写可以直接使用该默认项，不再因为 provider 选择本身暂停。

## 大型播放列表

播放列表较大且缺少人工字幕时，provider checkpoint 必须额外说明：

- 预计条目数。
- 可能 API 调用量。
- 可能费用或额度风险。
- 建议分批策略。
- 是否只处理部分视频。
- 是否先对首条或首批条目试跑。

## 拒绝外发后的退化菜单

如果用户拒绝 API 上传或代理外发，提供：

- 用户提供人工字幕。
- 用户提供已转写文本。
- 用户提供本地音频并指定本地 ASR。
- 只保存 metadata 和失败原因。
- 跳过该视频或播放列表中的该条。

## `--doctor`

用于本地诊断，不处理媒体：

- Python venv 是否可用。
- `yt-dlp`、`openai`、`requests` 是否可 import。
- `ffmpeg` / `ffprobe` 是否在 PATH。
- 各 provider 的认证环境变量是否存在。
- provider 的能力类型、endpoint label、默认 provider 偏好和阻塞原因。

不要把 key、token、cookie 或 session value 输出到日志或 summary。

## `--dry-run`

用于预览，不下载媒体、不上传 API、不转写：

- 解析 URL metadata。
- 预览播放列表条目。
- 预览人工字幕是否可用。
- 没有人工字幕时预览候选 provider、推荐默认、是否下载/上传、可能分片、成本/隐私/区域风险和退化选项。
- 预览输出目录和 metadata 路径。

## 自检

完成前逐项检查：

- `metadata.json` 可解析。
- `original.md` 非空。
- 使用 API/代理时，provider/mode/model/selection source/media upload/proxy 字段完整。
- 使用默认 provider 时，`default_provider_used` 和 `default_credential_label` 已脱敏记录。
- `zh.md` 状态与 `needs_zh_translation` 一致。
- `source`、模型、语言状态和错误字段清楚。
- 公式保留风险已标记。
- 可恢复失败已安全重试。

## Reviewer 交接

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
