---
name: video-transcript
description: Use this skill when the user provides one or more video or playlist URLs and wants a written transcript, talk script, lecture notes, or bilingual transcript document. It prefers existing human subtitles, falls back to OpenAI audio transcription, Kimi video transcription, or a configured MiniMax CLI command when subtitles are missing, writes Markdown transcript files, and can create a Chinese version when the original language is not Chinese.
---

# Video Transcript

## Overview

Create Markdown transcript documents from video or playlist URLs. Prefer existing human subtitles because they are fast and free; if no human subtitle is available, use a configured transcription fallback.

## Default Workflow

Run the helper from this skill directory:

```bash
python scripts/transcript.py "VIDEO_OR_PLAYLIST_URL"
```

For multiple URLs, pass them in one command:

```bash
python scripts/transcript.py "URL_1" "URL_2"
```

The script creates and maintains an isolated `.venv` inside the skill directory, then installs or updates `yt-dlp[default]` and `openai`. Transcript outputs go to `~/Documents/video-transcripts` unless the user asks for another location.

## Transcript Policy

- Use human subtitles first; do not use platform-generated automatic subtitles by default.
- If human subtitles exist, convert them into a clean `original.md`.
- If no human subtitles exist, use `--transcribe-backend auto`: OpenAI audio transcription when `OPENAI_API_KEY` exists, otherwise Kimi video transcription when `MOONSHOT_API_KEY` exists, otherwise MiniMax CLI transcription when `MINIMAX_CLI_COMMAND` is set or a supported MiniMax CLI executable is available.
- Default OpenAI transcription model is `gpt-4o-mini-transcribe`; use `--transcribe-model gpt-4o-transcribe` when the user prioritizes accuracy.
- Default Kimi model is `kimi-k2.6`; Kimi video transcription uses multimodal video understanding, not a dedicated ASR endpoint, so prefer human subtitles or OpenAI ASR when exact wording matters.
- Kimi/Moonshot keys can belong to different regions. The script auto-probes `https://api.moonshot.ai/v1` and `https://api.moonshot.cn/v1`; set `MOONSHOT_BASE_URL` explicitly if the user has a known endpoint.
- MiniMax CLI transcription is command-template based because CLI subcommands can vary by installed version. The command must read an audio file from `{audio}` and either print transcript text to stdout or write it to `{output}`.
- Preserve original audio quality where possible. Only when the upload would exceed the safe 24 MB threshold should the script split audio; if split chunks are still too large, compress to speech-friendly mono audio.
- If the original transcript is non-Chinese and `MOONSHOT_API_KEY` exists, the script translates `original.md` into natural Chinese with Kimi and saves `zh.md`; otherwise Codex should translate it after the script exits.
- For playlists, process each video into its own directory and continue after individual failures.
- Never write API keys into the Skill files. Read `OPENAI_API_KEY`, `MOONSHOT_API_KEY`, or MiniMax CLI credentials from the local environment or CLI auth store.

## MiniMax CLI Configuration

Use MiniMax CLI explicitly:

```bash
python scripts/transcript.py --transcribe-backend minimax-cli "VIDEO_OR_PLAYLIST_URL"
```

If the installed CLI's transcription command differs from the default, configure a command template with `MINIMAX_CLI_COMMAND` or `--minimax-cli-command`:

```bash
MINIMAX_CLI_COMMAND='["mmx","speech","transcribe","--audio","{audio}","--out","{output}"]'
python scripts/transcript.py --transcribe-backend minimax-cli "VIDEO_OR_PLAYLIST_URL"
```

Supported placeholders:

- `{audio}`: local audio file path.
- `{output}`: text file path where the CLI may write the transcript.
- `{model}`: value from `--minimax-model` or `MINIMAX_MODEL`.
- `{language}`: value from `--transcribe-language` or `TRANSCRIBE_LANGUAGE`.
- `{part_index}` and `{part_count}`: current chunk position when audio is split.

JSON-array command templates avoid shell quoting issues and are preferred. String templates are also supported, and the script quotes `{audio}` and `{output}` automatically.

## Options

Use these script options when the user asks for a variation:

- `--output-dir PATH` saves files somewhere other than `~/Documents/video-transcripts`.
- `--cookies-from-browser BROWSER` loads cookies from a browser such as `chrome`, `safari`, `firefox`, or `edge`.
- `--transcribe-backend auto|openai|kimi-video|minimax-cli` chooses the no-subtitle fallback.
- `--transcribe-model MODEL` changes the OpenAI transcription model.
- `--kimi-model MODEL` changes the Kimi/Moonshot model, default `kimi-k2.6`.
- `--minimax-cli-command COMMAND` sets the MiniMax CLI transcript command template. `MINIMAX_CLI_COMMAND` is the environment-variable equivalent.
- `--minimax-model MODEL` passes a MiniMax model name into `{model}`. `MINIMAX_MODEL` is the environment-variable equivalent.
- `--transcribe-language LANG` passes a language hint into `{language}`. `TRANSCRIBE_LANGUAGE` is the environment-variable equivalent.
- `--timestamps` keeps subtitle cue timestamps or part markers in the transcript.
- `--keep-audio` preserves intermediate audio files.
- `--update` updates isolated dependencies before processing.

## After Running

Inspect each video's `metadata.json`:

- If `needs_zh_translation` is `false`, the script already produced every requested document.
- If `needs_zh_translation` is `true`, read `original.md`, translate it faithfully into Chinese, and write `zh.md` to the `zh_path` shown in metadata.
- Keep the Markdown structure simple: title, source metadata, then transcript text. Do not invent content missing from the original.

## Troubleshooting

- If no subtitle exists and neither `OPENAI_API_KEY` nor `MOONSHOT_API_KEY` is set, check whether `MINIMAX_CLI_COMMAND` is configured or a MiniMax CLI executable is available.
- If MiniMax CLI returns an error, run the configured command manually with a small audio file and verify that it prints transcript text or writes `{output}`.
- If Kimi returns authentication errors, test whether the key belongs to the `.cn` or `.ai` endpoint and set `MOONSHOT_BASE_URL` if needed.
- If the user pasted an API key into chat, advise rotating it and setting it locally as an environment variable instead of storing it in the Skill.
- If a site requires login, retry with `--cookies-from-browser chrome` or the browser the user is signed into.
- If media extraction, compression, or splitting fails, ensure `ffmpeg` and `ffprobe` are installed and available in `PATH`.
- If a site recently changed behavior, retry with `--update`.
- Do not suggest bypassing DRM-protected content.
