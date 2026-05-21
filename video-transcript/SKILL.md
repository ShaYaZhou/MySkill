---
name: video-transcript
description: Use this skill when the user provides one or more video or playlist URLs and wants a written transcript, talk script, lecture notes, or bilingual transcript document. It prefers existing human subtitles, falls back to OpenAI audio transcription, Kimi video transcription, or MiniMax API transcription when subtitles are missing, writes Markdown transcript files, and can create a Chinese version when the original language is not Chinese.
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
- If no human subtitles exist, use `--transcribe-backend auto`: OpenAI audio transcription when `OPENAI_API_KEY` exists, otherwise Kimi video transcription when `MOONSHOT_API_KEY` exists, otherwise MiniMax API transcription when `MINIMAX_API_KEY` exists.
- Default OpenAI transcription model is `gpt-4o-mini-transcribe`; use `--transcribe-model gpt-4o-transcribe` when the user prioritizes accuracy.
- Default Kimi model is `kimi-k2.6`; Kimi video transcription uses multimodal video understanding, not a dedicated ASR endpoint, so prefer human subtitles or OpenAI ASR when exact wording matters.
- Kimi/Moonshot keys can belong to different regions. The script auto-probes `https://api.moonshot.ai/v1` and `https://api.moonshot.cn/v1`; set `MOONSHOT_BASE_URL` explicitly if the user has a known endpoint.
- MiniMax API transcription uses `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_TRANSCRIBE_URL`, and `MINIMAX_ASR_MODEL`. The default endpoint is OpenAI-compatible: `{MINIMAX_BASE_URL}/audio/transcriptions`.
- Ask transcription backends to preserve spoken math, equations, variables, symbols, and units as Markdown LaTeX: inline math as `$...$` and display equations as `$$...$$`.
- Preserve original audio quality where possible. Only when the upload would exceed the safe 24 MB threshold should the script split audio; if split chunks are still too large, compress to speech-friendly mono audio.
- If the original transcript is non-Chinese and `MOONSHOT_API_KEY` exists, the script translates `original.md` into natural Chinese with Kimi and saves `zh.md`; otherwise Codex should translate it after the script exits.
- For playlists, process each video into its own directory and continue after individual failures.
- Never write API keys into the Skill files. Read `OPENAI_API_KEY`, `MOONSHOT_API_KEY`, or `MINIMAX_API_KEY` from the local environment.

## MiniMax API Configuration

Use MiniMax API explicitly:

```bash
python scripts/transcript.py --transcribe-backend minimax-api "VIDEO_OR_PLAYLIST_URL"
```

Set the API key locally. Do not commit it:

```bash
export MINIMAX_API_KEY="..."
python scripts/transcript.py --transcribe-backend minimax-api "VIDEO_OR_PLAYLIST_URL"
```

Optional configuration:

- `MINIMAX_BASE_URL` or `--minimax-base-url`: API base URL, default `https://api.minimax.io/v1`.
- `MINIMAX_TRANSCRIBE_URL` or `--minimax-transcribe-url`: full ASR endpoint URL, default `{base}/audio/transcriptions`.
- `MINIMAX_ASR_MODEL` or `--minimax-model`: ASR model name, default `speech-2.8-turbo`.
- `TRANSCRIBE_LANGUAGE` or `--transcribe-language`: optional language hint.
- `TRANSCRIPTION_PROMPT` or `--transcription-prompt`: transcription prompt. The default prompt includes math-formula preservation rules.

MiniMax's public docs currently emphasize text generation, TTS, and file management rather than a dedicated ASR page, so keep `MINIMAX_TRANSCRIBE_URL` configurable if the account uses a custom or proxy ASR endpoint.

## Options

Use these script options when the user asks for a variation:

- `--output-dir PATH` saves files somewhere other than `~/Documents/video-transcripts`.
- `--cookies-from-browser BROWSER` loads cookies from a browser such as `chrome`, `safari`, `firefox`, or `edge`.
- `--transcribe-backend auto|openai|kimi-video|minimax-api` chooses the no-subtitle fallback.
- `--transcribe-model MODEL` changes the OpenAI transcription model.
- `--kimi-model MODEL` changes the Kimi/Moonshot model, default `kimi-k2.6`.
- `--minimax-base-url URL` changes the MiniMax API base URL.
- `--minimax-transcribe-url URL` changes the full MiniMax ASR endpoint URL.
- `--minimax-model MODEL` changes the MiniMax ASR model. `MINIMAX_ASR_MODEL` is the preferred environment-variable equivalent.
- `--transcribe-language LANG` passes a language hint to supported backends. `TRANSCRIBE_LANGUAGE` is the environment-variable equivalent.
- `--transcription-prompt PROMPT` overrides the default transcription prompt, including math formula formatting requirements.
- `--timestamps` keeps subtitle cue timestamps or part markers in the transcript.
- `--keep-audio` preserves intermediate audio files.
- `--update` updates isolated dependencies before processing.

## After Running

Inspect each video's `metadata.json`:

- If `needs_zh_translation` is `false`, the script already produced every requested document.
- If `needs_zh_translation` is `true`, read `original.md`, translate it faithfully into Chinese, and write `zh.md` to the `zh_path` shown in metadata.
- Keep the Markdown structure simple: title, source metadata, then transcript text. Do not invent content missing from the original.

## Troubleshooting

- If no subtitle exists and neither `OPENAI_API_KEY` nor `MOONSHOT_API_KEY` is set, check whether `MINIMAX_API_KEY` is configured.
- If MiniMax API returns 404 or model errors, verify `MINIMAX_TRANSCRIBE_URL` and `MINIMAX_ASR_MODEL`; MiniMax's public docs may not expose a universal ASR endpoint for every account.
- If formulas are misrecognized, rerun with `--transcription-prompt` containing the domain-specific notation, such as common variable names, theorem names, or expected equation forms.
- If Kimi returns authentication errors, test whether the key belongs to the `.cn` or `.ai` endpoint and set `MOONSHOT_BASE_URL` if needed.
- If the user pasted an API key into chat, advise rotating it and setting it locally as an environment variable instead of storing it in the Skill.
- If a site requires login, retry with `--cookies-from-browser chrome` or the browser the user is signed into.
- If media extraction, compression, or splitting fails, ensure `ffmpeg` and `ffprobe` are installed and available in `PATH`.
- If a site recently changed behavior, retry with `--update`.
- Do not suggest bypassing DRM-protected content.
