"""Public, no-auth site API fallbacks for video skills.

The module intentionally keeps the registry explicit. Unknown sites are never
guessed. Runtime summaries expose endpoint labels and states, not signed URLs,
cookies, tokens, or temporary media links.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


PUBLIC_API_STAGES = ("metadata", "subtitle", "media")
FALLBACK_ENV = "VIDEO_SKILL_PUBLIC_API_FALLBACK"
HTTP_TIMEOUT_SECONDS = 12
DOWNLOAD_TIMEOUT_SECONDS = 45

BILIBILI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bilibili.com/",
}

ADAPTER_REGISTRY: dict[str, dict[str, Any]] = {
    "bilibili": {
        "id": "bilibili",
        "display_name": "Bilibili",
        "domains": ("bilibili.com", "b23.tv"),
        "stages": ("metadata", "subtitle", "media"),
        "public": True,
        "requires_auth": False,
        "uses_cookie": False,
        "rate_limit": "small retry count; no parallel burst",
        "endpoint_labels": {
            "metadata": "api.bilibili.com/x/web-interface/view",
            "subtitle": "api.bilibili.com/x/player/v2",
            "media": "api.bilibili.com/x/player/playurl",
        },
        "headers": {"User-Agent": "desktop browser", "Referer": "https://www.bilibili.com/"},
    }
}


def public_api_fallback_disabled(args: Any | None = None) -> bool:
    if args is not None and getattr(args, "no_public_api_fallback", False):
        return True
    value = os.environ.get(FALLBACK_ENV, "").strip().lower()
    return value in {"0", "false", "no", "off", "disabled"}


def adapter_for_url(url: str) -> dict[str, Any] | None:
    host = urlparse(url).netloc.lower()
    if not host:
        return None
    for adapter in ADAPTER_REGISTRY.values():
        if any(host == domain or host.endswith("." + domain) for domain in adapter["domains"]):
            return adapter
    return None


def public_api_doctor(disabled: bool = False) -> dict[str, Any]:
    return {
        "enabled": not disabled,
        "disable_env": FALLBACK_ENV,
        "adapters": [
            {
                "id": adapter["id"],
                "display_name": adapter["display_name"],
                "domains": list(adapter["domains"]),
                "stages": list(adapter["stages"]),
                "public": adapter["public"],
                "requires_auth": adapter["requires_auth"],
                "uses_cookie": adapter["uses_cookie"],
                "endpoint_labels": adapter["endpoint_labels"],
            }
            for adapter in ADAPTER_REGISTRY.values()
        ],
    }


def base_record(
    url: str,
    *,
    adapter: dict[str, Any] | None,
    stages: tuple[str, ...] = PUBLIC_API_STAGES,
    source: str = "yt_dlp",
) -> dict[str, Any]:
    if adapter is None:
        return {
            "metadata_source": source,
            "public_api_fallback_used": False,
            "public_api_adapter": None,
            "public_api_stage": list(stages),
            "public_api_endpoint_label": [],
            "public_api_status": "unsupported-public-api",
            "public_api_requires_login": False,
            "public_api_uses_cookie": False,
            "requires_web_access": False,
            "subtitle_state": "unknown",
            "media_url_state": "unknown",
            "fallback_failures": [f"No public API adapter is registered for {urlparse(url).netloc or 'unknown-host'}."],
        }
    labels = adapter.get("endpoint_labels", {})
    return {
        "metadata_source": source,
        "public_api_fallback_used": False,
        "public_api_adapter": adapter["id"],
        "public_api_stage": [stage for stage in stages if stage in adapter["stages"]],
        "public_api_endpoint_label": [labels[stage] for stage in stages if stage in labels],
        "public_api_status": "planned",
        "public_api_requires_login": False,
        "public_api_uses_cookie": bool(adapter.get("uses_cookie")),
        "requires_web_access": False,
        "subtitle_state": "unknown",
        "media_url_state": "unknown",
        "fallback_failures": [],
    }


def disabled_record(url: str, stages: tuple[str, ...] = PUBLIC_API_STAGES) -> dict[str, Any]:
    record = base_record(url, adapter=adapter_for_url(url), stages=stages)
    record["public_api_status"] = "disabled"
    record["fallback_failures"] = ["Public API fallback was disabled by CLI option or environment."]
    return record


def public_api_plan(url: str, *, disabled: bool = False, stages: tuple[str, ...] = PUBLIC_API_STAGES) -> dict[str, Any]:
    if disabled:
        return disabled_record(url, stages)
    adapter = adapter_for_url(url)
    return base_record(url, adapter=adapter, stages=stages)


def public_api_summary_fields(video_or_record: dict[str, Any] | None, *, default_source: str = "yt_dlp") -> dict[str, Any]:
    record: dict[str, Any] | None = None
    if video_or_record:
        if "public_api_fallback" in video_or_record:
            record = video_or_record.get("public_api_fallback") or None
        elif "public_api_status" in video_or_record:
            record = video_or_record
    if not record:
        return {
            "metadata_source": default_source,
            "public_api_fallback_used": False,
            "public_api_adapter": None,
            "public_api_stage": [],
            "public_api_endpoint_label": [],
            "public_api_status": "not-used",
            "public_api_requires_login": False,
            "public_api_uses_cookie": False,
            "requires_web_access": False,
            "subtitle_state": "unknown",
            "media_url_state": "unknown",
            "fallback_failures": [],
        }
    allowed = {
        "metadata_source",
        "public_api_fallback_used",
        "public_api_adapter",
        "public_api_stage",
        "public_api_endpoint_label",
        "public_api_status",
        "public_api_requires_login",
        "public_api_uses_cookie",
        "requires_web_access",
        "subtitle_state",
        "media_url_state",
        "fallback_failures",
    }
    return {key: record.get(key) for key in allowed}


def _json_request(url: str, *, headers: dict[str, str] | None = None, retries: int = 1) -> tuple[dict[str, Any] | None, str | None]:
    last_error: str | None = None
    request_headers = dict(headers or {})
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers=request_headers)
            with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw), None
        except HTTPError as exc:
            last_error = f"http-{exc.code}"
        except (URLError, TimeoutError) as exc:
            last_error = f"network-error:{exc.reason if hasattr(exc, 'reason') else exc}"
        except json.JSONDecodeError as exc:
            last_error = f"invalid-json:{exc}"
            break
        if attempt < retries:
            time.sleep(0.5)
    return None, last_error


def _download_bytes(urls: list[str], path: Path, *, headers: dict[str, str]) -> tuple[bool, str | None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: str | None = None
    for url in urls:
        try:
            request = Request(url, headers=headers)
            with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                path.write_bytes(response.read())
            return True, None
        except HTTPError as exc:
            last_error = f"http-{exc.code}"
        except (URLError, TimeoutError) as exc:
            last_error = f"network-error:{exc.reason if hasattr(exc, 'reason') else exc}"
    return False, last_error


def _bilibili_ids(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    text = url
    bvid_match = re.search(r"\b(BV[0-9A-Za-z]+)\b", text)
    avid_match = re.search(r"(?:^|/|[?&])av(\d+)\b", text, re.I)
    if not avid_match and query.get("aid"):
        avid_match = re.match(r"(\d+)", query["aid"][0])
    ids: dict[str, str] = {}
    if bvid_match:
        ids["bvid"] = bvid_match.group(1)
    if avid_match:
        ids["aid"] = avid_match.group(1)
    if query.get("p"):
        ids["page"] = query["p"][0]
    if query.get("cid"):
        ids["cid"] = query["cid"][0]
    return ids


def _bilibili_view_url(ids: dict[str, str]) -> str | None:
    if ids.get("bvid"):
        return "https://api.bilibili.com/x/web-interface/view?" + urlencode({"bvid": ids["bvid"]})
    if ids.get("aid"):
        return "https://api.bilibili.com/x/web-interface/view?" + urlencode({"aid": ids["aid"]})
    return None


def _bilibili_page_url(bvid: str | None, aid: str | None, page: int | None) -> str:
    base = f"https://www.bilibili.com/video/{bvid or 'av' + str(aid or '')}/"
    if page and page > 1:
        return base + "?" + urlencode({"p": page})
    return base


def _bilibili_video_items(data: dict[str, Any], input_url: str) -> list[dict[str, Any]]:
    pages = data.get("pages") or []
    bvid = data.get("bvid")
    aid = data.get("aid")
    title = data.get("title") or "Bilibili video"
    owner = data.get("owner") or {}
    selected = _bilibili_ids(input_url)
    if selected.get("cid"):
        pages = [page for page in pages if str(page.get("cid")) == selected["cid"]] or pages
    elif selected.get("page"):
        pages = [page for page in pages if str(page.get("page")) == selected["page"]] or pages
    if not pages and data.get("cid"):
        pages = [{"cid": data.get("cid"), "page": 1, "part": title, "duration": data.get("duration")}]
    items: list[dict[str, Any]] = []
    multi = len(pages) > 1
    for index, page in enumerate(pages or [{}], start=1):
        page_no = int(page.get("page") or index)
        part = page.get("part") or title
        item_title = f"{title} - {part}" if multi and part and part != title else title
        video_id = str(bvid or aid or "bilibili")
        if multi:
            video_id = f"{video_id}_p{page_no}"
        item = {
            "id": video_id,
            "title": item_title,
            "webpage_url": _bilibili_page_url(str(bvid) if bvid else None, str(aid) if aid else None, page_no),
            "_download_url": _bilibili_page_url(str(bvid) if bvid else None, str(aid) if aid else None, page_no),
            "duration": page.get("duration") or data.get("duration"),
            "thumbnail": data.get("pic"),
            "description": data.get("desc"),
            "uploader": owner.get("name"),
            "channel_id": owner.get("mid"),
            "extractor": "BiliBiliPublicAPI",
            "extractor_key": "BiliBiliPublicAPI",
            "bilibili": {
                "bvid": bvid,
                "aid": aid,
                "cid": page.get("cid"),
                "page": page_no,
                "part": part,
            },
            "subtitles": {},
        }
        items.append(item)
    return items


def _bilibili_subtitle(url: str, bvid: str | None, aid: str | None, cid: Any, record: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    if not cid:
        record["subtitle_state"] = "missing-cid"
        record["fallback_failures"].append("Bilibili subtitle fallback cannot run without cid.")
        return {}, []
    params: dict[str, Any] = {"cid": cid}
    if bvid:
        params["bvid"] = bvid
    elif aid:
        params["aid"] = aid
    endpoint = "https://api.bilibili.com/x/player/v2?" + urlencode(params)
    payload, error = _json_request(endpoint, headers=BILIBILI_HEADERS, retries=1)
    if error or not payload:
        record["subtitle_state"] = "api-failed"
        record["fallback_failures"].append(f"Bilibili subtitle API failed: {error or 'empty-response'}")
        return {}, []
    if payload.get("code") not in (0, None):
        record["subtitle_state"] = "api-failed"
        record["fallback_failures"].append(f"Bilibili subtitle API returned code {payload.get('code')}.")
        return {}, []
    data = payload.get("data") or {}
    subtitle = data.get("subtitle") or {}
    tracks = subtitle.get("subtitles") or []
    need_login = bool(data.get("need_login_subtitle") or subtitle.get("need_login_subtitle"))
    if need_login and not tracks:
        record["subtitle_state"] = "requires-web-access"
        record["public_api_requires_login"] = True
        record["requires_web_access"] = True
        return {}, []
    if not tracks:
        record["subtitle_state"] = "empty"
        return {}, []
    ytdlp_subtitles: dict[str, list[dict[str, Any]]] = {}
    public_tracks: list[dict[str, Any]] = []
    for index, track in enumerate(tracks, start=1):
        raw_url = track.get("subtitle_url") or track.get("url")
        if not raw_url:
            continue
        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url
        lang = str(track.get("lan") or track.get("lang") or track.get("language") or f"und-{index}")
        item = {
            "lang": lang,
            "name": track.get("lan_doc") or track.get("name") or lang,
            "url": raw_url,
            "ext": "json",
            "source": "public_api",
            "adapter": "bilibili",
            "endpoint_label": ADAPTER_REGISTRY["bilibili"]["endpoint_labels"]["subtitle"],
            "headers": {"User-Agent": BILIBILI_HEADERS["User-Agent"], "Referer": url},
        }
        public_tracks.append(item)
        ytdlp_subtitles.setdefault(lang, []).append(
            {
                "url": raw_url,
                "ext": "json",
                "name": item["name"],
                "source": "public_api",
            }
        )
    record["subtitle_state"] = "available" if public_tracks else "empty"
    return ytdlp_subtitles, public_tracks


def _bilibili_media(url: str, bvid: str | None, aid: str | None, cid: Any, record: dict[str, Any]) -> dict[str, Any] | None:
    if not cid:
        record["media_url_state"] = "missing-cid"
        record["fallback_failures"].append("Bilibili media fallback cannot run without cid.")
        return None
    params: dict[str, Any] = {"cid": cid, "fnval": 16, "qn": 16, "fourk": 0}
    if bvid:
        params["bvid"] = bvid
    elif aid:
        params["avid"] = aid
    endpoint = "https://api.bilibili.com/x/player/playurl?" + urlencode(params)
    payload, error = _json_request(endpoint, headers=BILIBILI_HEADERS, retries=1)
    if error or not payload:
        record["media_url_state"] = "api-failed"
        record["fallback_failures"].append(f"Bilibili playurl API failed: {error or 'empty-response'}")
        return None
    if payload.get("code") not in (0, None):
        code = payload.get("code")
        state = "requires-web-access" if str(code) in {"-403", "-404", "-10403"} else "api-failed"
        record["media_url_state"] = state
        if state == "requires-web-access":
            record["requires_web_access"] = True
        record["fallback_failures"].append(f"Bilibili playurl API returned code {code}.")
        return None
    data = payload.get("data") or {}
    dash = data.get("dash") or {}
    audio = sorted(dash.get("audio") or [], key=lambda item: item.get("bandwidth") or 0, reverse=True)
    video = sorted(dash.get("video") or [], key=lambda item: item.get("bandwidth") or 0, reverse=True)
    durl = data.get("durl") or []

    def stream(item: dict[str, Any], kind: str) -> dict[str, Any]:
        primary = item.get("baseUrl") or item.get("base_url") or item.get("url")
        backups = item.get("backupUrl") or item.get("backup_url") or []
        if isinstance(backups, str):
            backups = [backups]
        return {
            "kind": kind,
            "url": primary,
            "backup_urls": [value for value in backups if value],
            "mime_type": item.get("mimeType") or item.get("mime_type"),
            "codecs": item.get("codecs"),
            "bandwidth": item.get("bandwidth"),
            "headers": {"User-Agent": BILIBILI_HEADERS["User-Agent"], "Referer": url},
        }

    media: dict[str, Any] = {
        "adapter": "bilibili",
        "endpoint_label": ADAPTER_REGISTRY["bilibili"]["endpoint_labels"]["media"],
        "expires": "temporary",
        "referer_required": True,
        "audio": stream(audio[0], "audio") if audio else None,
        "video": stream(video[0], "video") if video else None,
        "progressive": stream(durl[0], "progressive") if durl else None,
    }
    if not any(media.get(key) and media[key].get("url") for key in ("audio", "video", "progressive")):
        record["media_url_state"] = "empty"
        return None
    record["media_url_state"] = "available"
    return media


def fetch_public_api_info(
    url: str,
    *,
    disabled: bool = False,
    stages: tuple[str, ...] = PUBLIC_API_STAGES,
) -> dict[str, Any] | None:
    if disabled:
        return None
    adapter = adapter_for_url(url)
    if not adapter:
        return None
    if adapter["id"] != "bilibili":
        return None
    ids = _bilibili_ids(url)
    view_url = _bilibili_view_url(ids)
    record = base_record(url, adapter=adapter, stages=stages, source="public_api")
    record["public_api_fallback_used"] = True
    if not view_url:
        record["public_api_status"] = "invalid-url"
        record["fallback_failures"].append("Bilibili URL does not contain a BV or av id.")
        return None
    payload, error = _json_request(view_url, headers=BILIBILI_HEADERS, retries=1)
    if error or not payload:
        record["public_api_status"] = "api-failed"
        record["fallback_failures"].append(f"Bilibili metadata API failed: {error or 'empty-response'}")
        return None
    if payload.get("code") not in (0, None):
        record["public_api_status"] = "api-failed"
        record["fallback_failures"].append(f"Bilibili metadata API returned code {payload.get('code')}.")
        return None
    data = payload.get("data") or {}
    items = _bilibili_video_items(data, url)
    if not items:
        record["public_api_status"] = "api-failed"
        record["fallback_failures"].append("Bilibili metadata API returned no playable pages.")
        return None
    for item in items:
        item_record = dict(record)
        if "metadata" not in stages:
            item_record["metadata_source"] = "yt_dlp"
        bilibili = item.get("bilibili") or {}
        if "subtitle" in stages:
            subtitles, public_tracks = _bilibili_subtitle(
                item.get("webpage_url") or url,
                str(bilibili.get("bvid")) if bilibili.get("bvid") else None,
                str(bilibili.get("aid")) if bilibili.get("aid") else None,
                bilibili.get("cid"),
                item_record,
            )
            if subtitles:
                item["subtitles"] = subtitles
                item["public_api_subtitles"] = public_tracks
        if "media" in stages:
            media = _bilibili_media(
                item.get("webpage_url") or url,
                str(bilibili.get("bvid")) if bilibili.get("bvid") else None,
                str(bilibili.get("aid")) if bilibili.get("aid") else None,
                bilibili.get("cid"),
                item_record,
            )
            if media:
                item["public_api_media"] = media
        item_record["public_api_status"] = (
            "partial"
            if item_record["fallback_failures"] or item_record.get("requires_web_access")
            else "ok"
        )
        item["public_api_fallback"] = item_record
    info: dict[str, Any] = {
        "id": str(data.get("bvid") or data.get("aid") or "bilibili"),
        "title": data.get("title") or "Bilibili video",
        "webpage_url": items[0].get("webpage_url") or url,
        "extractor": "BiliBiliPublicAPI",
        "extractor_key": "BiliBiliPublicAPI",
        "public_api_fallback": record,
    }
    if len(items) == 1:
        info.update(items[0])
    else:
        info["entries"] = items
    return info


def supplement_public_api_info(
    info: dict[str, Any],
    url: str,
    *,
    disabled: bool = False,
    stages: tuple[str, ...] = ("subtitle", "media"),
) -> dict[str, Any]:
    if disabled or not adapter_for_url(url):
        return info
    public_info = fetch_public_api_info(url, disabled=disabled, stages=stages)
    if not public_info:
        return info
    public_items = public_info.get("entries") or [public_info]
    public_by_cid = {
        str((item.get("bilibili") or {}).get("cid")): item
        for item in public_items
        if (item.get("bilibili") or {}).get("cid") is not None
    }
    public_by_id = {str(item.get("id")): item for item in public_items if item.get("id")}
    target_items = info.get("entries") or [info]
    for item in target_items:
        cid = str(item.get("cid") or (item.get("bilibili") or {}).get("cid") or "")
        public_item = public_by_cid.get(cid) or public_by_id.get(str(item.get("id"))) or (public_items[0] if len(public_items) == 1 else None)
        if not public_item:
            continue
        if not item.get("subtitles") and public_item.get("subtitles"):
            item["subtitles"] = public_item["subtitles"]
        for key in ("public_api_fallback", "public_api_subtitles", "public_api_media", "bilibili"):
            if public_item.get(key):
                item[key] = public_item[key]
    if info.get("entries"):
        return info
    return target_items[0]


def _subtitle_body_from_bilibili_json(raw: str, *, keep_timestamps: bool = False) -> str:
    payload = json.loads(raw)
    body = payload.get("body") or []
    lines: list[str] = []
    for cue in body:
        text = str(cue.get("content") or "").strip()
        if not text:
            continue
        if keep_timestamps:
            start = cue.get("from")
            try:
                seconds = int(float(start))
                stamp = f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"
            except (TypeError, ValueError):
                stamp = "00:00:00"
            lines.append(f"### {stamp}\n\n{text}")
        else:
            lines.append(text)
    return "\n\n".join(lines).strip()


def public_subtitle_languages(video: dict[str, Any]) -> list[str]:
    return [str(track.get("lang")) for track in video.get("public_api_subtitles") or [] if track.get("lang")]


def download_public_subtitle(
    video: dict[str, Any],
    lang: str,
    output_dir: Path,
    *,
    keep_timestamps: bool = False,
    filename_stem: str = "subtitle",
) -> dict[str, Any]:
    tracks = [track for track in video.get("public_api_subtitles") or [] if str(track.get("lang")) == lang]
    if not tracks:
        return {"status": "missing", "paths": [], "body": "", "error": "No public API subtitle track matched."}
    track = tracks[0]
    safe_lang = re.sub(r"[^A-Za-z0-9_.-]+", "_", lang)
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename_stem)[:80] or "subtitle"
    raw_path = output_dir / f"{safe_stem}.{safe_lang}.public-api.json"
    text_path = output_dir / f"{safe_stem}.{safe_lang}.public-api.txt"
    ok, error = _download_bytes([track["url"]], raw_path, headers=track.get("headers") or BILIBILI_HEADERS)
    if not ok:
        return {"status": "failed", "paths": [], "body": "", "error": error}
    raw = raw_path.read_text(encoding="utf-8", errors="replace")
    try:
        body = _subtitle_body_from_bilibili_json(raw, keep_timestamps=keep_timestamps)
    except (json.JSONDecodeError, OSError) as exc:
        return {"status": "failed", "paths": [str(raw_path)], "body": "", "error": f"subtitle-parse-failed:{exc}"}
    text_path.write_text(body + "\n", encoding="utf-8")
    return {"status": "downloaded", "paths": [str(raw_path), str(text_path)], "body": body, "text_path": str(text_path)}


def _media_extension(stream: dict[str, Any], fallback: str) -> str:
    mime = str(stream.get("mime_type") or "").lower()
    codecs = str(stream.get("codecs") or "").lower()
    if "audio" in mime:
        return "m4a"
    if "video" in mime:
        return "mp4"
    if "mp4" in mime or "avc" in codecs or "mp4a" in codecs:
        return "mp4"
    return fallback


def download_public_media(
    video: dict[str, Any],
    output_dir: Path,
    *,
    audio_only: bool = False,
    filename_stem: str = "media",
) -> dict[str, Any]:
    media = video.get("public_api_media") or {}
    if not media:
        return {"status": "missing", "paths": [], "warnings": ["No public API media candidate is available."]}
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename_stem)[:80] or "media"
    streams: list[tuple[str, dict[str, Any]]] = []
    if media.get("progressive"):
        streams.append(("progressive", media["progressive"]))
    else:
        if media.get("audio"):
            streams.append(("audio", media["audio"]))
        if not audio_only and media.get("video"):
            streams.append(("video", media["video"]))
    paths: list[str] = []
    warnings: list[str] = []
    for kind, stream in streams:
        if not stream.get("url"):
            continue
        ext = _media_extension(stream, "m4a" if kind == "audio" else "mp4")
        path = output_dir / f"{safe_stem}.public-api.{kind}.{ext}"
        urls = [stream["url"], *(stream.get("backup_urls") or [])]
        ok, error = _download_bytes(urls, path, headers=stream.get("headers") or BILIBILI_HEADERS)
        if ok:
            paths.append(str(path))
        else:
            warnings.append(f"{kind} stream download failed: {error}")
    status = "downloaded" if paths else "failed"
    if paths and not audio_only and len(paths) > 1:
        warnings.append("Public API fallback downloaded separate streams; merge with ffmpeg if a single container is required.")
    return {"status": status, "paths": paths, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect registered public API fallback adapters.")
    parser.add_argument("--json", action="store_true", help="Print adapter registry as JSON")
    args = parser.parse_args(argv)
    report = public_api_doctor(False)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Public API fallback adapters:")
        for adapter in report["adapters"]:
            print(
                f"- {adapter['id']}: domains={', '.join(adapter['domains'])}; "
                f"stages={', '.join(adapter['stages'])}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
