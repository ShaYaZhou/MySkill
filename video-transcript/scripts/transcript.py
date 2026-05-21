#!/usr/bin/env python3
"""Create Markdown transcripts from video or playlist URLs."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


SKILL_DIR = Path(__file__).resolve().parents[1]
VENV_DIR = SKILL_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
DEFAULT_OUTPUT_DIR = Path("~/Documents/video-transcripts").expanduser()
SAFE_UPLOAD_BYTES = 24 * 1024 * 1024
KIMI_SAFE_VIDEO_BYTES = 70 * 1024 * 1024
MOONSHOT_BASE_URLS = ("https://api.moonshot.ai/v1", "https://api.moonshot.cn/v1")
MINIMAX_BASE_URL = "https://api.minimax.io/v1"
ZH_PATTERNS = ("zh", "zh-*", "zh-Hans", "zh-Hant", "zh-CN", "zh-TW")
ORIGINAL_LANG_PREFERENCE = ("en", "en-*", "ja", "ja-*", "ko", "ko-*", "fr", "de", "es", "pt", "it")
DEFAULT_TRANSCRIPTION_PROMPT = (
    "Create a faithful transcript in the original language. Preserve spoken math, equations, "
    "variables, symbols, and units as Markdown LaTeX when possible: inline math as $...$ and "
    "display equations as $$...$$. Do not summarize, paraphrase, or add content that was not spoken."
)


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def ensure_venv(update: bool) -> None:
    if not VENV_PYTHON.exists():
        print(f"Creating isolated environment: {VENV_DIR}")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        update = True

    probe = run([str(VENV_PYTHON), "-c", "import yt_dlp, openai"], check=False, capture=True)
    if update or probe.returncode != 0:
        print("Installing/updating transcript dependencies...")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-U", "pip"])
        run([str(VENV_PYTHON), "-m", "pip", "install", "-U", "yt-dlp[default]", "openai"])


def reexec_in_venv(args: list[str]) -> None:
    if "-h" in args or "--help" in args:
        return
    if Path(sys.prefix).resolve() == VENV_DIR.resolve():
        return
    update = "--update" in args
    ensure_venv(update)
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *args])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Markdown transcripts from video or playlist URLs.",
    )
    parser.add_argument("urls", nargs="+", help="Video or playlist URLs to process")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Transcript output directory")
    parser.add_argument("--cookies-from-browser", help="Browser to load cookies from, e.g. chrome or safari")
    parser.add_argument(
        "--transcribe-backend",
        choices=("auto", "openai", "kimi-video", "minimax-api"),
        default="auto",
        help="Fallback backend when no human subtitles are available",
    )
    parser.add_argument("--transcribe-model", default="gpt-4o-mini-transcribe", help="OpenAI transcription model")
    parser.add_argument("--kimi-model", default="kimi-k2.6", help="Kimi/Moonshot model for video transcript or translation")
    parser.add_argument(
        "--minimax-base-url",
        default=os.environ.get("MINIMAX_BASE_URL") or os.environ.get("MINIMAX_API_BASE") or MINIMAX_BASE_URL,
        help="MiniMax API base URL. Defaults to https://api.minimax.io/v1",
    )
    parser.add_argument(
        "--minimax-transcribe-url",
        default=os.environ.get("MINIMAX_TRANSCRIBE_URL"),
        help="Full MiniMax-compatible audio transcription endpoint URL. Defaults to {base}/audio/transcriptions.",
    )
    parser.add_argument(
        "--minimax-model",
        default=os.environ.get("MINIMAX_ASR_MODEL") or os.environ.get("MINIMAX_MODEL") or "speech-2.8-turbo",
        help="MiniMax ASR model name. MINIMAX_ASR_MODEL is the preferred environment variable.",
    )
    parser.add_argument(
        "--transcribe-language",
        default=os.environ.get("TRANSCRIBE_LANGUAGE", ""),
        help="Optional transcription language hint passed to supported backends.",
    )
    parser.add_argument(
        "--transcription-prompt",
        default=os.environ.get("TRANSCRIPTION_PROMPT", DEFAULT_TRANSCRIPTION_PROMPT),
        help="Prompt/hint sent to transcription backends, including math formula formatting requirements.",
    )
    parser.add_argument("--timestamps", action="store_true", help="Keep subtitle timestamps or chunk markers")
    parser.add_argument("--keep-audio", action="store_true", help="Keep intermediate audio files")
    parser.add_argument("--update", action="store_true", help="Update isolated dependencies before processing")
    return parser.parse_args()


def ytdlp_base(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ignore-errors",
        "--socket-timeout",
        "20",
        "--retries",
        "3",
        "--fragment-retries",
        "3",
    ]
    if args.cookies_from_browser:
        cmd += ["--cookies-from-browser", args.cookies_from_browser]
    return cmd


def fetch_info(url: str, args: argparse.Namespace) -> dict[str, Any] | None:
    cmd = ytdlp_base(args) + ["--dump-single-json", "--skip-download", "--yes-playlist", url]
    result = run(cmd, check=False, capture=True)
    if result.returncode != 0:
        print(result.stderr.strip() or f"Failed to inspect URL: {url}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"Failed to parse yt-dlp metadata for {url}: {exc}", file=sys.stderr)
        return None


def iter_videos(info: dict[str, Any], fallback_url: str) -> list[dict[str, Any]]:
    entries = info.get("entries")
    if not entries:
        item = dict(info)
        item.setdefault("_download_url", info.get("webpage_url") or info.get("original_url") or fallback_url)
        return [item]

    playlist_title = info.get("title") or info.get("playlist_title")
    videos: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        if not entry:
            continue
        item = dict(entry)
        item.setdefault("playlist_title", playlist_title)
        item.setdefault("playlist_index", entry.get("playlist_index") or index)
        item.setdefault("_download_url", entry.get("webpage_url") or entry.get("original_url") or entry.get("url"))
        videos.append(item)
    return videos


def lang_matches(pattern: str, lang: str) -> bool:
    pattern = pattern.strip()
    if not pattern:
        return False
    if pattern.endswith("*"):
        return lang.lower().startswith(pattern[:-1].lower())
    return lang.lower() == pattern.lower()


def choose_by_patterns(languages: list[str], patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        for lang in languages:
            if lang_matches(pattern, lang):
                return lang
    return None


def is_zh_lang(lang: str | None) -> bool:
    if not lang:
        return False
    return any(lang_matches(pattern, lang) for pattern in ZH_PATTERNS)


def has_cjk(text: str) -> bool:
    cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    letter_count = sum(1 for ch in text if ch.isalpha() or "\u4e00" <= ch <= "\u9fff")
    return bool(letter_count and cjk_count / letter_count > 0.2)


def choose_original_subtitle(video: dict[str, Any]) -> str | None:
    subtitles = video.get("subtitles") or {}
    languages = [lang for lang, tracks in subtitles.items() if tracks]
    if not languages:
        return None

    metadata_lang = video.get("language") or video.get("language_code")
    if metadata_lang:
        metadata_match = choose_by_patterns(languages, (str(metadata_lang), f"{metadata_lang}-*"))
        if metadata_match:
            return metadata_match

    non_zh = [lang for lang in languages if not is_zh_lang(lang)]
    preferred = choose_by_patterns(non_zh, ORIGINAL_LANG_PREFERENCE)
    if preferred:
        return preferred
    if non_zh:
        return non_zh[0]
    return choose_by_patterns(languages, ZH_PATTERNS) or languages[0]


def choose_zh_subtitle(video: dict[str, Any]) -> str | None:
    subtitles = video.get("subtitles") or {}
    languages = [lang for lang, tracks in subtitles.items() if tracks]
    return choose_by_patterns(languages, ZH_PATTERNS)


def safe_path_part(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:120] or "untitled"


def video_output_dir(video: dict[str, Any], output_root: Path) -> Path:
    title = safe_path_part(video.get("title") or video.get("id") or "video")
    video_id = safe_path_part(video_identifier(video))
    playlist_title = video.get("playlist_title")
    if playlist_title:
        try:
            index = int(video.get("playlist_index") or 0)
        except (TypeError, ValueError):
            index = 0
        parent = output_root / safe_path_part(playlist_title)
        return parent / f"{index:03d} - {title} [{video_id}]"
    return output_root / f"{title} [{video_id}]"


def video_identifier(video: dict[str, Any]) -> str:
    raw_id = str(video.get("id") or "").strip()
    if raw_id and len(raw_id) <= 64 and "_gl" not in raw_id and "?" not in raw_id and "*" not in raw_id:
        return raw_id

    url = str(video.get("_download_url") or video.get("webpage_url") or "")
    path_name = urlparse(url).path.rstrip("/").split("/")[-1]
    return path_name or raw_id or "unknown"


def download_subtitle(url: str, lang: str, work_dir: Path, args: argparse.Namespace) -> Path | None:
    subtitle_dir = work_dir / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    cmd = ytdlp_base(args) + [
        "--skip-download",
        "--no-playlist",
        "--write-subs",
        "--sub-langs",
        lang,
        "--sub-format",
        "vtt/srt/best",
        "--paths",
        f"home:{subtitle_dir}",
        "-o",
        "%(id)s.%(ext)s",
        url,
    ]
    result = run(cmd, check=False, capture=True)
    if result.returncode != 0:
        print(result.stderr.strip() or f"Failed to download subtitle {lang}", file=sys.stderr)
        return None
    candidates = sorted(subtitle_dir.glob(f"*.{lang}.*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def clean_subtitle_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_timestamp(value: str) -> str:
    value = value.strip().replace(",", ".")
    if "." in value:
        value = value.split(".", 1)[0]
    parts = value.split(":")
    if len(parts) == 2:
        return f"00:{parts[0]}:{parts[1]}"
    return value


def parse_subtitle_file(path: Path, keep_timestamps: bool) -> str:
    cues: list[tuple[str | None, str]] = []
    current_time: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_time, current_lines
        text = clean_subtitle_text(" ".join(current_lines))
        if text and (not cues or cues[-1][1] != text):
            cues.append((current_time, text))
        current_time = None
        current_lines = []

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if line == "WEBVTT" or line.startswith(("NOTE", "STYLE", "Kind:", "Language:")):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if "-->" in line:
            flush()
            current_time = parse_timestamp(line.split("-->", 1)[0])
            continue
        current_lines.append(line)
    flush()

    if keep_timestamps:
        return "\n\n".join(f"### {time or '00:00:00'}\n\n{text}" for time, text in cues)
    return "\n\n".join(text for _, text in cues)


def download_audio(url: str, work_dir: Path, args: argparse.Namespace) -> Path | None:
    audio_dir = work_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    cmd = ytdlp_base(args) + [
        "--no-playlist",
        "-f",
        "ba/b",
        "--extract-audio",
        "--audio-format",
        "m4a",
        "--paths",
        f"home:{audio_dir}",
        "--paths",
        f"temp:{work_dir / '.tmp'}",
        "-o",
        "%(id)s.%(ext)s",
        "--newline",
        url,
    ]
    result = run(cmd, check=False)
    if result.returncode != 0:
        print("Failed to download audio", file=sys.stderr)
        return None
    candidates = sorted(audio_dir.glob("*.*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def download_video_for_kimi(url: str, work_dir: Path, args: argparse.Namespace) -> Path | None:
    video_dir = work_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    cmd = ytdlp_base(args) + [
        "--no-playlist",
        "-f",
        "worst[ext=mp4]/worst",
        "--merge-output-format",
        "mp4",
        "--paths",
        f"home:{video_dir}",
        "--paths",
        f"temp:{work_dir / '.tmp'}",
        "-o",
        "%(id)s.%(ext)s",
        "--newline",
        url,
    ]
    result = run(cmd, check=False)
    if result.returncode != 0:
        print("Failed to download video for Kimi", file=sys.stderr)
        return None
    candidates = sorted(video_dir.glob("*.*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def compress_video_for_kimi(video_path: Path, work_dir: Path) -> Path:
    if video_path.stat().st_size <= KIMI_SAFE_VIDEO_BYTES:
        return video_path
    compressed = work_dir / "kimi-video.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        "scale='min(854,iw)':-2,fps=2",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "32",
        "-c:a",
        "aac",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "48k",
        "-movflags",
        "+faststart",
        str(compressed),
    ]
    result = run(cmd, check=False, capture=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to compress video for Kimi.")
    if compressed.stat().st_size > KIMI_SAFE_VIDEO_BYTES:
        raise RuntimeError("Compressed video is still too large for Kimi request-body limits.")
    return compressed


def ffprobe_duration(path: Path) -> float | None:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def split_audio_copy(audio_path: Path, parts_dir: Path) -> list[Path]:
    duration = ffprobe_duration(audio_path)
    if not duration:
        return []
    segment_count = max(2, math.ceil(audio_path.stat().st_size / SAFE_UPLOAD_BYTES))
    segment_time = max(300, math.ceil(duration / segment_count))
    parts_dir.mkdir(parents=True, exist_ok=True)
    pattern = parts_dir / "part-%03d.m4a"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-vn",
        "-f",
        "segment",
        "-segment_time",
        str(segment_time),
        "-reset_timestamps",
        "1",
        "-c",
        "copy",
        str(pattern),
    ]
    result = run(cmd, check=False, capture=True)
    if result.returncode != 0:
        return []
    return sorted(parts_dir.glob("part-*.m4a"))


def split_audio_compressed(audio_path: Path, parts_dir: Path) -> list[Path]:
    shutil.rmtree(parts_dir, ignore_errors=True)
    parts_dir.mkdir(parents=True, exist_ok=True)
    pattern = parts_dir / "part-%03d.m4a"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "48k",
        "-f",
        "segment",
        "-segment_time",
        "1200",
        "-reset_timestamps",
        "1",
        str(pattern),
    ]
    result = run(cmd, check=False, capture=True)
    if result.returncode != 0:
        print(result.stderr.strip() or "Failed to split compressed audio", file=sys.stderr)
        return []
    return sorted(parts_dir.glob("part-*.m4a"))


def prepare_audio_parts(audio_path: Path, work_dir: Path) -> list[Path]:
    if audio_path.stat().st_size <= SAFE_UPLOAD_BYTES:
        return [audio_path]

    parts_dir = work_dir / "audio-parts"
    parts = split_audio_copy(audio_path, parts_dir)
    if parts and all(part.stat().st_size <= SAFE_UPLOAD_BYTES for part in parts):
        return parts

    print("Audio chunks are still large; compressing to speech-friendly mono audio.")
    parts = split_audio_compressed(audio_path, parts_dir)
    too_large = [part for part in parts if part.stat().st_size > SAFE_UPLOAD_BYTES]
    if too_large:
        names = ", ".join(path.name for path in too_large)
        raise RuntimeError(f"Audio chunks still exceed upload limit after compression: {names}")
    return parts


def transcribe_audio(parts: list[Path], args: argparse.Namespace) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required when no human subtitles are available.")

    from openai import OpenAI

    client = OpenAI()
    blocks: list[str] = []
    for index, part in enumerate(parts, start=1):
        print(f"Transcribing audio part {index}/{len(parts)}: {part.name}")
        request: dict[str, Any] = {
            "model": args.transcribe_model,
            "response_format": "json",
            "prompt": args.transcription_prompt,
        }
        if args.transcribe_language:
            request["language"] = args.transcribe_language
        with part.open("rb") as audio_file:
            result = client.audio.transcriptions.create(file=audio_file, **request)
        text = getattr(result, "text", "") or (result.get("text", "") if isinstance(result, dict) else "")
        text = text.strip()
        if args.timestamps and len(parts) > 1:
            blocks.append(f"### Part {index}\n\n{text}")
        elif text:
            blocks.append(text)
    return "\n\n".join(blocks).strip()


def extract_transcription_text(data: Any) -> str:
    candidates: list[Any] = [data]
    while candidates:
        current = candidates.pop(0)
        if isinstance(current, str) and current.strip():
            return current.strip()
        if isinstance(current, dict):
            for key in ("text", "transcript", "transcription", "content", "output", "result"):
                value = current.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            candidates.extend(current.values())
        elif isinstance(current, list):
            candidates.extend(current)
    return ""


def minimax_transcribe_url(args: argparse.Namespace) -> str:
    if args.minimax_transcribe_url:
        return args.minimax_transcribe_url.rstrip("/")
    return args.minimax_base_url.rstrip("/") + "/audio/transcriptions"


def transcribe_audio_with_minimax_api(parts: list[Path], args: argparse.Namespace) -> str:
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY is required for MiniMax API transcription.")

    import requests

    endpoint = minimax_transcribe_url(args)
    blocks: list[str] = []
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": args.minimax_model,
        "response_format": "json",
        "prompt": args.transcription_prompt,
    }
    if args.transcribe_language:
        data["language"] = args.transcribe_language

    for index, part in enumerate(parts, start=1):
        print(f"Transcribing audio part {index}/{len(parts)} with MiniMax API: {part.name}")
        with part.open("rb") as audio_file:
            response = requests.post(
                endpoint,
                headers=headers,
                data=data,
                files={"file": (part.name, audio_file, "application/octet-stream")},
                timeout=300,
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"MiniMax API transcription failed for {part.name}: "
                f"HTTP {response.status_code} {response.text[:1000]}"
            )
        try:
            payload: Any = response.json()
        except ValueError:
            payload = response.text
        text = extract_transcription_text(payload).strip()
        if not text:
            raise RuntimeError(f"MiniMax API returned empty transcript for {part.name}.")
        if args.timestamps and len(parts) > 1:
            blocks.append(f"### Part {index}\n\n{text}")
        else:
            blocks.append(text)
    return "\n\n".join(blocks).strip()


def kimi_client():
    api_key = os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        raise RuntimeError("MOONSHOT_API_KEY is required for Kimi video transcription or translation.")

    from openai import OpenAI

    return OpenAI(api_key=api_key, base_url=resolve_moonshot_base_url(api_key))


def resolve_moonshot_base_url(api_key: str) -> str:
    configured = os.environ.get("MOONSHOT_BASE_URL")
    candidates = (configured,) if configured else MOONSHOT_BASE_URLS
    failures: list[str] = []
    for base_url in candidates:
        if not base_url:
            continue
        request = Request(
            base_url.rstrip("/") + "/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        try:
            with urlopen(request, timeout=15) as response:
                if response.status == 200:
                    return base_url.rstrip("/")
                failures.append(f"{base_url}: HTTP {response.status}")
        except HTTPError as exc:
            failures.append(f"{base_url}: HTTP {exc.code}")
        except URLError as exc:
            failures.append(f"{base_url}: {exc.reason}")
    raise RuntimeError("Could not authenticate with Moonshot API endpoints. " + "; ".join(failures))


def transcribe_video_with_kimi(video_path: Path, model: str, keep_timestamps: bool) -> str:
    client = kimi_client()
    ext = video_path.suffix.lstrip(".").lower() or "mp4"
    mime = "mp4" if ext == "m4v" else ext
    encoded = base64.b64encode(video_path.read_bytes()).decode("utf-8")
    prompt = (
        "请根据这个视频的音频内容生成逐字程度尽量高的讲稿。"
        "保留原语言，不要总结、不要改写、不要添加视频里没有说的内容。"
        "遇到数学公式、变量、符号、单位时，尽量用 Markdown LaTeX 表达：行内公式用 $...$，独立公式用 $$...$$。"
        "如果听不清，请标注[听不清]。"
    )
    if keep_timestamps:
        prompt += " 请按大约2到5分钟一段添加时间段标题。"
    else:
        prompt += " 不需要时间戳。"
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You create faithful transcripts from video content."},
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": f"data:video/{mime};base64,{encoded}"}},
                    {"type": "text", "text": prompt},
                ],
            },
        ],
        extra_body={"thinking": {"type": "disabled"}},
        max_tokens=32768,
    )
    return (response.choices[0].message.content or "").strip()


def translate_to_zh_with_kimi(original_text: str, model: str) -> str:
    client = kimi_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You translate transcripts into natural, faithful Simplified Chinese."},
            {
                "role": "user",
                "content": (
                    "请把下面的讲稿翻译成自然、准确的简体中文。"
                    "保留 Markdown 标题和段落结构，不要总结，不要添加原文没有的信息。\n\n"
                    + original_text
                ),
            },
        ],
        extra_body={"thinking": {"type": "disabled"}},
        max_tokens=32768,
    )
    return (response.choices[0].message.content or "").strip()


def choose_transcribe_backend(args: argparse.Namespace) -> str:
    if args.transcribe_backend != "auto":
        return args.transcribe_backend
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("MOONSHOT_API_KEY"):
        return "kimi-video"
    if os.environ.get("MINIMAX_API_KEY"):
        return "minimax-api"
    raise RuntimeError(
        "Set OPENAI_API_KEY for OpenAI audio transcription, MOONSHOT_API_KEY for Kimi video transcription, "
        "or MINIMAX_API_KEY for MiniMax API transcription."
    )


def markdown_document(video: dict[str, Any], body: str, *, source: str, language: str | None) -> str:
    title = video.get("title") or "Video transcript"
    url = video.get("_download_url") or video.get("webpage_url") or ""
    lines = [
        f"# {title}",
        "",
        f"- Source: {url}",
        f"- Transcript source: {source}",
    ]
    if language:
        lines.append(f"- Language: {language}")
    lines += ["", "## Transcript", "", body.strip(), ""]
    return "\n".join(lines)


def write_metadata(video_dir: Path, metadata: dict[str, Any]) -> None:
    (video_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def process_video(video: dict[str, Any], output_root: Path, args: argparse.Namespace) -> bool:
    url = video.get("_download_url")
    if not url:
        print(f"Skipping item without URL: {video.get('title') or video.get('id')}", file=sys.stderr)
        return False

    video_dir = video_output_dir(video, output_root)
    work_dir = video_dir / "_work"
    video_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    original_path = video_dir / "original.md"
    zh_path = video_dir / "zh.md"
    metadata: dict[str, Any] = {
        "title": video.get("title"),
        "id": video.get("id"),
        "url": url,
        "original_path": str(original_path),
        "zh_path": str(zh_path),
        "source": None,
        "original_language": None,
        "needs_zh_translation": False,
    }

    try:
        original_lang = choose_original_subtitle(video)
        zh_lang = choose_zh_subtitle(video)
        if original_lang:
            subtitle_file = download_subtitle(str(url), original_lang, work_dir, args)
            if not subtitle_file:
                raise RuntimeError(f"Could not download selected subtitle: {original_lang}")
            body = parse_subtitle_file(subtitle_file, args.timestamps)
            original_path.write_text(
                markdown_document(video, body, source=f"human subtitle ({original_lang})", language=original_lang),
                encoding="utf-8",
            )
            metadata["source"] = "human_subtitle"
            metadata["original_language"] = original_lang

            if zh_lang and not is_zh_lang(original_lang):
                zh_subtitle_file = download_subtitle(str(url), zh_lang, work_dir, args)
                if zh_subtitle_file:
                    zh_body = parse_subtitle_file(zh_subtitle_file, args.timestamps)
                    zh_path.write_text(
                        markdown_document(video, zh_body, source=f"human subtitle ({zh_lang})", language=zh_lang),
                        encoding="utf-8",
                    )
                    metadata["zh_source"] = "human_subtitle"

            metadata["needs_zh_translation"] = not is_zh_lang(original_lang) and not zh_path.exists()
            if metadata["needs_zh_translation"] and os.environ.get("MOONSHOT_API_KEY"):
                print("Translating transcript to Chinese with Kimi...")
                zh_text = translate_to_zh_with_kimi(original_path.read_text(encoding="utf-8"), args.kimi_model)
                if zh_text:
                    zh_path.write_text(zh_text.rstrip() + "\n", encoding="utf-8")
                    metadata["zh_source"] = f"kimi_translation ({args.kimi_model})"
                    metadata["needs_zh_translation"] = False
        else:
            backend = choose_transcribe_backend(args)
            if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
                raise RuntimeError("ffmpeg and ffprobe are required for transcription fallback.")
            if backend in ("openai", "minimax-api"):
                audio_path = download_audio(str(url), work_dir, args)
                if not audio_path:
                    raise RuntimeError("Could not download audio for transcription.")
                parts = prepare_audio_parts(audio_path, work_dir)
                if backend == "openai":
                    body = transcribe_audio(parts, args)
                    source = f"OpenAI transcription ({args.transcribe_model})"
                    metadata["source"] = "openai_transcription"
                    metadata["transcribe_model"] = args.transcribe_model
                else:
                    body = transcribe_audio_with_minimax_api(parts, args)
                    source = f"MiniMax API transcription ({args.minimax_model})"
                    metadata["source"] = "minimax_api_transcription"
                    metadata["minimax_model"] = args.minimax_model
                    metadata["minimax_base_url"] = args.minimax_base_url
                    metadata["minimax_transcribe_url"] = minimax_transcribe_url(args)
            else:
                video_path = download_video_for_kimi(str(url), work_dir, args)
                if not video_path:
                    raise RuntimeError("Could not download video for Kimi transcription.")
                kimi_video_path = compress_video_for_kimi(video_path, work_dir)
                body = transcribe_video_with_kimi(kimi_video_path, args.kimi_model, args.timestamps)
                source = f"Kimi video transcription ({args.kimi_model})"
                metadata["source"] = "kimi_video_transcription"
                metadata["kimi_model"] = args.kimi_model
            if not body:
                raise RuntimeError("Transcription returned empty text.")
            original_path.write_text(
                markdown_document(video, body, source=source, language=None),
                encoding="utf-8",
            )
            metadata["needs_zh_translation"] = not has_cjk(body)
            if metadata["needs_zh_translation"] and os.environ.get("MOONSHOT_API_KEY"):
                print("Translating transcript to Chinese with Kimi...")
                zh_text = translate_to_zh_with_kimi(original_path.read_text(encoding="utf-8"), args.kimi_model)
                if zh_text:
                    zh_path.write_text(zh_text.rstrip() + "\n", encoding="utf-8")
                    metadata["zh_source"] = f"kimi_translation ({args.kimi_model})"
                    metadata["needs_zh_translation"] = False

        write_metadata(video_dir, metadata)
        if not args.keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
        print(f"Transcript written: {original_path}")
        if zh_path.exists():
            print(f"Chinese transcript written: {zh_path}")
        elif metadata["needs_zh_translation"]:
            print(f"Chinese translation needed: {zh_path}")
        return True
    except Exception as exc:
        metadata["error"] = str(exc)
        write_metadata(video_dir, metadata)
        if not args.keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
        print(f"Failed: {video.get('title') or url}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    reexec_in_venv(sys.argv[1:])
    args = parse_args()

    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    failures = 0
    for url in args.urls:
        info = fetch_info(url, args)
        if not info:
            failures += 1
            continue
        for video in iter_videos(info, url):
            if not process_video(video, output_root, args):
                failures += 1

    print(f"\nDone. Transcript folders are in: {output_root}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
