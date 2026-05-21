#!/usr/bin/env python3
"""Download videos/playlists with an isolated yt-dlp installation."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VENV_DIR = SKILL_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
DEFAULT_OUTPUT_DIR = Path("~/Downloads/yt-dlp").expanduser()
DEFAULT_SUBTITLE_PATTERNS = ("zh", "zh-*", "zh-Hans", "zh-Hant", "zh-CN", "zh-TW", "en", "en-*")


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

    version = run([str(VENV_PYTHON), "-m", "yt_dlp", "--version"], check=False, capture=True)
    if update or version.returncode != 0:
        print("Installing/updating yt-dlp in the isolated environment...")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-U", "pip"])
        run([str(VENV_PYTHON), "-m", "pip", "install", "-U", "yt-dlp[default]"])


def warn_missing_ffmpeg() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        print(
            "Warning: missing "
            + ", ".join(missing)
            + ". Some MP4 merging or audio extraction operations may fail.",
            file=sys.stderr,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download video or playlist URLs with MP4 preference, human subtitles, and thumbnails.",
    )
    parser.add_argument("urls", nargs="+", help="Video or playlist URLs to download")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Download directory")
    parser.add_argument("--audio-only", action="store_true", help="Extract audio-only files")
    parser.add_argument("--no-thumbnail", action="store_true", help="Do not download thumbnails")
    parser.add_argument("--sub-lang", action="append", help="Specific human subtitle language to download")
    parser.add_argument("--cookies-from-browser", help="Browser to load cookies from, e.g. chrome or safari")
    parser.add_argument("--update", action="store_true", help="Update yt-dlp before downloading")
    return parser.parse_args()


def ytdlp_base(args: argparse.Namespace) -> list[str]:
    cmd = [str(VENV_PYTHON), "-m", "yt_dlp", "--ignore-errors"]
    if args.cookies_from_browser:
        cmd += ["--cookies-from-browser", args.cookies_from_browser]
    return cmd


def fetch_info(url: str, args: argparse.Namespace) -> dict | None:
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


def iter_videos(info: dict, fallback_url: str) -> list[dict]:
    entries = info.get("entries")
    if not entries:
        item = dict(info)
        item.setdefault("_download_url", info.get("webpage_url") or info.get("original_url") or fallback_url)
        return [item]

    playlist_title = info.get("title") or info.get("playlist_title")
    videos: list[dict] = []
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


def choose_subtitle_lang(subtitles: dict, requested: list[str] | None) -> str | None:
    if not subtitles:
        return None
    available = [lang for lang, tracks in subtitles.items() if tracks]
    patterns = requested or list(DEFAULT_SUBTITLE_PATTERNS)
    for pattern in patterns:
        for lang in available:
            if lang_matches(pattern, lang):
                return lang
    return None


def safe_path_part(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:120] or "playlist"


def output_template(video: dict) -> str:
    playlist_title = video.get("playlist_title")
    if playlist_title:
        try:
            index = int(video.get("playlist_index") or 0)
        except (TypeError, ValueError):
            index = 0
        return f"{safe_path_part(playlist_title)}/{index:03d} - %(title).200B [%(id)s].%(ext)s"
    return "%(extractor_key)s/%(title).200B [%(id)s].%(ext)s"


def download_video(video: dict, args: argparse.Namespace, output_dir: Path, archive_file: Path) -> int:
    url = video.get("_download_url")
    if not url:
        print(f"Skipping item without a downloadable URL: {video.get('title') or video.get('id')}", file=sys.stderr)
        return 1

    sub_lang = choose_subtitle_lang(video.get("subtitles") or {}, args.sub_lang)
    cmd = ytdlp_base(args) + [
        "--no-playlist",
        "--continue",
        "--no-overwrites",
        "--download-archive",
        str(archive_file),
        "--paths",
        f"home:{output_dir}",
        "--paths",
        f"temp:{output_dir / '.tmp'}",
        "-o",
        output_template(video),
        "--newline",
    ]

    if args.audio_only:
        cmd += ["--extract-audio", "--audio-format", "m4a"]
    else:
        cmd += ["-f", "bv*+ba/b", "-S", "res,ext:mp4:m4a", "--merge-output-format", "mp4/mkv"]

    if sub_lang:
        cmd += ["--write-subs", "--sub-langs", sub_lang]
    else:
        cmd += ["--no-write-subs"]

    if not args.no_thumbnail:
        cmd += ["--write-thumbnail"]

    cmd.append(str(url))
    print(f"\nDownloading: {video.get('title') or url}")
    if sub_lang:
        print(f"Subtitle: {sub_lang}")
    else:
        print("Subtitle: none (no matching human subtitle found)")
    return run(cmd, check=False).returncode


def main() -> int:
    args = parse_args()
    ensure_venv(args.update)
    warn_missing_ffmpeg()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_file = output_dir / ".yt-dlp-archive.txt"

    failures = 0
    for url in args.urls:
        info = fetch_info(url, args)
        if not info:
            failures += 1
            continue
        for video in iter_videos(info, url):
            failures += 1 if download_video(video, args, output_dir, archive_file) else 0

    print(f"\nDone. Files are in: {output_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
