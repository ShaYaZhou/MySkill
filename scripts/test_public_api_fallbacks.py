#!/usr/bin/env python3
"""Offline checks for public API fallback behavior."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "video-transcript" / "scripts" / "public_api_fallbacks.py"


def load_helper() -> Any:
    spec = importlib.util.spec_from_file_location("public_api_fallbacks_under_test", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load helper: {HELPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    helper = load_helper()
    calls: list[str] = []
    subtitle_mode = {"value": "requires-login"}

    def fake_json_request(url: str, *, headers: dict[str, str] | None = None, retries: int = 1):
        calls.append(url)
        if "x/web-interface/view" in url:
            return {
                "code": 0,
                "data": {
                    "bvid": "BV1mock12345",
                    "aid": 123,
                    "title": "Mock Bilibili Video",
                    "duration": 60,
                    "pic": "https://i.example.invalid/pic.jpg",
                    "desc": "mock description",
                    "owner": {"name": "mock owner", "mid": 1},
                    "pages": [{"cid": 456, "page": 1, "part": "P1", "duration": 60}],
                },
            }, None
        if "x/player/v2" in url:
            if subtitle_mode["value"] == "available":
                return {
                    "code": 0,
                    "data": {
                        "need_login_subtitle": False,
                        "subtitle": {
                            "subtitles": [
                                {
                                    "lan": "zh-Hans",
                                    "lan_doc": "Chinese",
                                    "subtitle_url": "//subtitle.example.invalid/sub.json?token=secret",
                                }
                            ]
                        },
                    },
                }, None
            return {"code": 0, "data": {"need_login_subtitle": True, "subtitle": {"subtitles": []}}}, None
        if "x/player/playurl" in url:
            return {
                "code": 0,
                "data": {
                    "dash": {
                        "audio": [
                            {
                                "baseUrl": "https://media.example.invalid/audio.m4s?token=secret",
                                "backupUrl": [],
                                "mimeType": "audio/mp4",
                                "bandwidth": 64000,
                            }
                        ],
                        "video": [],
                    }
                },
            }, None
        return None, "unexpected-url"

    helper._json_request = fake_json_request

    assert helper.adapter_for_url("https://www.bilibili.com/video/BV1mock12345/")["id"] == "bilibili"
    unsupported = helper.public_api_plan("https://example.invalid/watch")
    assert unsupported["public_api_status"] == "unsupported-public-api"

    info = helper.fetch_public_api_info(
        "https://www.bilibili.com/video/BV1mock12345/",
        stages=helper.PUBLIC_API_STAGES,
    )
    assert info is not None
    fields = helper.public_api_summary_fields(info)
    assert fields["metadata_source"] == "public_api"
    assert fields["public_api_adapter"] == "bilibili"
    assert fields["subtitle_state"] == "requires-web-access"
    assert fields["media_url_state"] == "available"
    assert fields["requires_web_access"] is True
    assert "secret" not in str(fields)

    subtitle_mode["value"] = "available"
    info = helper.fetch_public_api_info(
        "https://www.bilibili.com/video/BV1mock12345/",
        stages=helper.PUBLIC_API_STAGES,
    )
    assert info is not None
    assert info["subtitles"]["zh-Hans"][0]["source"] == "public_api"
    assert helper.public_api_summary_fields(info)["subtitle_state"] == "available"

    def fake_download_bytes(urls, path, *, headers):
        assert "token=secret" in urls[0]
        return False, "http-403"

    helper._download_bytes = fake_download_bytes
    with tempfile.TemporaryDirectory() as tmp:
        media_result = helper.download_public_media(info, Path(tmp), audio_only=True, filename_stem="mock")
    assert media_result["status"] == "failed"
    assert "token=secret" not in str(media_result)

    disabled = helper.disabled_record("https://www.bilibili.com/video/BV1mock12345/")
    assert disabled["public_api_status"] == "disabled"
    assert calls
    print("public_api_fallbacks: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
