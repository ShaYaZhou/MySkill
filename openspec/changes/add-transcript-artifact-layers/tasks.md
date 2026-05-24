## 1. 文档与契约

- [x] 1.1 新增 `ARTIFACT-LAYERS.md`，说明 raw ASR、speech、chapters、HTML 的边界、命名和 metadata 字段。
- [x] 1.2 更新 `video-transcript/SKILL.md`，加入 `--output-profile`、`--artifact` 和三层产物说明。
- [x] 1.3 更新 `OUTPUT-CONTRACT.md` 与示例 JSON，加入 artifact 列表和 transform 字段。
- [x] 1.4 更新 `BACKENDS.md`，明确 Kimi/Moonshot 是 video-understanding，不得标记为严格 ASR。

## 2. CLI 与输出模型

- [x] 2.1 在 `transcript.py` 增加 `--output-profile` 与可重复 `--artifact` 参数。
- [x] 2.2 实现 artifact 选择解析函数，支持 `raw`、`speech`、`chapters`、`html`、`all`。
- [x] 2.3 增加 artifact metadata helper，统一记录 `artifact_type`、`source_artifact`、`allowed_transform`、`status` 和路径。
- [x] 2.4 保持 `original.md` 兼容，同时写入 `original.asr.md` 或 `speech.md` 等明确层级文件。

## 3. 生成流程

- [x] 3.1 将人工字幕、OpenAI、MiniMax 和兼容 ASR 的结果记录为 `raw_asr`。
- [x] 3.2 将 Kimi video-understanding 的直出结果记录为 `speech_transcript`，并保留非严格 ASR warning。
- [x] 3.3 实现从 raw ASR 到 `speech.md` 的轻清洗/复制派生路径。
- [x] 3.4 实现从 speech/raw 文本到 `chapters/ch01-*.md` 的章节讲义生成路径。
- [x] 3.5 实现从章节 Markdown 到 `chapters/ch01-*.html` 的简单 HTML 派生路径。
- [x] 3.6 在 dry-run 中展示计划生成的 artifact、来源和输出路径。

## 4. 验证与同步

- [x] 4.1 增加或更新脚本级验证，覆盖 profile 解析、artifact metadata、Kimi 非 ASR 标记和 HTML 派生。
- [x] 4.2 运行 `--help`、dry-run、仓库 validation 和 OpenSpec 校验。
- [x] 4.3 同步安装 `video-transcript` 到 Claude、Codex、Cursor、Mavis 本地 skill 目录。
- [x] 4.4 开 2 个 agent 做质检，并根据反馈修正问题。
- [x] 4.5 最终检查 `git status`，确认本次变更范围清晰。
