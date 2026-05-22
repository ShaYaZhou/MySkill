# 转写后端与 Provider 注册表

`video-transcript` 的默认策略是先使用确定性最高、成本最低的来源，再进入需要下载、上传或付费的后端。

## 决策顺序

1. 人工字幕。
2. 用户显式选择的 `--transcribe-provider` / `--transcribe-mode`。
3. 用户级默认 provider 偏好。
4. 无默认时的 provider 选择 checkpoint。

不要默认使用平台自动生成字幕。只有用户明确接受，或后续单独扩展策略时，才把自动字幕作为候选。

## 首次默认 provider

没有人工字幕且需要 API/代理转写时，如果用户没有显式选择，也没有已保存默认 provider，必须先暂停并让用户选择一个默认 API 凭据。这里的“凭据”只指向环境变量名或凭据标签，例如 `MINIMAX_API_KEY`，不得保存真实 key 值。

默认 provider 偏好只允许记录：

- provider id。
- mode。
- 认证环境变量名。
- 模型名或模型环境变量名。
- endpoint label 或脱敏 host。
- 选择来源和更新时间。

后续再次缺人工字幕时，如果默认 provider 可用，可以直接调用；但大型播放列表、登录/cookie、覆盖已有产物、默认 key 缺失、endpoint 区域不明或 provider 能力不支持仍必须重新 checkpoint。

## Provider 注册表

| Provider | 默认 mode | 能力类型 | 认证变量 | 默认模型 | 直接执行状态 |
| --- | --- | --- | --- | --- | --- |
| `openai` | `audio-asr` | 专用音频 ASR | `OPENAI_API_KEY` | `gpt-4o-mini-transcribe` | 可直接执行 |
| `moonshot` | `video-understanding` | 视频理解转写 | `MOONSHOT_API_KEY` | `kimi-k2.6` | 可直接执行，但非专用逐字 ASR |
| `minimax` | `audio-asr` | 专用音频 ASR | `MINIMAX_API_KEY` | `speech-2.8-turbo` | 可直接执行 |
| `deepseek` | `unsupported-direct` | 默认不声明音视频能力 | `DEEPSEEK_API_KEY` | `deepseek-chat` | 需要代理或自定义 endpoint |
| `glm` | `unsupported-direct` | 默认不声明音视频能力 | `GLM_API_KEY` | `glm-4` | 需要代理或自定义 endpoint |
| `gemini` | `audio-to-llm` | 理解式转写 | `GEMINI_API_KEY` | `gemini-2.5-flash` | 首版通过代理/兼容 endpoint 执行 |
| `claude` | `unsupported-direct` | 默认不声明音视频能力 | `ANTHROPIC_API_KEY` | `claude-sonnet-4-5` | 需要代理或自定义 endpoint |
| `openai-compatible` | `openai-compatible` | OpenAI 兼容代理 | `OPENAI_COMPATIBLE_API_KEY` | `gpt-4o-mini-transcribe` | 需要 base URL 或转写 endpoint |
| `custom-proxy` | `custom-proxy` | 自定义代理 | `CUSTOM_TRANSCRIBE_API_KEY` | `transcribe` | 需要明确 endpoint |

## 旧参数兼容

旧 `--transcribe-backend` 继续可用，并映射为：

| 旧 backend | provider | mode |
| --- | --- | --- |
| `openai` | `openai` | `audio-asr` |
| `kimi-video` | `moonshot` | `video-understanding` |
| `minimax-api` | `minimax` | `audio-asr` |

如果旧 backend 与新 provider/mode 参数互相冲突，脚本必须报错，不得静默选择任一方案。

## 代理与多厂商

DeepSeek、GLM、Gemini、Claude 可以出现在候选列表里，但不能把“文本模型”伪装成 ASR：

- 如果用户提供 OpenAI-compatible 或 custom-proxy 转写 endpoint，可按代理执行。
- 如果 provider 只支持文本生成，必须标记为 `unsupported-direct` 或 `requires-proxy`。
- 如果使用 `video-understanding` 或 `audio-to-llm`，完成汇报必须说明这不是专用逐字 ASR。

## 数学公式

所有 API/代理后端都应使用包含数学保留规则的 prompt：

- 行内公式：`$...$`
- 块级公式：`$$...$$`
- 保留变量名、单位、上下标、定理名和推导上下文。

如果公式识别风险高，在完成汇报中标为风险，不要把不确定公式描述为已验证。
