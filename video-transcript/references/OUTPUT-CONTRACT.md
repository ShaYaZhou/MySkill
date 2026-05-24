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
├── original.asr.md
├── speech.md
├── chapters/
│   ├── ch01-<title>.md
│   └── ch01-<title>.html
├── zh.md
├── metadata.json
└── _work/                # 临时文件，可能不存在或运行后清理
```

批量运行可以在输出根目录写入：

```text
run-summary.json
transcript-summary.json
```

## `metadata.json`

必填字段：

- `title`
- `url`
- `video_id`
- `original_path`
- `original_asr_path` 或 `artifacts[].path`
- `zh_path`
- `source`
- `needs_zh_translation`
- `status`
- `artifacts`

API/代理转写字段：

- `transcribe_provider`
- `transcribe_mode`
- `transcribe_model`
- `provider_capability_type`
- `provider_selection_source`
- `default_provider_used`
- `default_credential_label`
- `auth_env`
- `media_downloaded`
- `media_uploaded`
- `endpoint_label`
- `proxy_used`
- `selection_warnings`

常用可选字段：

- `original_language`
- `zh_source`
- `kimi_model`
- `minimax_model`
- `minimax_endpoint_label`
- `metadata_source`
- `public_api_fallback_used`
- `public_api_adapter`
- `public_api_stage`
- `public_api_endpoint_label`
- `public_api_status`
- `public_api_requires_login`
- `public_api_uses_cookie`
- `requires_web_access`
- `subtitle_state`
- `media_url_state`
- `fallback_failures`
- `error`
- `provider_checkpoint`
- `requested_output_profile`
- `requested_artifacts`
- `primary_artifact`
- `original_mirrors_artifact`

`artifacts[]` 字段：

- `artifact_type`: `raw_asr`、`speech_transcript`、`chapter_handout`、`html_render`
- `path`
- `source_artifact`
- `source_type`
- `provider`
- `model`
- `allowed_transform`
- `derivation_stage`
- `status`
- `reason`

稳定状态值：

- `metadata.status`: `success`、`failed`、`blocked`、`skipped`
- `run-summary.status`: `success`、`partial_failure`、`dry_run`、`ok`、`blocked`
- `item.status`: `success`、`failed`、`blocked`、`skipped`、`would_process`、`requires_confirmation`、`requires-proxy`、`uncertain`
- `source`: `human_subtitle`、`public_api_subtitle`、`openai_transcription`、`kimi_video_transcription`、`minimax_api_transcription`、`<provider>_proxy_transcription`
- `provider_selection_source`: `cli-explicit`、`saved-default`、`user-confirmed-default`、`conversation-explicit`、`dry-run-confirmed`
- `provider_capability_type`: `audio-asr`、`video-understanding`、`audio-to-llm`、`openai-compatible`、`custom-proxy`、`unsupported-direct`
- `metadata_source`: `yt_dlp`、`public_api`
- `public_api_status`: `not-used`、`planned`、`ok`、`partial`、`disabled`、`unsupported-public-api`、`invalid-url`、`api-failed`
- `subtitle_state`: `unknown`、`available`、`empty`、`requires-web-access`、`missing-cid`、`api-failed`
- `media_url_state`: `unknown`、`available`、`empty`、`requires-web-access`、`missing-cid`、`api-failed`
- `artifact_type`: `raw_asr`、`speech_transcript`、`chapter_handout`、`html_render`
- `allowed_transform`: `none_or_timestamp_only`、`light_cleanup_no_reorder`、`summarize_restructure_add_tables`、`html_render_from_markdown`
- `artifact.status`: `generated`、`planned`、`skipped`、`blocked`

禁止记录：

- API key、token、cookie、session value。
- 完整敏感浏览器 profile 路径。
- 带鉴权 query 的完整 endpoint。
- 完整临时媒体 URL、签名 query 或可复用下载凭据。
- 私密 HTML 内容。

## `run-summary.json`

建议字段：

```json
{
  "schema_version": 1,
  "tool": "video-transcript",
  "status": "dry_run",
  "started_at": "2026-01-01T00:00:00Z",
  "finished_at": "2026-01-01T00:01:00Z",
  "cwd": "D:/git/MySkill",
  "argv": ["--dry-run", "--transcribe-provider", "minimax", "https://example.invalid/watch"],
  "requested_backend": "auto",
  "requested_provider": "minimax",
  "requested_mode": "audio-asr",
  "requested_output_profile": "all",
  "requested_artifacts": ["raw_asr", "speech_transcript", "chapter_handout", "html_render"],
  "transcribe_provider": null,
  "transcribe_mode": null,
  "default_provider_path": "C:/Users/example/AppData/Roaming/MySkill/video-transcript/provider-default.json",
  "default_provider_used": false,
  "items": [
    {
      "url": "https://example.invalid/watch",
      "status": "would_process",
      "source": "minimax_audio-asr",
      "transcribe_provider": "minimax",
      "transcribe_mode": "audio-asr",
      "provider_selection_source": "cli-explicit",
      "default_provider_used": false,
      "auth_env": "MINIMAX_API_KEY",
      "endpoint_label": "api.minimaxi.com",
      "media_uploaded": true,
      "artifact_plan": [
        {
          "artifact_type": "raw_asr",
          "path": "D:/example-output/example/original.asr.md",
          "source_artifact": null,
          "source_type": "audio-asr",
          "provider": "minimax",
          "model": "speech-2.8-turbo",
          "allowed_transform": "none_or_timestamp_only",
          "derivation_stage": "primary",
          "provider_capability_type": "audio-asr",
          "status": "planned"
        },
        {
          "artifact_type": "speech_transcript",
          "path": "D:/example-output/example/speech.md",
          "source_artifact": "raw_asr",
          "source_type": "raw_asr",
          "provider": "local-cleanup",
          "model": null,
          "allowed_transform": "light_cleanup_no_reorder",
          "derivation_stage": "derived",
          "provider_capability_type": "audio-asr",
          "status": "planned"
        },
        {
          "artifact_type": "chapter_handout",
          "path": "D:/example-output/example/chapters/ch01-example.md",
          "source_artifact": "speech_transcript",
          "source_type": "speech_transcript",
          "provider": "moonshot-or-local-structured-fallback",
          "model": null,
          "allowed_transform": "summarize_restructure_add_tables",
          "derivation_stage": "derived",
          "provider_capability_type": "audio-asr",
          "status": "planned"
        },
        {
          "artifact_type": "html_render",
          "path": "D:/example-output/example/chapters/ch01-example.html",
          "source_artifact": "chapter_handout",
          "source_type": "chapter_handout",
          "provider": "local-html-render",
          "model": null,
          "allowed_transform": "html_render_from_markdown",
          "derivation_stage": "derived",
          "provider_capability_type": "audio-asr",
          "status": "planned"
        }
      ],
      "artifacts": [],
      "selection_warnings": []
    }
  ],
  "failures": [],
  "uncertain": []
}
```

`argv` 必须规范化并脱敏。只记录环境变量名或是否存在，不能记录 secret。

## 默认 Provider 偏好

默认 provider 偏好是用户本机非敏感配置，不属于 skill 仓库产物。推荐结构：

```json
{
  "schema_version": 1,
  "default_provider": "minimax",
  "default_mode": "audio-asr",
  "auth_env": "MINIMAX_API_KEY",
  "model": "speech-2.8-turbo",
  "model_env": "MINIMAX_ASR_MODEL",
  "endpoint_label": "api.minimaxi.com",
  "selection_source": "user-confirmed-default",
  "updated_at": "2026-05-22T00:00:00Z"
}
```

不得把真实 API key 或 cookie 写入该文件。

## 完成契约

汇报成功前必须确认：

- 每个尝试处理的视频都有 `metadata.json`。
- 成功项的 `original.md` 非空。
- 如果使用 API/代理，provider 字段完整且 endpoint 脱敏。
- 如果使用默认 provider，summary 或 metadata 记录 `default_provider_used`。
- 失败项包含错误文本和最小可执行下一步。
- 不确定的后端、公式、语言或路径显式标记。
