# 输出契约

本文档定义 `video-transcript` 的文件输出、事实源和机器可读字段。运行事实以每视频 `metadata.json` 为准；批量事实以 `run-summary.json` 或同等聚合 summary 为准。

## 目录结构

默认输出根目录：

```text
~/Documents/video-transcripts/
```

每个视频写入独立目录：

```text
<title> [<video-id>]/
├── original.md
├── zh.md
├── metadata.json
└── .work/                 # 临时文件，可能不存在或运行后清理
```

批量运行可以在输出根目录写入：

```text
run-summary.json
```

## `metadata.json`

必填字段：

- `title`
- `url`
- `video_id`
- `original_path`
- `zh_path`
- `source`
- `needs_zh_translation`
- `status`

常用可选字段：

- `original_language`
- `zh_source`
- `transcribe_model`
- `kimi_model`
- `minimax_model`
- `minimax_base_url`
- `minimax_transcribe_url`
- `error`

稳定状态值：

- `status`: `ok`、`failed`、`skipped`
- `source`: `human_subtitle`、`openai_transcription`、`kimi_video_transcription`、`minimax_api_transcription`
- `language_state`: `zh_complete`、`needs_zh_translation`、`unknown`
- `privacy_gate`: `none`、`cookies`、`api_upload`、`login_required`

禁止记录：

- API key、token、cookie、session value。
- 完整敏感浏览器 profile 路径。
- 私密 HTML 内容。

## `run-summary.json`

建议字段：

```json
{
  "schema_version": 1,
  "tool": "video-transcript",
  "status": "ok",
  "started_at": "2026-01-01T00:00:00Z",
  "completed_at": "2026-01-01T00:00:00Z",
  "cwd": "D:/git/MySkill/video-transcript",
  "argv": ["scripts/transcript.py", "--dry-run", "https://example.invalid/watch"],
  "env": {
    "OPENAI_API_KEY": "present",
    "MOONSHOT_API_KEY": "missing",
    "MINIMAX_API_KEY": "missing"
  },
  "items": [
    {
      "url": "https://example.invalid/watch",
      "status": "ok",
      "metadata_path": "D:/out/example/metadata.json",
      "original_path": "D:/out/example/original.md",
      "zh_path": "D:/out/example/zh.md",
      "source": "human_subtitle",
      "needs_zh_translation": false,
      "warnings": []
    }
  ],
  "failures": [],
  "warnings": []
}
```

`argv` 必须规范化并脱敏。只记录环境变量是否存在，不能记录 secret。

## Completion Contract

Before reporting success:

- `metadata.json` exists for each attempted video.
- Successful items have non-empty `original.md`.
- If `needs_zh_translation` is false and Chinese output was expected, `zh.md` exists.
- Failures include error text and a smallest useful next action.
- Any uncertain backend, formula, language, or path is marked explicitly.
