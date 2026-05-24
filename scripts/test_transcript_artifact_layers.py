#!/usr/bin/env python3
"""Offline checks for video-transcript artifact layer helpers."""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "video-transcript" / "scripts"


def load_transcript() -> Any:
    sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("transcript_under_test", SCRIPT_DIR / "transcript.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load transcript.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    transcript = load_transcript()
    args = argparse.Namespace(output_profile="all", artifact=None)
    assert transcript.requested_artifacts(args) == [
        "raw_asr",
        "speech_transcript",
        "chapter_handout",
        "html_render",
    ]
    args = argparse.Namespace(output_profile="raw", artifact=["speech", "chapters"])
    assert transcript.requested_artifacts(args) == ["speech_transcript", "chapter_handout"]
    assert transcript.expand_artifacts_for_generation(["html_render"]) == [
        "speech_transcript",
        "chapter_handout",
        "html_render",
    ]
    assert transcript.generation_artifacts_for_request(["html_render"], "raw_asr") == [
        "raw_asr",
        "speech_transcript",
        "chapter_handout",
        "html_render",
    ]
    assert transcript.generation_artifacts_for_request(["html_render"], "speech_transcript") == [
        "speech_transcript",
        "chapter_handout",
        "html_render",
    ]

    kimi_choice = {"provider": "moonshot", "mode": "video-understanding", "provider_capability_type": "video-understanding"}
    assert transcript.primary_artifact_for_choice(kimi_choice) == "speech_transcript"
    assert transcript.raw_asr_only_blocked(["raw_asr"], "speech_transcript")
    assert not transcript.raw_asr_only_blocked(["raw_asr", "speech_transcript"], "speech_transcript")
    minimax_choice = {"provider": "minimax", "mode": "audio-asr", "provider_capability_type": "audio-asr"}
    assert transcript.primary_artifact_for_choice(minimax_choice) == "raw_asr"

    record = transcript.artifact_record(
        "speech_transcript",
        "C:/out/speech.md",
        source_artifact="raw_asr",
        source_type="raw_asr",
        provider="local-cleanup",
        model=None,
        derivation_stage="derived",
    )
    assert record["allowed_transform"] == "light_cleanup_no_reorder"
    assert record["status"] == "generated"

    video = {"title": "测试视频", "_download_url": "https://example.invalid/watch"}
    raw = transcript.markdown_document(video, "第一段\n\n第二段", source="test ASR", language="zh")
    speech = transcript.generate_speech_from_raw(raw, video)
    assert "Transcript source: light cleanup from raw ASR" in speech
    chapter = transcript.generate_chapter_fallback(speech, video)
    assert "artifact" not in chapter.lower()
    assert "本文件是由转写稿派生的章节讲义" in chapter
    html = transcript.render_markdown_html(chapter, "测试视频")
    assert "<html" in html and "测试视频" in html

    with tempfile.TemporaryDirectory() as tmp:
        path = transcript.write_artifact_file(Path(tmp) / "speech.md", speech)
        assert path.exists()
        video_dir = Path(tmp) / "测试视频 [abc]"
        video_dir.mkdir()
        (video_dir / "original.md").write_text(raw, encoding="utf-8")
        metadata = {"status": "success", "source": "human_subtitle", "artifacts": []}
        assert not transcript.existing_success_satisfies_request(video_dir, video, metadata, args)
        transcript.ensure_existing_artifact_records(metadata, video_dir, video)
        assert transcript.first_artifact_path(metadata, "raw_asr")
    print("transcript_artifact_layers: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
