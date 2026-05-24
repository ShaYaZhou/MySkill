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
from datetime import datetime, timezone
from pathlib import Path

from public_api_fallbacks import (
    PUBLIC_API_STAGES,
    download_public_media,
    download_public_subtitle,
    fetch_public_api_info,
    public_api_doctor,
    public_api_fallback_disabled,
    public_api_plan,
    public_api_summary_fields,
    public_subtitle_languages,
    supplement_public_api_info,
)


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


def warn_missing_ffmpeg(warnings: list[str] | None = None) -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        message = (
            "Warning: missing "
            + ", ".join(missing)
            + ". Some MP4 merging or audio extraction operations may fail."
        )
        if warnings is not None:
            warnings.append(message)
        print(message, file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download video or playlist URLs with MP4 preference, human subtitles, and thumbnails.",
    )
    parser.add_argument("urls", nargs="*", help="Video or playlist URLs to download")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Download directory")
    parser.add_argument("--audio-only", action="store_true", help="Extract audio-only files")
    parser.add_argument("--no-thumbnail", action="store_true", help="Do not download thumbnails")
    parser.add_argument("--sub-lang", action="append", help="Specific human subtitle language to download")
    parser.add_argument("--cookies-from-browser", help="Browser to load cookies from, e.g. chrome or safari")
    parser.add_argument("--update", action="store_true", help="Update yt-dlp before downloading")
    parser.add_argument("--doctor", action="store_true", help="Check local dependencies and configuration without URLs")
    parser.add_argument("--dry-run", action="store_true", help="Inspect metadata and write a summary without downloading media")
    parser.add_argument("--no-public-api-fallback", action="store_true", help="Disable public, no-auth site API fallback adapters")
    parser.add_argument("--force", action="store_true", help="Redownload and allow overwriting existing output files")
    return parser.parse_args()


def redact_argv(argv: list[str]) -> list[str]:
    redacted: list[str] = []
    redact_next = False
    sensitive_options = {"--cookies", "--cookies-from-browser"}
    for value in argv:
        if redact_next:
            redacted.append("<redacted>")
            redact_next = False
            continue
        if value in sensitive_options:
            redacted.append(value)
            redact_next = True
            continue
        if any(value.startswith(option + "=") for option in sensitive_options):
            option, _, _secret = value.partition("=")
            redacted.append(f"{option}=<redacted>")
            continue
        redacted.append(value)
    return redacted


def tool_version(cmd: list[str]) -> dict:
    try:
        result = run(cmd, check=False, capture=True)
    except FileNotFoundError:
        return {"command": cmd[0], "available": False, "version": None, "returncode": None}
    text = (result.stdout or result.stderr or "").strip().splitlines()
    return {
        "command": cmd[0],
        "available": result.returncode == 0,
        "version": text[0] if text else None,
        "returncode": result.returncode,
    }


def ytdlp_version() -> dict:
    if not VENV_PYTHON.exists():
        return {"available": False, "version": None, "returncode": None}
    result = run([str(VENV_PYTHON), "-m", "yt_dlp", "--version"], check=False, capture=True)
    return {
        "available": result.returncode == 0,
        "version": (result.stdout or result.stderr or "").strip() or None,
        "returncode": result.returncode,
    }


def make_summary(args: argparse.Namespace, output_dir: Path) -> dict:
    return {
        "schema_version": 1,
        "tool": "yt-dlp-download",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "doctor" if args.doctor else "dry-run" if args.dry_run else "download",
        "argv": redact_argv(sys.argv),
        "cwd": str(Path.cwd()),
        "skill_dir": str(SKILL_DIR),
        "output_dir": str(output_dir),
        "archive_file": str(output_dir / ".yt-dlp-archive.txt"),
        "options": {
            "audio_only": args.audio_only,
            "no_thumbnail": args.no_thumbnail,
            "sub_lang": args.sub_lang or [],
            "cookies_from_browser": bool(args.cookies_from_browser),
            "update": args.update,
            "dry_run": args.dry_run,
            "force": args.force,
            "public_api_fallback_enabled": not public_api_fallback_disabled(args),
        },
        "public_api_fallback": public_api_doctor(public_api_fallback_disabled(args)),
        "tool_versions": {
            "python": sys.version.split()[0],
            "venv_python": str(VENV_PYTHON),
            "yt_dlp": ytdlp_version(),
            "ffmpeg": tool_version(["ffmpeg", "-version"]),
            "ffprobe": tool_version(["ffprobe", "-version"]),
        },
        "inputs": list(args.urls),
        "items": [],
        "failures": [],
        "warnings": [],
        "doctor": None,
    }


def write_summary(summary: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "download-summary.json"
    summary["summary_path"] = str(summary_path)
    summary["updated_at"] = datetime.now(timezone.utc).isoformat()
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary_path


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
        if public_api_fallback_disabled(args):
            return None
        info = fetch_public_api_info(url, disabled=False, stages=PUBLIC_API_STAGES)
        if info:
            print(f"Using public API fallback for metadata: {info.get('extractor_key') or 'public-api'}")
            return info
        return None
    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"Failed to parse yt-dlp metadata for {url}: {exc}", file=sys.stderr)
        if public_api_fallback_disabled(args):
            return None
        return fetch_public_api_info(url, disabled=False, stages=PUBLIC_API_STAGES)
    stages = PUBLIC_API_STAGES if args.dry_run else ("subtitle", "media")
    return supplement_public_api_info(
        info,
        url,
        disabled=public_api_fallback_disabled(args),
        stages=stages,
    )


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


def archive_keys(video: dict) -> list[str]:
    video_id = str(video.get("id") or "").strip()
    if not video_id:
        return []
    keys = [video_id]
    for extractor in (video.get("extractor_key"), video.get("ie_key"), video.get("extractor")):
        if extractor:
            keys.append(f"{extractor} {video_id}")
            keys.append(f"{str(extractor).lower()} {video_id}")
    return keys


def archive_hit(video: dict, archive_file: Path) -> bool:
    if not archive_file.exists():
        return False
    try:
        lines = set(archive_file.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return False
    keys = archive_keys(video)
    return any(key in lines for key in keys)


def planned_output(video: dict, output_dir: Path) -> dict:
    template = output_template(video)
    return {
        "template": template,
        "candidate": str(output_dir / template),
        "actual_files": [],
        "uncertain_path": True,
        "note": "yt-dlp resolves title, id, extension, sidecar names, and final paths at download time.",
    }


def discover_output_files(video: dict, output_dir: Path) -> list[str]:
    video_id = str(video.get("id") or "").strip()
    if not video_id or not output_dir.exists():
        return []
    try:
        needle = f"[{video_id}]"
        matches = sorted(path for path in output_dir.rglob("*") if path.is_file() and needle in path.name)
    except OSError:
        return []
    return [str(path) for path in matches]


def fallback_filename_stem(video: dict) -> str:
    return safe_path_part(f"{video.get('title') or 'video'} [{video.get('id') or 'unknown'}]")


def item_summary(video: dict, args: argparse.Namespace, output_dir: Path, archive_file: Path, input_url: str) -> dict:
    sub_lang = choose_subtitle_lang(video.get("subtitles") or {}, args.sub_lang)
    subtitle_source = "public_api" if sub_lang in public_subtitle_languages(video) else "yt_dlp"
    item = {
        "input_url": input_url,
        "download_url": video.get("_download_url"),
        "title": video.get("title"),
        "id": video.get("id"),
        "playlist_title": video.get("playlist_title"),
        "playlist_index": video.get("playlist_index"),
        "output": planned_output(video, output_dir),
        "subtitle_language": sub_lang,
        "subtitle_status": "selected" if sub_lang else "none_matching_human_subtitles",
        "subtitle_source": subtitle_source if sub_lang else None,
        "thumbnail": {
            "requested": not args.no_thumbnail,
            "status": "planned" if not args.no_thumbnail else "disabled",
        },
        "archive": {
            "file": str(archive_file),
            "skip": False if args.force else archive_hit(video, archive_file),
            "ignored_by_force": args.force,
        },
        "status": "pending",
        "returncode": None,
        "warnings": [],
    }
    item.update(public_api_summary_fields(video))
    return item


def download_video(video: dict, args: argparse.Namespace, output_dir: Path, archive_file: Path, summary_item: dict) -> int:
    url = video.get("_download_url")
    if not url:
        message = f"Skipping item without a downloadable URL: {video.get('title') or video.get('id')}"
        print(message, file=sys.stderr)
        summary_item["status"] = "failed"
        summary_item["warnings"].append(message)
        return 1

    sub_lang = choose_subtitle_lang(video.get("subtitles") or {}, args.sub_lang)
    cmd = ytdlp_base(args) + [
        "--no-playlist",
        "--paths",
        f"home:{output_dir}",
        "--paths",
        f"temp:{output_dir / '.tmp'}",
        "-o",
        output_template(video),
        "--newline",
    ]

    if args.force:
        cmd += ["--force-overwrites", "--no-continue"]
    else:
        cmd += ["--continue", "--no-overwrites", "--download-archive", str(archive_file)]

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
    result = run(cmd, check=False)
    summary_item["returncode"] = result.returncode
    summary_item["output"]["actual_files"] = discover_output_files(video, output_dir)
    if summary_item["output"]["actual_files"]:
        summary_item["output"]["uncertain_path"] = False
    if result.returncode and not public_api_fallback_disabled(args):
        fallback_dir = output_dir / "public-api-fallback"
        fallback = download_public_media(
            video,
            fallback_dir,
            audio_only=args.audio_only,
            filename_stem=fallback_filename_stem(video),
        )
        summary_item["public_api_media_download"] = {
            "status": fallback.get("status"),
            "paths": fallback.get("paths", []),
        }
        summary_item["warnings"].extend(fallback.get("warnings", []))
        if sub_lang in public_subtitle_languages(video):
            subtitle = download_public_subtitle(
                video,
                sub_lang,
                fallback_dir,
                filename_stem=fallback_filename_stem(video),
            )
            summary_item["public_api_subtitle_download"] = {
                "status": subtitle.get("status"),
                "paths": subtitle.get("paths", []),
            }
            if subtitle.get("error"):
                summary_item["warnings"].append(str(subtitle["error"]))
        if fallback.get("status") == "downloaded" and fallback.get("paths"):
            summary_item["output"]["actual_files"] = list(fallback.get("paths") or [])
            if summary_item.get("public_api_subtitle_download"):
                summary_item["output"]["actual_files"].extend(summary_item["public_api_subtitle_download"].get("paths", []))
            summary_item["output"]["uncertain_path"] = False
            summary_item["status"] = "completed_public_api_fallback"
            summary_item["returncode"] = 0
            return 0
    summary_item["status"] = "failed" if result.returncode else "completed"
    if summary_item["archive"]["skip"] and result.returncode == 0:
        summary_item["status"] = "archive_skipped"
    return result.returncode


def run_doctor(args: argparse.Namespace, output_dir: Path, summary: dict) -> int:
    checks: list[dict] = []

    checks.append({"name": "venv", "ok": VENV_DIR.exists(), "path": str(VENV_DIR)})
    checks.append({"name": "venv_python", "ok": VENV_PYTHON.exists(), "path": str(VENV_PYTHON)})
    yt_dlp = ytdlp_version()
    checks.append({"name": "yt-dlp", "ok": yt_dlp["available"], "version": yt_dlp["version"]})

    for name in ("ffmpeg", "ffprobe"):
        path = shutil.which(name)
        version = tool_version([name, "-version"]) if path else {"available": False, "version": None}
        checks.append({"name": name, "ok": path is not None, "path": path, "version": version.get("version")})

    output_check = {"name": "output_dir_writable", "ok": False, "path": str(output_dir)}
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".yt-dlp-doctor-write-test"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
        output_check["ok"] = True
    except OSError as exc:
        output_check["error"] = str(exc)
    checks.append(output_check)

    cookie_check = {
        "name": "cookies_from_browser",
        "ok": args.cookies_from_browser is not None,
        "configured": bool(args.cookies_from_browser),
        "browser": "<redacted>" if args.cookies_from_browser else None,
        "note": "Only argument visibility is checked; browser profile access is verified by yt-dlp during metadata or download.",
    }
    checks.append(cookie_check)
    public_api = public_api_doctor(public_api_fallback_disabled(args))
    checks.append(
        {
            "name": "public_api_fallback",
            "ok": True,
            "enabled": public_api["enabled"],
            "adapters": [
                {
                    "id": adapter["id"],
                    "domains": adapter["domains"],
                    "stages": adapter["stages"],
                }
                for adapter in public_api["adapters"]
            ],
        }
    )

    summary["doctor"] = {"checks": checks, "public_api_fallback": public_api}
    summary["warnings"].extend(
        f"Doctor check failed: {check['name']}" for check in checks if not check.get("ok") and check["name"] != "cookies_from_browser"
    )
    for check in checks:
        status = "ok" if check.get("ok") else "missing"
        print(f"{check['name']}: {status}")
        if check["name"] == "public_api_fallback":
            for adapter in check.get("adapters", []):
                print(f"  adapter {adapter['id']}: domains={', '.join(adapter['domains'])}; stages={', '.join(adapter['stages'])}")
    blocked = any(not check.get("ok") for check in checks if check["name"] != "cookies_from_browser")
    summary["result"] = "blocked" if blocked else "ok"
    summary["status"] = summary["result"]
    return 1 if blocked else 0


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    archive_file = output_dir / ".yt-dlp-archive.txt"
    summary = make_summary(args, output_dir)

    if args.doctor:
        code = run_doctor(args, output_dir, summary)
        summary_path = write_summary(summary, output_dir)
        print(f"\nDoctor summary: {summary_path}")
        return code

    if not args.urls:
        print("At least one URL is required unless --doctor is used.", file=sys.stderr)
        return 2

    ensure_venv(args.update)
    summary["tool_versions"]["yt_dlp"] = ytdlp_version()
    warn_missing_ffmpeg(summary["warnings"])
    if args.force:
        summary["warnings"].append("--force ignores the download archive for this run and may overwrite existing files.")

    output_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for url in args.urls:
        info = fetch_info(url, args)
        if not info:
            failures += 1
            fallback_plan = public_api_plan(
                url,
                disabled=public_api_fallback_disabled(args),
                stages=PUBLIC_API_STAGES,
            )
            failure = {"input_url": url, "status": "metadata_failed"}
            failure.update(public_api_summary_fields(fallback_plan))
            summary["failures"].append(failure)
            continue
        for video in iter_videos(info, url):
            item = item_summary(video, args, output_dir, archive_file, url)
            summary["items"].append(item)
            if args.dry_run:
                item["status"] = "dry_run_planned"
                continue
            returncode = download_video(video, args, output_dir, archive_file, item)
            if returncode:
                failures += 1
                summary["failures"].append(
                    {
                        "input_url": url,
                        "download_url": item.get("download_url"),
                        "title": item.get("title"),
                        "id": item.get("id"),
                        "returncode": returncode,
                        "retry_suggestion": "Retry the same command after resolving warnings; use --force only when redownloading and overwriting is intended.",
                    }
                )

    summary["result"] = "partial_failure" if failures else "dry_run" if args.dry_run else "success"
    summary["status"] = summary["result"]
    summary_path = write_summary(summary, output_dir)
    if args.dry_run:
        print(f"\nDry run complete. Summary: {summary_path}")
    else:
        print(f"\nDone. Files are in: {output_dir}")
        print(f"Summary: {summary_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
