## Why

`video-transcript` 现在把“原始逐字转写”“Kimi 理解式讲稿”“章节讲义/HTML”都容易混叫成转写稿，导致用户比较产物质量时会把 ASR、演讲稿和二次整理稿放在同一层评价。最近对比 `original.md`、`a.md` 和 `ch01-测光基础概念.md` 后可以确认，这三类文件需要明确分层、命名、metadata 和生成开关。

## What Changes

- 为 `video-transcript` 增加三层产物模型：
  - 原始 ASR 层：尽量逐字、保留时间戳和口语痕迹，输出 `original.asr.md`。
  - 忠实演讲稿层：类似 `a.md`，按时间线轻清洗、保留讲述顺序，输出 `speech.md` 或 provider 标记文件。
  - 章节讲义层：类似 `ch01-测光基础概念.md`，允许章节化、提炼、表格、小结和 HTML 派生，输出到 `chapters/`。
- 新增输出 profile / artifact 选择参数，让用户可以选择 `raw`、`speech`、`chapters`、`html` 或 `all`。
- 让 metadata 和 run-summary 对每个产物记录 `artifact_type`、`source_artifact`、`source_type`、`provider`、`allowed_transform`、`derivation_stage` 和路径，避免把派生产物误报为原始转写。
- 明确 Kimi/Moonshot 的定位：可以生成理解式讲稿或章节讲义，但不得被标记为严格 ASR；严格 ASR 优先来自人工字幕、本地 faster-whisper、MiniMax audio-asr、OpenAI audio-asr 或兼容 ASR 代理。
- 更新 `SKILL.md`、reference、examples 和验证脚本，要求完成汇报区分三层产物。

## Capabilities

### New Capabilities

- `transcript-artifact-layers`：定义 `video-transcript` 生成原始 ASR、忠实演讲稿、章节讲义和 HTML 派生产物时的层级、命名、生成开关、metadata 字段和安全边界。

### Modified Capabilities

- 无。

## Impact

- 影响 `video-transcript/scripts/transcript.py` 的 CLI 参数、输出路径、metadata/run-summary 写入和派生产物生成流程。
- 影响 `video-transcript/SKILL.md`、`references/OUTPUT-CONTRACT.md`、`references/BACKENDS.md`、示例 JSON 和完成检查。
- 可能新增 `video-transcript/references/ARTIFACT-LAYERS.md`，专门说明三层产物的用途、允许改写范围和文件命名。
- 不影响 `yt-dlp-download` 的下载职责。
