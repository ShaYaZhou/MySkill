---
name: yt-dlp-download
description: Use this skill when the user provides one or more video or playlist URLs and wants to download videos with yt-dlp. It downloads MP4-preferred video by default, saves human subtitles when available, downloads thumbnails, supports playlist batch downloads, and can use browser cookies for login-restricted sites.
---

# yt-dlp Download

## Overview

Download video or playlist URLs with yt-dlp through the bundled helper script. Default behavior is tuned for everyday use: MP4-compatible formats first, human subtitles only, thumbnails saved, playlist batch handling, and duplicate downloads avoided with an archive file.

## Default Workflow

Run the helper from this skill directory:

```bash
python scripts/download.py "VIDEO_OR_PLAYLIST_URL"
```

For multiple URLs, pass them in one command:

```bash
python scripts/download.py "URL_1" "URL_2"
```

The script creates and maintains an isolated `.venv` inside the skill directory, then installs or updates `yt-dlp[default]` there. Downloads go to `~/Downloads/yt-dlp` unless the user asks for another location.

## Download Policy

- Prefer MP4-compatible output while keeping best practical quality.
- Download human subtitles only; do not download automatic/generated subtitles.
- Subtitle preference is Chinese first, then English. If no matching human subtitles exist, continue without subtitles.
- Download thumbnails by default.
- Treat playlist URLs as batch downloads by default.
- Use `.yt-dlp-archive.txt` in the output directory to skip already downloaded videos.
- Keep subtitles and thumbnails as sidecar files rather than embedding them into the media.

## Options

Use these script options when the user asks for a variation:

- `--output-dir PATH` saves files somewhere other than `~/Downloads/yt-dlp`.
- `--audio-only` extracts audio-only files.
- `--no-thumbnail` skips thumbnail download.
- `--sub-lang LANG` requests a specific human subtitle language instead of the Chinese-then-English default.
- `--cookies-from-browser BROWSER` loads cookies from a browser such as `chrome`, `safari`, `firefox`, or `edge`.
- `--update` updates the isolated yt-dlp package before downloading.

## Troubleshooting

- If a site requires login, retry with `--cookies-from-browser chrome` or the browser the user is signed into.
- If a download fails because formats must be merged, ensure `ffmpeg` and `ffprobe` are installed and available in `PATH`.
- If a site recently changed behavior, retry with `--update`.
- Do not suggest downloading DRM-protected content; yt-dlp cannot bypass DRM.
