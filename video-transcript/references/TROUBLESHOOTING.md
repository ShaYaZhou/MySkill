# 故障排查

先看 `metadata.json`，再看 `run-summary.json`。不要只根据终端最后几行判断成功。

## 缺少依赖

- `requests` 缺失：MiniMax API、OpenAI-compatible 和 custom-proxy 分支需要 `requests`。运行 `--doctor`，确认 isolated venv 中能 import。
- `ffmpeg` / `ffprobe` 缺失：音视频下载、抽音轨、格式合并可能失败。安装后确保它们在 `PATH`。
- `yt-dlp` 行为异常：优先运行 `--doctor`，必要时使用脚本提供的更新选项。

## 默认 Provider 失效

如果已保存默认 provider 但运行时 blocked：

- 检查 `auth_env` 对应的环境变量是否存在。
- 检查 endpoint label 是否仍匹配 key 区域。
- 使用 `--ignore-default-provider --transcribe-provider <provider>` 临时改用其它 provider。
- 使用 `--clear-default-provider` 清除默认值。
- 使用显式 provider 加 `--save-default-provider` 保存新默认值。

默认 provider 文件只能保存环境变量名和 endpoint label，不能保存真实 key。

## MiniMax Endpoint

MiniMax 有国内和海外 endpoint。国内版默认：

```text
https://api.minimaxi.com/v1
```

海外版常用：

```text
https://api.minimax.io/v1
```

不能确认区域时不要静默猜测，应在 checkpoint 中说明：

- 当前可见的 `MINIMAX_BASE_URL`。
- 是否存在 `MINIMAX_TRANSCRIBE_URL`。
- 将使用的 `MINIMAX_ASR_MODEL`。
- 不确定时给出配置、换后端、跳过转写或报告阻塞的退化菜单。

## DeepSeek / GLM / Gemini / Claude

这些 provider 必须按能力边界处理：

- 没有可用音频/视频 endpoint 时，标记为 `unsupported-direct` 或 `requires-proxy`。
- 通过 OpenAI-compatible 或 custom-proxy 接入时，必须提供 endpoint、认证环境变量和 model。
- 使用理解式转写时，在完成汇报中说明不是专用逐字 ASR。
- 不要把只支持文本生成的模型伪装成音频转字幕。

## OpenAI-compatible / Custom Proxy

最小执行路径使用 OpenAI-style multipart 请求：

```powershell
python scripts/transcript.py --transcribe-provider openai-compatible --transcribe-mode openai-compatible --transcribe-endpoint "<proxy-transcribe-url>" --transcribe-auth-env OPENAI_COMPATIBLE_API_KEY "URL"
```

若代理不是 OpenAI-style multipart，请不要强行执行；应标记为 blocked，并新增适配器或让用户提供兼容 endpoint。

## Cookie 与登录态

需要登录时优先使用最小授权范围：

```powershell
python scripts/transcript.py --cookies-from-browser chrome "URL"
```

不要记录 cookie、token、session value 或完整敏感 profile 路径。若网站涉及 DRM、付费限制或访问控制，不要尝试绕过。

## 字幕不可用

如果没有人工字幕：

1. 用 `--dry-run` 预览候选 provider、输出路径和风险。
2. 如果没有默认 provider，让用户选择 provider/API 凭据，并保存为默认 provider。
3. 向用户确认是否下载媒体并上传 API/代理。
4. 记录 fallback 原因和最终 provider。

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
