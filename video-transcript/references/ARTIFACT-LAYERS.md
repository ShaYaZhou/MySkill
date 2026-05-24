# 产物分层

本文档定义 `video-transcript` 的四类文本/展示产物，避免把原始 ASR、演讲稿和章节讲义混称为“转写稿”。

## 四类 artifact

| artifact_type | 默认文件 | 定位 | 允许改写 |
| --- | --- | --- | --- |
| `raw_asr` | `original.asr.md` | 原始语音转文字或人工字幕转写 | `none_or_timestamp_only`，尽量逐字，最多保留/整理时间戳 |
| `speech_transcript` | `speech.md` | 忠实演讲稿，类似 `a.md` | `light_cleanup_no_reorder`，可轻清洗标点和段落，不重排知识结构 |
| `chapter_handout` | `chapters/ch01-*.md` | 章节讲义，类似 `ch01-测光基础概念.md` | `summarize_restructure_add_tables`，可章节化、提炼、加表格和小结 |
| `html_render` | `chapters/ch01-*.html` | 由章节 Markdown 派生的展示页 | `html_render_from_markdown`，只做渲染，不改变事实 |

`original.md` 保留为兼容入口，但 metadata 必须写明它镜像的是哪一类 artifact。新流程不能只看 `original.md` 判断产物类型。

## Provider 边界

- 严格 ASR：人工字幕、本地 `faster-whisper`、OpenAI `audio-asr`、MiniMax `audio-asr`、明确声明为 ASR 的兼容代理。
- 理解式转写：Moonshot/Kimi `video-understanding`、Gemini `audio-to-llm` 等。它们可以生成 `speech_transcript` 或 `chapter_handout`，但不得标记为 `raw_asr`。
- 章节讲义：必须从已有文本 artifact 派生，不能直接声称来自音频逐字识别。

## 选择参数

```powershell
python scripts/transcript.py --output-profile raw "URL"
python scripts/transcript.py --output-profile speech "URL"
python scripts/transcript.py --output-profile chapters "URL"
python scripts/transcript.py --output-profile html "URL"
python scripts/transcript.py --output-profile all "URL"
```

也可以显式组合：

```powershell
python scripts/transcript.py --artifact raw --artifact speech --artifact chapters "URL"
```

`--artifact` 出现时优先于 `--output-profile`。`html` 会需要 `chapter_handout` 作为来源；如果来源不存在，系统会先生成必要的中间 artifact 或记录 skipped/blocked。

## Metadata 字段

每个 artifact 都必须记录：

```json
{
  "artifact_type": "speech_transcript",
  "path": "C:/out/video/speech.md",
  "source_artifact": "raw_asr",
  "source_type": "raw_asr",
  "provider": "local-cleanup",
  "model": null,
  "allowed_transform": "light_cleanup_no_reorder",
  "derivation_stage": "derived",
  "status": "generated"
}
```

如果 artifact 无法生成，`status` 使用 `skipped` 或 `blocked`，并写入 `reason`。

## 汇报规则

完成汇报必须说清：

- 哪个文件是原始 ASR。
- 哪个文件是演讲稿。
- 哪个文件是章节讲义或 HTML。
- Kimi/Moonshot 参与时，说明它是理解式转写或派生整理，不是严格 ASR。
