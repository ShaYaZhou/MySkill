## Context

当前 `video-transcript` 已能生成 Markdown 转写，并支持人工字幕、OpenAI/MiniMax audio-asr、Moonshot/Kimi video-understanding 和代理方案。问题在于输出命名和 metadata 只表达“转写成功”，没有把“原始 ASR”“轻整理演讲稿”“章节讲义/HTML”分成不同 artifact。用户看到 `ch01-测光基础概念.md` 时容易以为这是 ASR 质量变化，但它实际更像二次整理稿。

本变更只治理 `video-transcript` 的产物分层和轻量派生能力。公开视频下载 fallback、provider 选择、多厂商 API 已由既有变更处理，本文不重新定义。

## Goals / Non-Goals

**Goals:**

- 明确三层产物：`raw_asr`、`speech_transcript`、`chapter_handout`，以及 HTML 派生。
- 增加可组合输出 profile，允许用户选择只要原始 ASR、只要演讲稿、只要章节讲义，或全部生成。
- 让每个产物在 metadata/run-summary 中有独立记录，说明来源、provider、允许改写范围和路径。
- Kimi/Moonshot 产物必须标注为 `video-understanding` 或 LLM 派生，不得冒充严格 ASR。
- 保持普通调用的默认体验稳定：默认仍生成可阅读 Markdown，但 summary 要说明是否包含 raw ASR。

**Non-Goals:**

- 不实现复杂的多章内容策划系统；章节讲义先用单文件或简单分章规则生成。
- 不承诺 Kimi 可以输出严格逐字稿。
- 不引入新的外部依赖。
- 不改 `yt-dlp-download`。
- 不强制所有 provider 都能生成所有 artifact；不支持的组合必须记录为 skipped/blocked。

## Decisions

### 1. 使用 artifact profile 而不是隐式文件名推断

新增 `--output-profile`，可选值为 `raw`、`speech`、`chapters`、`html`、`all`。同时提供可重复的 `--artifact` 参数以便组合，例如 `--artifact raw_asr --artifact speech_transcript`。如果两者同时出现，以显式 `--artifact` 为准。

理由：用户心智上更容易理解“我要哪类产物”，而不是通过文件名猜测流程。

### 2. 原始 ASR 和演讲稿分开保存

严格 ASR 写 `original.asr.md`；现有 `original.md` 保持兼容，指向默认主产物或复制主产物内容。忠实演讲稿写 `speech.md`。Kimi 直接视频理解生成的内容只能写 `speech.md` 或 `original.kimi.md` 这类标注文件，不写成 `original.asr.md`。

理由：`original.md` 已被既有流程依赖，不能立刻破坏；但新文件名必须表达真实层级。

### 3. 章节讲义只从已有文本派生

章节讲义输入优先级为 `speech.md`、`original.asr.md`、人工字幕转写正文。章节讲义不直接声称来自音频；它是 LLM/规则派生产物，输出到 `chapters/ch01-<safe-title>.md`。请求 HTML 时从章节 Markdown 派生 `chapters/ch01-<safe-title>.html`。

理由：这能把“听写”与“内容重构”分离，便于复查。

### 4. allowed_transform 写进每个 artifact

artifact metadata 使用稳定字段：

- `artifact_type`
- `path`
- `source_artifact`
- `source_type`
- `provider`
- `model`
- `allowed_transform`
- `derivation_stage`
- `status`

典型 `allowed_transform`：

- `none_or_timestamp_only`
- `light_cleanup_no_reorder`
- `summarize_restructure_add_tables`
- `html_render_from_markdown`

### 5. Kimi 默认进入 speech/chapters，而非 raw_asr

当 provider 是 `moonshot` 且 mode 是 `video-understanding` 时，默认 artifact 是 `speech_transcript`。如果用户要求 `raw`，脚本必须提示/记录该 provider 不是严格 ASR，并尝试使用可用 ASR provider 或将 raw artifact 标记为 blocked。

## Risks / Trade-offs

- [Risk] 文件数量增加导致用户迷路 → 在 `metadata.json` 和完成汇报中列出 artifact 清单和主产物。
- [Risk] 兼容旧流程时 `original.md` 语义模糊 → 保留兼容文件，但新增 metadata 字段说明它对应的 artifact。
- [Risk] 章节讲义被误认为逐字稿 → 文件放入 `chapters/`，metadata 标注 `chapter_handout` 和 `summarize_restructure_add_tables`。
- [Risk] Kimi 仍可能改写演讲稿 → speech metadata 必须标注 `video-understanding`，并在 warnings 中写明“非严格 ASR”。
- [Risk] 实现范围变大 → 第一版只实现单章讲义和简单 HTML 派生，不做复杂多章规划。

## Migration Plan

1. 新增 artifact layer reference 和示例字段。
2. 在脚本中增加 profile/artifact 参数、artifact 记录 helper 和输出路径。
3. 将现有转写结果写入对应层级：ASR/人工字幕/OpenAI/MiniMax 进入 `raw_asr`，Kimi video-understanding 进入 `speech_transcript`。
4. 增加 speech 和 chapter 派生函数，优先复用已有文本，不重复上传媒体。
5. 更新 examples、doctor/dry-run 文案和 validation。
6. 同步安装到本地 skill 目录并跑 smoke test。

## Open Questions

- 多章拆分是否后续接入 `content-plan.md`，由用户确认章节目录后再批量生成。
- `original.md` 长期应该固定为 raw ASR，还是保留为“默认主产物”兼容入口。
