#!/usr/bin/env python3
"""Create Markdown transcripts from video or playlist URLs."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import html
import importlib.util
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

from public_api_fallbacks import (
    PUBLIC_API_STAGES,
    adapter_for_url,
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
DEFAULT_OUTPUT_DIR = Path("~/Documents/video-transcripts").expanduser()
SAFE_UPLOAD_BYTES = 24 * 1024 * 1024
KIMI_SAFE_VIDEO_BYTES = 70 * 1024 * 1024
MOONSHOT_BASE_URLS = ("https://api.moonshot.ai/v1", "https://api.moonshot.cn/v1")
MINIMAX_CN_BASE_URL = "https://api.minimaxi.com/v1"
MINIMAX_GLOBAL_BASE_URL = "https://api.minimax.io/v1"
MINIMAX_BASE_URL = MINIMAX_CN_BASE_URL
ZH_PATTERNS = ("zh", "zh-*", "zh-Hans", "zh-Hant", "zh-CN", "zh-TW")
ORIGINAL_LANG_PREFERENCE = ("en", "en-*", "ja", "ja-*", "ko", "ko-*", "fr", "de", "es", "pt", "it")
DEFAULT_TRANSCRIPTION_PROMPT = (
    "Create a faithful transcript in the original language. Preserve spoken math, equations, "
    "variables, symbols, and units as Markdown LaTeX when possible: inline math as $...$ and "
    "display equations as $$...$$. Do not summarize, paraphrase, or add content that was not spoken."
)
TRANSCRIBE_MODES = (
    "audio-asr",
    "video-understanding",
    "audio-to-llm",
    "openai-compatible",
    "custom-proxy",
    "proxy-asr",
    "unsupported-direct",
)
ARTIFACT_ALIASES = {
    "raw": "raw_asr",
    "asr": "raw_asr",
    "raw_asr": "raw_asr",
    "speech": "speech_transcript",
    "speech_transcript": "speech_transcript",
    "chapters": "chapter_handout",
    "chapter": "chapter_handout",
    "chapter_handout": "chapter_handout",
    "html": "html_render",
    "html_render": "html_render",
}
OUTPUT_PROFILE_ARTIFACTS = {
    "default": (),
    "raw": ("raw_asr",),
    "speech": ("speech_transcript",),
    "chapters": ("speech_transcript", "chapter_handout"),
    "html": ("speech_transcript", "chapter_handout", "html_render"),
    "all": ("raw_asr", "speech_transcript", "chapter_handout", "html_render"),
}
ARTIFACT_DEPENDENCIES = {
    "chapter_handout": ("speech_transcript",),
    "html_render": ("chapter_handout",),
}
ASR_CAPABLE_PROVIDERS = {"openai", "minimax", "openai-compatible", "custom-proxy"}
ASR_CAPABLE_MODES = {"audio-asr", "openai-compatible", "proxy-asr", "custom-proxy"}
PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
    "openai": {
        "display_name": "OpenAI",
        "capability_type": "audio-asr",
        "default_mode": "audio-asr",
        "auth_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini-transcribe",
        "default_model_env": "OPENAI_TRANSCRIBE_MODEL",
        "uploads_media": True,
        "requires_media_download": True,
        "paid_or_quota_risk": True,
        "region_risk": "global",
        "limitations": "专用音频转写；需要下载音频并上传 API。",
    },
    "moonshot": {
        "display_name": "Moonshot/Kimi",
        "capability_type": "video-understanding",
        "default_mode": "video-understanding",
        "auth_env": "MOONSHOT_API_KEY",
        "base_url_env": "MOONSHOT_BASE_URL",
        "default_model": "kimi-k2.6",
        "default_model_env": "KIMI_MODEL",
        "uploads_media": True,
        "requires_media_download": True,
        "paid_or_quota_risk": True,
        "region_risk": "cn/global endpoint auto-detect",
        "limitations": "视频理解式转写，非专用逐字 ASR；精确措辞需要复核。",
    },
    "minimax": {
        "display_name": "MiniMax",
        "capability_type": "audio-asr",
        "default_mode": "audio-asr",
        "auth_env": "MINIMAX_API_KEY",
        "base_url_env": "MINIMAX_BASE_URL",
        "endpoint_env": "MINIMAX_TRANSCRIBE_URL",
        "default_model": "speech-2.8-turbo",
        "default_model_env": "MINIMAX_ASR_MODEL",
        "uploads_media": True,
        "requires_media_download": True,
        "paid_or_quota_risk": True,
        "region_risk": "cn/global endpoint must match key region",
        "limitations": "专用音频转写；国内 key 默认使用 https://api.minimaxi.com/v1。",
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "capability_type": "unsupported-direct",
        "default_mode": "unsupported-direct",
        "auth_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "default_model": "deepseek-chat",
        "default_model_env": "DEEPSEEK_MODEL",
        "uploads_media": False,
        "requires_media_download": False,
        "paid_or_quota_risk": True,
        "region_risk": "depends on endpoint",
        "limitations": "默认只按文本/兼容接口登记；直接音频转写需要代理或自定义 endpoint。",
    },
    "glm": {
        "display_name": "GLM",
        "capability_type": "unsupported-direct",
        "default_mode": "unsupported-direct",
        "auth_env": "GLM_API_KEY",
        "base_url_env": "GLM_BASE_URL",
        "default_model": "glm-4",
        "default_model_env": "GLM_MODEL",
        "uploads_media": False,
        "requires_media_download": False,
        "paid_or_quota_risk": True,
        "region_risk": "depends on endpoint",
        "limitations": "默认不声明可直接 ASR；需要代理或用户配置可用音视频 endpoint。",
    },
    "gemini": {
        "display_name": "Gemini",
        "capability_type": "audio-to-llm",
        "default_mode": "audio-to-llm",
        "auth_env": "GEMINI_API_KEY",
        "base_url_env": "GEMINI_BASE_URL",
        "default_model": "gemini-2.5-flash",
        "default_model_env": "GEMINI_MODEL",
        "uploads_media": True,
        "requires_media_download": True,
        "paid_or_quota_risk": True,
        "region_risk": "depends on account and region",
        "limitations": "按理解式转写登记；本脚本首版仅通过代理/兼容 endpoint 执行。",
    },
    "claude": {
        "display_name": "Claude",
        "capability_type": "unsupported-direct",
        "default_mode": "unsupported-direct",
        "auth_env": "ANTHROPIC_API_KEY",
        "base_url_env": "ANTHROPIC_BASE_URL",
        "default_model": "claude-sonnet-4-5",
        "default_model_env": "CLAUDE_MODEL",
        "uploads_media": False,
        "requires_media_download": False,
        "paid_or_quota_risk": True,
        "region_risk": "depends on endpoint",
        "limitations": "默认不声明可直接 ASR；需要代理或用户配置可用音视频 endpoint。",
    },
    "openai-compatible": {
        "display_name": "OpenAI-compatible 代理",
        "capability_type": "openai-compatible",
        "default_mode": "openai-compatible",
        "auth_env": "OPENAI_COMPATIBLE_API_KEY",
        "base_url_env": "OPENAI_COMPATIBLE_BASE_URL",
        "endpoint_env": "OPENAI_COMPATIBLE_TRANSCRIBE_URL",
        "default_model": "gpt-4o-mini-transcribe",
        "default_model_env": "OPENAI_COMPATIBLE_TRANSCRIBE_MODEL",
        "uploads_media": True,
        "requires_media_download": True,
        "paid_or_quota_risk": True,
        "region_risk": "depends on proxy",
        "limitations": "按 OpenAI audio/transcriptions 兼容格式发送 multipart 请求。",
    },
    "custom-proxy": {
        "display_name": "自定义转写代理",
        "capability_type": "custom-proxy",
        "default_mode": "custom-proxy",
        "auth_env": "CUSTOM_TRANSCRIBE_API_KEY",
        "base_url_env": "CUSTOM_TRANSCRIBE_BASE_URL",
        "endpoint_env": "CUSTOM_TRANSCRIBE_URL",
        "default_model": "transcribe",
        "default_model_env": "CUSTOM_TRANSCRIBE_MODEL",
        "uploads_media": True,
        "requires_media_download": True,
        "paid_or_quota_risk": True,
        "region_risk": "depends on proxy",
        "limitations": "首版使用 OpenAI-style multipart 请求；非兼容格式需要后续适配器。",
    },
}
BACKEND_PROVIDER_MAP = {
    "openai": ("openai", "audio-asr"),
    "kimi-video": ("moonshot", "video-understanding"),
    "minimax-api": ("minimax", "audio-asr"),
}
PROXY_EXECUTION_MODES = {"openai-compatible", "custom-proxy", "proxy-asr"}
DIRECT_EXECUTION_PROVIDERS = {"openai", "moonshot", "minimax"}


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

    probe = run([str(VENV_PYTHON), "-c", "import yt_dlp, openai, requests"], check=False, capture=True)
    if update or probe.returncode != 0:
        print("Installing/updating transcript dependencies...")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-U", "pip"])
        run([str(VENV_PYTHON), "-m", "pip", "install", "-U", "yt-dlp[default]", "openai", "requests"])


def reexec_in_venv(args: list[str]) -> None:
    if "-h" in args or "--help" in args:
        return
    if Path(sys.prefix).resolve() == VENV_DIR.resolve():
        return
    update = "--update" in args
    ensure_venv(update)
    if os.name == "nt":
        result = run([str(VENV_PYTHON), str(Path(__file__).resolve()), *args], check=False)
        raise SystemExit(result.returncode)
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *args])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Markdown transcripts from video or playlist URLs.",
    )
    parser.add_argument("urls", nargs="*", help="Video or playlist URLs to process")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Transcript output directory")
    parser.add_argument("--cookies-from-browser", help="Browser to load cookies from, e.g. chrome or safari")
    parser.add_argument(
        "--transcribe-backend",
        choices=("auto", "openai", "kimi-video", "minimax-api"),
        default="auto",
        help="Legacy fallback backend when no human subtitles are available",
    )
    parser.add_argument(
        "--transcribe-provider",
        choices=tuple(PROVIDER_REGISTRY),
        help="Provider id for no-subtitle transcription, e.g. minimax, openai, openai-compatible, custom-proxy.",
    )
    parser.add_argument(
        "--transcribe-mode",
        choices=TRANSCRIBE_MODES,
        help="Provider execution mode, e.g. audio-asr, video-understanding, openai-compatible, proxy-asr.",
    )
    parser.add_argument("--transcribe-model", default="gpt-4o-mini-transcribe", help="OpenAI transcription model")
    parser.add_argument("--kimi-model", default="kimi-k2.6", help="Kimi/Moonshot model for video transcript or translation")
    parser.add_argument(
        "--transcribe-base-url",
        default=os.environ.get("TRANSCRIBE_BASE_URL"),
        help="Generic provider/proxy base URL. Use endpoint-specific variables when possible.",
    )
    parser.add_argument(
        "--transcribe-endpoint",
        default=os.environ.get("TRANSCRIBE_ENDPOINT"),
        help="Full provider/proxy audio transcription endpoint URL. Only a redacted host is recorded.",
    )
    parser.add_argument(
        "--transcribe-auth-env",
        default=os.environ.get("TRANSCRIBE_AUTH_ENV", ""),
        help="Environment variable name that contains the provider/proxy API key; the value is never logged.",
    )
    parser.add_argument(
        "--minimax-base-url",
        default=os.environ.get("MINIMAX_BASE_URL") or os.environ.get("MINIMAX_API_BASE") or MINIMAX_BASE_URL,
        help=(
            "MiniMax API base URL. Defaults to domestic China endpoint https://api.minimaxi.com/v1. "
            "Use https://api.minimax.io/v1 for global keys."
        ),
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
    parser.add_argument(
        "--output-profile",
        choices=tuple(OUTPUT_PROFILE_ARTIFACTS),
        default="default",
        help="Artifact profile: default, raw, speech, chapters, html, or all.",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        choices=tuple(ARTIFACT_ALIASES),
        help="Artifact layer to generate. Repeatable; overrides --output-profile.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Inspect URLs and write summaries without downloading media or transcribing")
    parser.add_argument("--doctor", action="store_true", help="Check local dependencies and environment without requiring URLs")
    parser.add_argument("--no-public-api-fallback", action="store_true", help="Disable public, no-auth site API fallback adapters")
    parser.add_argument("--force", action="store_true", help="Overwrite existing transcript outputs; current default behavior is overwrite-compatible")
    parser.add_argument("--update", action="store_true", help="Update isolated dependencies before processing")
    parser.add_argument(
        "--save-default-provider",
        action="store_true",
        help="Save the explicit provider choice as the user default without storing the API key value.",
    )
    parser.add_argument(
        "--clear-default-provider",
        action="store_true",
        help="Clear the saved user default transcription provider and exit if no URLs are provided.",
    )
    parser.add_argument(
        "--ignore-default-provider",
        action="store_true",
        help="Ignore the saved user default provider for this run.",
    )
    args = parser.parse_args()
    can_run_without_urls = args.doctor or args.clear_default_provider or (args.save_default_provider and (args.transcribe_provider or args.transcribe_backend != "auto"))
    if not can_run_without_urls and not args.urls:
        parser.error("the following arguments are required unless --doctor is used: urls")
    return args


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def redact_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        return value
    redacted = parsed._replace(query="<redacted>" if parsed.query else "", fragment="<redacted>" if parsed.fragment else "")
    return redacted.geturl()


def sanitize_argv(argv: list[str]) -> list[str]:
    sanitized: list[str] = []
    redact_next: str | None = None
    for arg in argv:
        option_name = arg.split("=", 1)[0].lower()
        sensitive_option = any(token in option_name for token in ("key", "token", "secret", "password"))
        endpoint_option = "endpoint" in option_name or "base-url" in option_name or "base_url" in option_name
        if redact_next:
            sanitized.append("<redacted>" if redact_next == "secret" else endpoint_label(arg) or "<endpoint>")
            redact_next = None
            continue
        if sensitive_option:
            if "=" in arg:
                sanitized.append(arg.split("=", 1)[0] + "=<redacted>")
            else:
                sanitized.append(arg)
                redact_next = "secret"
            continue
        if endpoint_option:
            if "=" in arg:
                key, value = arg.split("=", 1)
                sanitized.append(key + "=" + (endpoint_label(value) or "<endpoint>"))
            else:
                sanitized.append(arg)
                redact_next = "endpoint"
            continue
        sanitized.append(redact_url(arg))
    return sanitized


class ProviderSelectionRequired(RuntimeError):
    def __init__(self, message: str, plan: dict[str, Any]) -> None:
        super().__init__(message)
        self.plan = plan


class ProviderBlocked(RuntimeError):
    def __init__(self, message: str, choice: dict[str, Any]) -> None:
        super().__init__(message)
        self.choice = choice


class ProviderConfigurationError(RuntimeError):
    pass


def provider_default_path() -> Path:
    override = os.environ.get("VIDEO_TRANSCRIPT_DEFAULT_PROVIDER_PATH")
    if override:
        return Path(override).expanduser()
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "MySkill" / "video-transcript" / "provider-default.json"
    return Path("~/.config/MySkill/video-transcript/provider-default.json").expanduser()


def load_default_provider() -> dict[str, Any] | None:
    path = provider_default_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    provider = data.get("default_provider")
    if provider not in PROVIDER_REGISTRY:
        return None
    return data


def save_default_provider(choice: dict[str, Any]) -> Path:
    path = provider_default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "default_provider": choice["provider"],
        "default_mode": choice["mode"],
        "auth_env": choice.get("auth_env"),
        "model": choice.get("model"),
        "model_env": choice.get("model_env"),
        "endpoint_label": choice.get("endpoint_label"),
        "selection_source": "user-confirmed-default",
        "updated_at": utc_now(),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def clear_default_provider() -> Path:
    path = provider_default_path()
    if path.exists():
        path.unlink()
    return path


def endpoint_label(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return parsed.netloc
    return str(value).split("?", 1)[0].strip() or None


def env_value(name: str | None) -> str | None:
    return os.environ.get(name or "")


def provider_model(provider_id: str, args: argparse.Namespace, default_data: dict[str, Any] | None = None) -> str:
    if default_data and not explicit_provider_requested(args) and default_data.get("model"):
        return str(default_data["model"])
    if provider_id == "openai":
        return args.transcribe_model
    if provider_id == "moonshot":
        return args.kimi_model
    if provider_id == "minimax":
        return args.minimax_model
    if default_data and default_data.get("model"):
        return str(default_data["model"])
    config = PROVIDER_REGISTRY[provider_id]
    model_env = str(config.get("default_model_env") or "")
    return os.environ.get(model_env) or str(config.get("default_model") or args.transcribe_model)


def provider_base_url(provider_id: str, args: argparse.Namespace, default_data: dict[str, Any] | None = None) -> str | None:
    if args.transcribe_base_url:
        return args.transcribe_base_url
    if provider_id == "minimax":
        return args.minimax_base_url
    if default_data and default_data.get("base_url"):
        return str(default_data["base_url"])
    config = PROVIDER_REGISTRY[provider_id]
    return env_value(str(config.get("base_url_env") or ""))


def provider_endpoint(provider_id: str, args: argparse.Namespace, default_data: dict[str, Any] | None = None) -> str | None:
    if args.transcribe_endpoint:
        return args.transcribe_endpoint
    if provider_id == "minimax":
        return minimax_transcribe_url(args)
    if default_data and default_data.get("endpoint"):
        return str(default_data["endpoint"])
    config = PROVIDER_REGISTRY[provider_id]
    configured = env_value(str(config.get("endpoint_env") or ""))
    if configured:
        return configured
    base_url = provider_base_url(provider_id, args, default_data)
    effective_mode = args.transcribe_mode or str((default_data or {}).get("default_mode") or "")
    if base_url and (provider_id in {"openai-compatible", "custom-proxy"} or effective_mode in PROXY_EXECUTION_MODES):
        return base_url.rstrip("/") + "/audio/transcriptions"
    return None


def explicit_provider_requested(args: argparse.Namespace) -> bool:
    return bool(
        args.transcribe_provider
        or args.transcribe_mode
        or args.transcribe_base_url
        or args.transcribe_endpoint
        or args.transcribe_auth_env
        or args.transcribe_backend != "auto"
    )


def provider_option_status(provider_id: str, args: argparse.Namespace) -> dict[str, Any]:
    config = PROVIDER_REGISTRY[provider_id]
    auth_env = str(config.get("auth_env") or "")
    key_present = bool(env_value(auth_env))
    endpoint = provider_endpoint(provider_id, args)
    capability = str(config.get("capability_type"))
    effective_mode = args.transcribe_mode or str(config.get("default_mode") or "")
    proxy_requested = provider_id in {"openai-compatible", "custom-proxy"} or effective_mode in PROXY_EXECUTION_MODES
    if not key_present:
        state = "missing-key"
    elif provider_id not in DIRECT_EXECUTION_PROVIDERS and not proxy_requested:
        state = "requires-proxy"
    elif capability == "unsupported-direct" and not proxy_requested:
        state = "requires-proxy"
    elif proxy_requested and provider_id not in DIRECT_EXECUTION_PROVIDERS and not endpoint:
        state = "needs-endpoint"
    else:
        state = "available"
    return {
        "provider": provider_id,
        "display_name": config["display_name"],
        "capability_type": capability,
        "default_mode": config["default_mode"],
        "auth_env": auth_env,
        "key_present": key_present,
        "base_url_label": endpoint_label(provider_base_url(provider_id, args)),
        "endpoint_label": endpoint_label(endpoint),
        "state": state,
        "uploads_media": bool(config.get("uploads_media")),
        "requires_media_download": bool(config.get("requires_media_download")),
        "paid_or_quota_risk": bool(config.get("paid_or_quota_risk")),
        "region_risk": config.get("region_risk"),
        "limitations": config.get("limitations"),
    }


def provider_options(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [provider_option_status(provider_id, args) for provider_id in PROVIDER_REGISTRY]


def recommended_provider_id(args: argparse.Namespace) -> str | None:
    for provider_id in ("openai", "moonshot", "minimax"):
        status = provider_option_status(provider_id, args)
        if status["state"] == "available":
            return provider_id
    for status in provider_options(args):
        if status["state"] == "available":
            return str(status["provider"])
    return None


def provider_checkpoint_plan(args: argparse.Namespace, reason: str) -> dict[str, Any]:
    recommendation = recommended_provider_id(args)
    return {
        "status": "requires_confirmation",
        "reason": reason,
        "recommended_provider": recommendation,
        "available_providers": provider_options(args),
        "default_provider_path": str(provider_default_path()),
        "action": (
            "首次无人工字幕且没有默认 provider 时，必须选择默认 provider/API 凭据；"
            "请传入 --transcribe-provider/--transcribe-mode，并用 --save-default-provider 保存默认值。"
        ),
        "degrade_options": [
            "提供人工字幕文件",
            "提供已转写文本",
            "改用本地 ASR 或自定义代理",
            "只保存 metadata 并跳过该视频",
        ],
    }


def resolve_provider_choice(args: argparse.Namespace, *, allow_default: bool = True) -> dict[str, Any]:
    mapped_provider: str | None = None
    mapped_mode: str | None = None
    if args.transcribe_backend != "auto":
        mapped_provider, mapped_mode = BACKEND_PROVIDER_MAP[args.transcribe_backend]
    if mapped_provider and args.transcribe_provider and args.transcribe_provider != mapped_provider:
        raise ProviderConfigurationError(
            f"--transcribe-backend {args.transcribe_backend} maps to provider {mapped_provider}, "
            f"but --transcribe-provider {args.transcribe_provider} was also provided."
        )
    if mapped_mode and args.transcribe_mode and args.transcribe_mode != mapped_mode:
        raise ProviderConfigurationError(
            f"--transcribe-backend {args.transcribe_backend} maps to mode {mapped_mode}, "
            f"but --transcribe-mode {args.transcribe_mode} was also provided."
        )

    default_data = None if args.ignore_default_provider or not allow_default else load_default_provider()
    selection_source = "cli-explicit" if explicit_provider_requested(args) else "saved-default" if default_data else ""
    if explicit_provider_requested(args):
        provider_id = args.transcribe_provider or mapped_provider or ("custom-proxy" if args.transcribe_endpoint else "openai-compatible")
        mode = args.transcribe_mode or mapped_mode or str(PROVIDER_REGISTRY[provider_id]["default_mode"])
    elif default_data:
        provider_id = str(default_data["default_provider"])
        mode = str(default_data.get("default_mode") or PROVIDER_REGISTRY[provider_id]["default_mode"])
    else:
        raise ProviderSelectionRequired(
            "No human subtitles are available and no transcription provider/default provider was selected.",
            provider_checkpoint_plan(args, "no-human-subtitle-without-provider"),
        )

    if provider_id not in PROVIDER_REGISTRY:
        raise ProviderBlocked(f"Unknown transcription provider: {provider_id}", {"provider": provider_id})
    config = PROVIDER_REGISTRY[provider_id]
    auth_env = args.transcribe_auth_env or str((default_data or {}).get("auth_env") or config.get("auth_env") or "")
    model = provider_model(provider_id, args, default_data)
    endpoint = provider_endpoint(provider_id, args, default_data)
    capability_type = str(config.get("capability_type"))
    proxy_used = provider_id in {"openai-compatible", "custom-proxy"} or mode in PROXY_EXECUTION_MODES
    warnings: list[str] = []
    if capability_type in {"video-understanding", "audio-to-llm"}:
        warnings.append("该 provider 使用理解式转写，不是专用逐字 ASR。")
    if provider_id not in DIRECT_EXECUTION_PROVIDERS and not proxy_used:
        warnings.append("该 provider 首版需要代理或自定义 endpoint 执行。")
    if capability_type == "unsupported-direct" and not proxy_used:
        warnings.append("该 provider 当前未声明可直接处理音频/视频，需要代理或自定义 endpoint。")
    choice = {
        "provider": provider_id,
        "display_name": config["display_name"],
        "mode": mode,
        "model": model,
        "model_env": config.get("default_model_env"),
        "auth_env": auth_env,
        "auth_present": bool(env_value(auth_env)),
        "base_url_label": endpoint_label(provider_base_url(provider_id, args, default_data)),
        "endpoint": endpoint,
        "endpoint_label": endpoint_label(endpoint),
        "provider_capability_type": capability_type,
        "provider_selection_source": selection_source or "env-recommendation",
        "default_provider_used": bool(default_data and not explicit_provider_requested(args)),
        "default_credential_label": auth_env or None,
        "media_downloaded": bool(config.get("requires_media_download")),
        "media_uploaded": bool(config.get("uploads_media")),
        "proxy_used": proxy_used,
        "selection_warnings": warnings,
        "status": "ok",
    }
    def raise_blocked(message: str, status: str = "blocked") -> None:
        choice["status"] = status
        if choice["default_provider_used"]:
            choice["provider_checkpoint"] = provider_checkpoint_plan(args, "saved-default-provider-invalid")
        raise ProviderBlocked(message, choice)

    if not choice["auth_present"]:
        raise_blocked(f"{auth_env or provider_id + ' API key'} is required for provider {provider_id}.")
    if proxy_used and not endpoint:
        raise_blocked(f"Provider {provider_id} requires --transcribe-endpoint or a configured endpoint env var.")
    if provider_id not in DIRECT_EXECUTION_PROVIDERS and not proxy_used:
        raise_blocked(f"Provider {provider_id} requires proxy mode or a compatible transcription endpoint.", "requires-proxy")
    if capability_type == "unsupported-direct" and not proxy_used:
        raise_blocked(f"Provider {provider_id} requires proxy mode or a compatible transcription endpoint.", "requires-proxy")
    return choice


def provider_metadata_fields(choice: dict[str, Any]) -> dict[str, Any]:
    return {
        "transcribe_provider": choice.get("provider"),
        "transcribe_mode": choice.get("mode"),
        "transcribe_model": choice.get("model"),
        "provider_capability_type": choice.get("provider_capability_type"),
        "provider_selection_source": choice.get("provider_selection_source"),
        "default_provider_used": choice.get("default_provider_used", False),
        "default_credential_label": choice.get("default_credential_label"),
        "auth_env": choice.get("auth_env"),
        "media_downloaded": choice.get("media_downloaded", False),
        "media_uploaded": choice.get("media_uploaded", False),
        "endpoint_label": choice.get("endpoint_label"),
        "proxy_used": choice.get("proxy_used", False),
        "selection_warnings": choice.get("selection_warnings", []),
    }


def public_provider_choice(choice: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": choice.get("provider"),
        "display_name": choice.get("display_name"),
        "mode": choice.get("mode"),
        "model": choice.get("model"),
        "capability_type": choice.get("provider_capability_type"),
        "selection_source": choice.get("provider_selection_source"),
        "default_provider_used": choice.get("default_provider_used", False),
        "default_credential_label": choice.get("default_credential_label"),
        "auth_env": choice.get("auth_env"),
        "base_url_label": choice.get("base_url_label"),
        "endpoint_label": choice.get("endpoint_label"),
        "media_downloaded": choice.get("media_downloaded", False),
        "media_uploaded": choice.get("media_uploaded", False),
        "proxy_used": choice.get("proxy_used", False),
        "selection_warnings": choice.get("selection_warnings", []),
        "status": choice.get("status", "ok"),
        "provider_checkpoint": choice.get("provider_checkpoint"),
    }


def normalize_artifact(value: str) -> str:
    return ARTIFACT_ALIASES[value]


def unique_ordered(values: list[str] | tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def requested_artifacts(args: argparse.Namespace) -> list[str]:
    if args.artifact:
        return unique_ordered([normalize_artifact(value) for value in args.artifact])
    return list(OUTPUT_PROFILE_ARTIFACTS[args.output_profile])


def expand_artifacts_for_generation(artifacts: list[str]) -> list[str]:
    expanded = list(artifacts)
    changed = True
    while changed:
        changed = False
        for artifact in list(expanded):
            for dep in ARTIFACT_DEPENDENCIES.get(artifact, ()):
                if dep not in expanded:
                    expanded.insert(0, dep)
                    changed = True
    return unique_ordered(expanded)


def generation_artifacts_for_request(requested: list[str], primary_artifact: str | None) -> list[str]:
    if not requested:
        return [primary_artifact] if primary_artifact else []

    expanded = expand_artifacts_for_generation(requested)
    needs_transcript_source = any(
        artifact in {"speech_transcript", "chapter_handout", "html_render"}
        for artifact in expanded
    )
    if primary_artifact in {"raw_asr", "speech_transcript"} and needs_transcript_source:
        expanded.insert(0, primary_artifact)
    return unique_ordered(expanded)


def raw_asr_only_blocked(requested: list[str], primary_artifact: str) -> bool:
    return requested == ["raw_asr"] and primary_artifact != "raw_asr"


def primary_artifact_for_choice(choice: dict[str, Any] | None = None, *, subtitle: bool = False) -> str:
    if subtitle:
        return "raw_asr"
    if not choice:
        return "raw_asr"
    capability = str(choice.get("provider_capability_type") or "")
    provider = str(choice.get("provider") or "")
    mode = str(choice.get("mode") or "")
    if capability == "video-understanding" or provider == "moonshot" or mode == "video-understanding":
        return "speech_transcript"
    if provider in ASR_CAPABLE_PROVIDERS or mode in ASR_CAPABLE_MODES:
        return "raw_asr"
    return "speech_transcript"


def artifact_allowed_transform(artifact_type: str) -> str:
    return {
        "raw_asr": "none_or_timestamp_only",
        "speech_transcript": "light_cleanup_no_reorder",
        "chapter_handout": "summarize_restructure_add_tables",
        "html_render": "html_render_from_markdown",
    }[artifact_type]


def artifact_path(video_dir: Path, video: dict[str, Any], artifact_type: str) -> Path:
    if artifact_type == "raw_asr":
        return video_dir / "original.asr.md"
    if artifact_type == "speech_transcript":
        return video_dir / "speech.md"
    if artifact_type == "chapter_handout":
        chapter_dir = video_dir / "chapters"
        return chapter_dir / f"ch01-{safe_path_part(video.get('title') or 'transcript')}.md"
    if artifact_type == "html_render":
        return artifact_path(video_dir, video, "chapter_handout").with_suffix(".html")
    raise ValueError(f"Unknown artifact type: {artifact_type}")


def artifact_record(
    artifact_type: str,
    path: Path | str | None,
    *,
    source_artifact: str | None,
    source_type: str | None,
    provider: str | None,
    model: str | None,
    derivation_stage: str,
    status: str = "generated",
    reason: str | None = None,
) -> dict[str, Any]:
    record = {
        "artifact_type": artifact_type,
        "path": str(path) if path else None,
        "source_artifact": source_artifact,
        "source_type": source_type,
        "provider": provider,
        "model": model,
        "allowed_transform": artifact_allowed_transform(artifact_type),
        "derivation_stage": derivation_stage,
        "status": status,
    }
    if reason:
        record["reason"] = reason
    return record


def artifact_status_exists(metadata: dict[str, Any], artifact_type: str) -> bool:
    return any(
        item.get("artifact_type") == artifact_type
        for item in metadata.get("artifacts", [])
    )


def generated_artifact_status_exists(metadata: dict[str, Any], artifact_type: str) -> bool:
    return any(
        item.get("artifact_type") == artifact_type and item.get("status") == "generated"
        for item in metadata.get("artifacts", [])
    )


def record_missing_artifacts(
    metadata: dict[str, Any],
    video_dir: Path,
    video: dict[str, Any],
    artifacts: list[str],
    *,
    status: str,
    reason: str,
    source_artifact: str | None = None,
    source_type: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    for artifact_type in expand_artifacts_for_generation(artifacts):
        if artifact_status_exists(metadata, artifact_type):
            continue
        metadata.setdefault("artifacts", []).append(
            artifact_record(
                artifact_type,
                artifact_path(video_dir, video, artifact_type),
                source_artifact=source_artifact,
                source_type=source_type,
                provider=provider,
                model=model,
                derivation_stage=status,
                status=status,
                reason=reason,
            )
        )


def legacy_original_artifact_type(metadata: dict[str, Any]) -> str:
    source = str(metadata.get("source") or "").lower()
    provider = str(metadata.get("transcribe_provider") or "").lower()
    mode = str(metadata.get("transcribe_mode") or "").lower()
    if "kimi" in source or "moonshot" in source or provider == "moonshot" or mode == "video-understanding":
        return "speech_transcript"
    return "raw_asr"


def ensure_existing_artifact_records(metadata: dict[str, Any], video_dir: Path, video: dict[str, Any]) -> None:
    metadata.setdefault("artifacts", [])
    primary_artifact = metadata.get("primary_artifact") or legacy_original_artifact_type(metadata)
    original_path = video_dir / "original.md"
    if primary_artifact in ARTIFACT_ALIASES.values() and original_path.exists():
        target_path = artifact_path(video_dir, video, str(primary_artifact))
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original_path, target_path)
        if not generated_artifact_status_exists(metadata, str(primary_artifact)):
            metadata["artifacts"].append(
                artifact_record(
                    str(primary_artifact),
                    target_path,
                    source_artifact=None,
                    source_type=str(metadata.get("transcribe_mode") or metadata.get("source") or "existing-output"),
                    provider=str(metadata.get("transcribe_provider") or metadata.get("source") or "existing-output"),
                    model=metadata.get("transcribe_model") or metadata.get("kimi_model") or metadata.get("minimax_model"),
                    derivation_stage="existing",
                )
            )
        metadata["primary_artifact"] = str(primary_artifact)
        metadata["original_mirrors_artifact"] = str(primary_artifact)

    for artifact_type in ("raw_asr", "speech_transcript", "chapter_handout", "html_render"):
        path = artifact_path(video_dir, video, artifact_type)
        if not path.exists() or generated_artifact_status_exists(metadata, artifact_type):
            continue
        metadata["artifacts"].append(
            artifact_record(
                artifact_type,
                path,
                source_artifact=None,
                source_type="existing-output",
                provider="existing-output",
                model=None,
                derivation_stage="existing",
            )
        )


def blocked_status(choice: dict[str, Any]) -> str:
    status = str(choice.get("status") or "")
    return status if status and status != "ok" else "blocked"


def artifact_path_exists(video_dir: Path, video: dict[str, Any], metadata: dict[str, Any], artifact_type: str) -> bool:
    for item in metadata.get("artifacts", []):
        if item.get("artifact_type") != artifact_type or item.get("status", "generated") != "generated":
            continue
        path = item.get("path")
        if path and Path(path).exists():
            return True
    return artifact_path(video_dir, video, artifact_type).exists()


def existing_success_satisfies_request(
    video_dir: Path,
    video: dict[str, Any],
    metadata: dict[str, Any],
    args: argparse.Namespace,
) -> bool:
    requested = requested_artifacts(args)
    if not requested:
        return True
    return all(artifact_path_exists(video_dir, video, metadata, artifact_type) for artifact_type in requested)


def artifact_plan_for_video(
    video: dict[str, Any],
    output_root: Path,
    args: argparse.Namespace,
    primary_artifact: str | None = None,
    provider_choice: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    video_dir = video_output_dir(video, output_root)
    requested = requested_artifacts(args)
    artifacts = generation_artifacts_for_request(requested, primary_artifact)
    if not artifacts:
        artifacts = ["raw_asr"] if choose_original_subtitle(video) else ["provider_primary"]
    plan: list[dict[str, Any]] = []
    for artifact in artifacts:
        if artifact == "provider_primary":
            plan.append({"artifact_type": "provider_primary", "path": None, "status": "depends-on-provider"})
            continue
        status = "planned"
        derivation_stage = "derived"
        source_artifact = None
        source_type = None
        provider = provider_choice.get("provider") if provider_choice else None
        model = provider_choice.get("model") if provider_choice else None
        reason = None
        if artifact == primary_artifact:
            derivation_stage = "primary"
            source_type = provider_choice.get("mode") if provider_choice else "human_subtitle"
        elif artifact == "raw_asr" and primary_artifact and primary_artifact != "raw_asr":
            status = "blocked"
            derivation_stage = "blocked"
            source_artifact = primary_artifact
            source_type = provider_choice.get("mode") if provider_choice else None
            reason = "Selected provider/output is not strict ASR; use an ASR-capable provider for raw_asr."
        elif artifact == "speech_transcript":
            source_artifact = "raw_asr" if "raw_asr" in artifacts else primary_artifact
            source_type = source_artifact
            provider = "local-cleanup" if source_artifact == "raw_asr" else provider
            model = None if source_artifact == "raw_asr" else model
        elif artifact == "chapter_handout":
            source_artifact = "speech_transcript" if "speech_transcript" in artifacts else "raw_asr"
            source_type = source_artifact
            provider = "moonshot-or-local-structured-fallback"
            model = provider_choice.get("model") if provider_choice and provider_choice.get("provider") == "moonshot" else None
        elif artifact == "html_render":
            source_artifact = "chapter_handout"
            source_type = "chapter_handout"
            provider = "local-html-render"
            model = None
        item = {
            "artifact_type": artifact,
            "path": str(artifact_path(video_dir, video, artifact)),
            "source_artifact": source_artifact,
            "source_type": source_type,
            "provider": provider,
            "model": model,
            "allowed_transform": artifact_allowed_transform(artifact),
            "derivation_stage": derivation_stage,
            "status": status,
        }
        if provider_choice:
            item["provider_capability_type"] = provider_choice.get("provider_capability_type")
        if reason:
            item["reason"] = reason
        plan.append(
            item
        )
    return plan


def write_artifact_file(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def first_artifact_path(metadata: dict[str, Any], artifact_type: str) -> str | None:
    for artifact in metadata.get("artifacts", []):
        if artifact.get("artifact_type") == artifact_type and artifact.get("status") == "generated":
            return artifact.get("path")
    return None


def chapter_title(video: dict[str, Any]) -> str:
    title = str(video.get("title") or "视频转写").strip()
    short = title
    for sep in ("：", ":", "-", "——"):
        if sep in short:
            short = short.split(sep, 1)[-1].strip() or short
    return short[:60] or "视频转写"


def plain_transcript_body(markdown_text: str) -> str:
    lines = []
    in_transcript = False
    for line in markdown_text.splitlines():
        if line.strip() == "## Transcript":
            in_transcript = True
            continue
        if in_transcript:
            lines.append(line)
    return "\n".join(lines).strip() or markdown_text.strip()


def generate_speech_from_raw(raw_markdown: str, video: dict[str, Any]) -> str:
    body = plain_transcript_body(raw_markdown)
    return markdown_document(video, body, source="light cleanup from raw ASR", language=None)


def generate_chapter_with_kimi(source_markdown: str, video: dict[str, Any], args: argparse.Namespace) -> str | None:
    if not os.environ.get("MOONSHOT_API_KEY"):
        return None
    try:
        client = kimi_client()
        source_body = source_markdown[:45000]
        prompt = (
            "请基于下面的转写稿生成中文章节讲义。要求：\n"
            "1. 不冒充逐字稿，不新增视频没有表达的观点。\n"
            "2. 保留讲述顺序，但允许章节化、提炼概念、添加小结和简单表格。\n"
            "3. 文件开头使用一级标题，随后写“视频信息”和“第一章”。\n"
            "4. 输出 Markdown，不要输出解释说明。\n\n"
            f"视频标题：{video.get('title') or '未命名视频'}\n\n"
            f"转写稿：\n{source_body}"
        )
        response = client.chat.completions.create(
            model=args.kimi_model,
            messages=[
                {"role": "system", "content": "你把转写稿整理成忠实、清晰的中文学习讲义。"},
                {"role": "user", "content": prompt},
            ],
            extra_body={"thinking": {"type": "disabled"}},
            max_tokens=32768,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001
        print(f"Kimi chapter generation failed, using local fallback: {exc}", file=sys.stderr)
        return None


def generate_chapter_fallback(source_markdown: str, video: dict[str, Any]) -> str:
    body = plain_transcript_body(source_markdown)
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", body) if part.strip()]
    excerpt = "\n\n".join(paragraphs[:12])
    title = video.get("title") or "视频转写"
    return "\n".join(
        [
            f"# {title}",
            "",
            "**视频信息**",
            f"- 标题：{title}",
            f"- 链接：{video.get('_download_url') or video.get('webpage_url') or ''}",
            "",
            "---",
            "",
            f"## 第一章：{chapter_title(video)}",
            "",
            excerpt,
            "",
            "---",
            "",
            "## 本章小结",
            "",
            "- 本文件是由转写稿派生的章节讲义，不是原始逐字 ASR。",
            "- 讲义保留原始讲述顺序，但允许概念提炼和结构化排版。",
            "",
        ]
    )


def render_markdown_html(markdown_text: str, title: str) -> str:
    lines = [
        "<!doctype html>",
        "<html lang=\"zh-CN\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        f"  <title>{html.escape(title)}</title>",
        "  <style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.7;max-width:920px;margin:40px auto;padding:0 24px;color:#202124} h1,h2,h3{line-height:1.25} blockquote{border-left:4px solid #8aa;padding-left:14px;color:#455} code{background:#f4f4f4;padding:2px 4px} table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:6px}</style>",
        "</head>",
        "<body>",
    ]
    in_list = False
    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if not line:
            if in_list:
                lines.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{html.escape(line[2:].strip())}</li>")
        elif line == "---":
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append("<hr>")
        elif line.startswith("> "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<blockquote>{html.escape(line[2:].strip())}</blockquote>")
        else:
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        lines.append("</ul>")
    lines.extend(["</body>", "</html>", ""])
    return "\n".join(lines)


def output_paths_for_video(video: dict[str, Any], output_root: Path) -> dict[str, str]:
    video_dir = video_output_dir(video, output_root)
    return {
        "output_dir": str(video_dir),
        "work_dir": str(video_dir / "_work"),
        "original_path": str(video_dir / "original.md"),
        "original_asr_path": str(video_dir / "original.asr.md"),
        "speech_path": str(video_dir / "speech.md"),
        "chapters_dir": str(video_dir / "chapters"),
        "zh_path": str(video_dir / "zh.md"),
        "metadata_path": str(video_dir / "metadata.json"),
    }


def make_video_summary(video: dict[str, Any], output_root: Path) -> dict[str, Any]:
    paths = output_paths_for_video(video, output_root)
    summary = {
        "title": video.get("title"),
        "id": video.get("id"),
        "url": redact_url(str(video.get("_download_url") or video.get("webpage_url") or "")),
        "status": "pending",
        "backend": None,
        "transcribe_provider": None,
        "transcribe_mode": None,
        "provider_selection_source": None,
        "default_provider_used": False,
        "source": None,
        "output_paths": paths,
        "artifact_plan": [],
        "artifacts": [],
        "failures": [],
        "uncertain": [],
    }
    summary.update(public_api_summary_fields(video))
    return summary


def summarize_outputs(video_dir: Path) -> list[str]:
    outputs = [
        video_dir / "original.md",
        video_dir / "original.asr.md",
        video_dir / "speech.md",
        video_dir / "zh.md",
        video_dir / "metadata.json",
    ]
    outputs.extend(sorted((video_dir / "chapters").glob("*.*")) if (video_dir / "chapters").exists() else [])
    return [str(path) for path in outputs if path.exists()]


def existing_success(video_dir: Path) -> dict[str, Any] | None:
    metadata_path = video_dir / "metadata.json"
    original_path = video_dir / "original.md"
    if not metadata_path.exists() or not original_path.exists():
        return None
    try:
        if not original_path.read_text(encoding="utf-8").strip():
            return None
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if metadata.get("status") in {"failed", "blocked"} or metadata.get("error"):
        return None
    return metadata


def make_run_summary(args: argparse.Namespace, output_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "tool": "video-transcript",
        "status": "pending",
        "started_at": utc_now(),
        "finished_at": None,
        "mode": "doctor" if args.doctor else "dry-run" if args.dry_run else "run",
        "argv": sanitize_argv(sys.argv[1:]),
        "cwd": str(Path.cwd()),
        "requested_backend": args.transcribe_backend,
        "requested_provider": args.transcribe_provider,
        "requested_mode": args.transcribe_mode,
        "requested_output_profile": args.output_profile,
        "requested_artifacts": requested_artifacts(args),
        "backend": None,
        "transcribe_provider": None,
        "transcribe_mode": None,
        "default_provider_path": str(provider_default_path()),
        "default_provider_used": False,
        "output_root": str(output_root),
        "force": bool(args.force),
        "public_api_fallback": {
            "enabled": not public_api_fallback_disabled(args),
            "disable_env": "VIDEO_SKILL_PUBLIC_API_FALLBACK",
        },
        "items": [],
        "output_paths": [],
        "failures": [],
        "uncertain": [],
    }


def write_summary_files(output_root: Path, summary: dict[str, Any]) -> None:
    summary["finished_at"] = utc_now()
    items = summary.get("items", [])
    summary["output_paths"] = [
        path
        for item in items
        for path in item.get("outputs_written", [])
    ]
    summary["failures"] = [
        failure
        for item in items
        for failure in item.get("failures", [])
    ] + summary.get("failures", [])
    summary["uncertain"] = [
        uncertain
        for item in items
        for uncertain in item.get("uncertain", [])
    ] + summary.get("uncertain", [])
    if summary["mode"] == "doctor":
        summary["status"] = "blocked" if summary["failures"] else "ok"
    elif summary["mode"] == "dry-run":
        summary["status"] = "partial_failure" if summary["failures"] else "dry_run"
    else:
        summary["status"] = "partial_failure" if summary["failures"] else "success"
    run_summary_path = output_root / "run-summary.json"
    transcript_summary_path = output_root / "transcript-summary.json"
    run_summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    transcript_summary = {
        "schema_version": 1,
        "generated_at": summary["finished_at"],
        "mode": summary["mode"],
        "cwd": summary["cwd"],
        "requested_backend": summary["requested_backend"],
        "requested_provider": summary.get("requested_provider"),
        "requested_mode": summary.get("requested_mode"),
        "requested_output_profile": summary.get("requested_output_profile"),
        "requested_artifacts": summary.get("requested_artifacts", []),
        "backend": summary.get("backend"),
        "transcribe_provider": summary.get("transcribe_provider"),
        "transcribe_mode": summary.get("transcribe_mode"),
        "default_provider_used": summary.get("default_provider_used", False),
        "output_root": summary["output_root"],
        "items": items,
        "output_paths": summary["output_paths"],
        "failures": summary["failures"],
        "uncertain": summary["uncertain"],
    }
    transcript_summary_path.write_text(
        json.dumps(transcript_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def check_python_module(name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(name)
    return {"name": name, "ok": spec is not None, "detail": "importable" if spec else "missing"}


def doctor_report(args: argparse.Namespace, output_root: Path) -> tuple[int, dict[str, Any]]:
    packages = [check_python_module(name) for name in ("yt_dlp", "openai", "requests")]
    commands = [
        {"name": name, "ok": shutil.which(name) is not None, "detail": "found" if shutil.which(name) else "missing"}
        for name in ("yt-dlp", "ffmpeg", "ffprobe")
    ]
    env_names = (
        "OPENAI_API_KEY",
        "MOONSHOT_API_KEY",
        "MINIMAX_API_KEY",
        "MINIMAX_BASE_URL",
        "MINIMAX_API_BASE",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "GLM_API_KEY",
        "GLM_BASE_URL",
        "GEMINI_API_KEY",
        "GEMINI_BASE_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "OPENAI_COMPATIBLE_API_KEY",
        "OPENAI_COMPATIBLE_BASE_URL",
        "OPENAI_COMPATIBLE_TRANSCRIBE_URL",
        "CUSTOM_TRANSCRIBE_API_KEY",
        "CUSTOM_TRANSCRIBE_BASE_URL",
        "CUSTOM_TRANSCRIBE_URL",
    )
    env = [{"name": name, "present": bool(os.environ.get(name))} for name in env_names]
    default_data = load_default_provider()
    checks = {
        "python": sys.version.split()[0],
        "executable": str(Path(sys.executable).resolve()),
        "packages": packages,
        "commands": commands,
        "environment": env,
        "providers": provider_options(args),
        "default_provider": {
            "path": str(provider_default_path()),
            "present": bool(default_data),
            "provider": default_data.get("default_provider") if default_data else None,
            "mode": default_data.get("default_mode") if default_data else None,
            "auth_env": default_data.get("auth_env") if default_data else None,
            "endpoint_label": default_data.get("endpoint_label") if default_data else None,
        },
        "public_api_fallback": public_api_doctor(public_api_fallback_disabled(args)),
        "artifact_layers": {
            "requested_output_profile": args.output_profile,
            "requested_artifacts": requested_artifacts(args),
            "profiles": OUTPUT_PROFILE_ARTIFACTS,
        },
    }
    missing = [
        f"package:{item['name']}" for item in packages if not item["ok"]
    ] + [
        f"command:{item['name']}" for item in commands if not item["ok"]
    ]
    status = 0 if not missing else 1
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return status, {
        "title": "doctor",
        "id": None,
        "url": None,
        "status": "success" if status == 0 else "failed",
        "backend": args.transcribe_backend,
        "transcribe_provider": args.transcribe_provider,
        "transcribe_mode": args.transcribe_mode,
        "default_provider_used": False,
        "source": "doctor",
        "output_paths": {"output_root": str(output_root)},
        "outputs_written": [],
        "checks": checks,
        "failures": missing,
        "uncertain": [],
    }


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
        if public_api_fallback_disabled(args):
            return None
        info = fetch_public_api_info(url, disabled=False, stages=PUBLIC_API_STAGES)
        if info:
            print(f"Using public API fallback for metadata: {info.get('extractor_key') or adapter_for_url(url)['id']}")
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


def download_subtitle(video: dict[str, Any], url: str, lang: str, work_dir: Path, args: argparse.Namespace) -> Path | None:
    subtitle_dir = work_dir / "subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    if lang in public_subtitle_languages(video):
        result = download_public_subtitle(
            video,
            lang,
            subtitle_dir,
            keep_timestamps=args.timestamps,
            filename_stem=video_identifier(video),
        )
        if result.get("status") == "downloaded" and result.get("text_path"):
            return Path(str(result["text_path"]))
        print(result.get("error") or f"Failed to download public API subtitle {lang}", file=sys.stderr)
        return None
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


def download_audio(url: str, work_dir: Path, args: argparse.Namespace, video: dict[str, Any] | None = None) -> Path | None:
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
        if video and not public_api_fallback_disabled(args):
            fallback = download_public_media(
                video,
                audio_dir,
                audio_only=True,
                filename_stem=video_identifier(video),
            )
            for warning in fallback.get("warnings", []):
                print(warning, file=sys.stderr)
            paths = fallback.get("paths") or []
            if fallback.get("status") == "downloaded" and paths:
                return Path(str(paths[0]))
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


def transcribe_audio_with_proxy(parts: list[Path], args: argparse.Namespace, choice: dict[str, Any]) -> str:
    import requests

    api_key = env_value(str(choice.get("auth_env") or ""))
    if not api_key:
        raise RuntimeError(f"{choice.get('auth_env') or 'Provider API key'} is required for proxy transcription.")
    endpoint = choice.get("endpoint")
    if not endpoint:
        raise RuntimeError("A transcription endpoint is required for proxy transcription.")

    blocks: list[str] = []
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": choice.get("model") or args.transcribe_model,
        "response_format": "json",
        "prompt": args.transcription_prompt,
    }
    if args.transcribe_language:
        data["language"] = args.transcribe_language

    for index, part in enumerate(parts, start=1):
        print(f"Transcribing audio part {index}/{len(parts)} with {choice['provider']} proxy: {part.name}")
        with part.open("rb") as audio_file:
            response = requests.post(
                str(endpoint),
                headers=headers,
                data=data,
                files={"file": (part.name, audio_file, "application/octet-stream")},
                timeout=300,
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"{choice['provider']} proxy transcription failed for {part.name}: "
                f"HTTP {response.status_code} {response.text[:1000]}"
            )
        try:
            payload: Any = response.json()
        except ValueError:
            payload = response.text
        text = extract_transcription_text(payload).strip()
        if not text:
            raise RuntimeError(f"{choice['provider']} proxy returned empty transcript for {part.name}.")
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


def generate_requested_artifacts(
    metadata: dict[str, Any],
    video_dir: Path,
    video: dict[str, Any],
    args: argparse.Namespace,
    *,
    primary_artifact_type: str,
    primary_provider: str | None,
    primary_model: str | None,
    primary_source_type: str | None,
) -> None:
    requested = requested_artifacts(args)
    if not requested:
        return

    for artifact_type in generation_artifacts_for_request(requested, primary_artifact_type):
        if generated_artifact_status_exists(metadata, artifact_type):
            continue
        if artifact_type == "raw_asr":
            if primary_artifact_type == "raw_asr":
                continue
            metadata["artifacts"].append(
                artifact_record(
                    "raw_asr",
                    artifact_path(video_dir, video, "raw_asr"),
                    source_artifact=primary_artifact_type,
                    source_type=primary_source_type,
                    provider=primary_provider,
                    model=primary_model,
                    derivation_stage="blocked",
                    status="blocked",
                    reason="Selected provider/output is not strict ASR; use an ASR-capable provider for raw_asr.",
                )
            )
            metadata["selection_warnings"].append("raw_asr was requested but the selected provider/output is not strict ASR.")
        elif artifact_type == "speech_transcript":
            source_path = first_artifact_path(metadata, "raw_asr")
            if source_path:
                raw_markdown = Path(source_path).read_text(encoding="utf-8")
                speech_markdown = generate_speech_from_raw(raw_markdown, video)
                speech_path = write_artifact_file(artifact_path(video_dir, video, "speech_transcript"), speech_markdown)
                metadata["artifacts"].append(
                    artifact_record(
                        "speech_transcript",
                        speech_path,
                        source_artifact="raw_asr",
                        source_type="raw_asr",
                        provider="local-cleanup",
                        model=None,
                        derivation_stage="derived",
                    )
                )
            elif primary_artifact_type == "speech_transcript":
                continue
            else:
                metadata["artifacts"].append(
                    artifact_record(
                        "speech_transcript",
                        artifact_path(video_dir, video, "speech_transcript"),
                        source_artifact=primary_artifact_type,
                        source_type=primary_source_type,
                        provider=primary_provider,
                        model=primary_model,
                        derivation_stage="skipped",
                        status="skipped",
                        reason="No raw or speech source artifact is available.",
                    )
                )
        elif artifact_type == "chapter_handout":
            source_type = "speech_transcript" if first_artifact_path(metadata, "speech_transcript") else "raw_asr"
            source_path = first_artifact_path(metadata, source_type)
            if not source_path:
                metadata["artifacts"].append(
                    artifact_record(
                        "chapter_handout",
                        artifact_path(video_dir, video, "chapter_handout"),
                        source_artifact=None,
                        source_type=None,
                        provider=None,
                        model=None,
                        derivation_stage="skipped",
                        status="skipped",
                        reason="No transcript source is available for chapter handout.",
                    )
                )
                continue
            source_markdown = Path(source_path).read_text(encoding="utf-8")
            chapter_provider = "local-structured-fallback"
            chapter_model = None
            chapter_markdown = None
            if os.environ.get("MOONSHOT_API_KEY"):
                chapter_markdown = generate_chapter_with_kimi(source_markdown, video, args)
                if chapter_markdown:
                    chapter_provider = "moonshot"
                    chapter_model = args.kimi_model
            if not chapter_markdown:
                chapter_markdown = generate_chapter_fallback(source_markdown, video)
            chapter_path = write_artifact_file(artifact_path(video_dir, video, "chapter_handout"), chapter_markdown)
            metadata["artifacts"].append(
                artifact_record(
                    "chapter_handout",
                    chapter_path,
                    source_artifact=source_type,
                    source_type=source_type,
                    provider=chapter_provider,
                    model=chapter_model,
                    derivation_stage="derived",
                )
            )
        elif artifact_type == "html_render":
            source_path = first_artifact_path(metadata, "chapter_handout")
            if not source_path:
                metadata["artifacts"].append(
                    artifact_record(
                        "html_render",
                        artifact_path(video_dir, video, "html_render"),
                        source_artifact=None,
                        source_type=None,
                        provider=None,
                        model=None,
                        derivation_stage="skipped",
                        status="skipped",
                        reason="No chapter handout is available for HTML render.",
                    )
                )
                continue
            chapter_markdown = Path(source_path).read_text(encoding="utf-8")
            html_path = write_artifact_file(
                artifact_path(video_dir, video, "html_render"),
                render_markdown_html(chapter_markdown, str(video.get("title") or "视频讲义")),
            )
            metadata["artifacts"].append(
                artifact_record(
                    "html_render",
                    html_path,
                    source_artifact="chapter_handout",
                    source_type="chapter_handout",
                    provider="local-html-render",
                    model=None,
                    derivation_stage="derived",
                )
            )


def dry_run_video(video: dict[str, Any], output_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    summary = make_video_summary(video, output_root)
    original_lang = choose_original_subtitle(video)
    zh_lang = choose_zh_subtitle(video)
    if original_lang:
        summary["artifact_plan"] = artifact_plan_for_video(video, output_root, args, "raw_asr")
        summary["status"] = "would_process"
        summary["backend"] = "subtitle"
        subtitle_source = "public_api_subtitle" if original_lang in public_subtitle_languages(video) else "human_subtitle"
        summary["source"] = f"{subtitle_source} ({original_lang})"
        summary["original_language"] = original_lang
        summary["zh_language"] = zh_lang
        summary["uncertain"].append("dry-run did not download subtitle files or verify transcript text")
        return summary

    try:
        choice = resolve_provider_choice(args)
        primary_artifact = primary_artifact_for_choice(choice)
        summary["artifact_plan"] = artifact_plan_for_video(video, output_root, args, primary_artifact, choice)
        summary.update(provider_metadata_fields(choice))
        summary["status"] = "blocked" if raw_asr_only_blocked(requested_artifacts(args), primary_artifact) else "would_process"
        summary["backend"] = choice["provider"]
        summary["source"] = f"{choice['provider']}_{choice['mode']}"
        summary["provider_plan"] = public_provider_choice(choice)
        if summary["status"] == "blocked":
            summary["failures"].append("raw_asr was requested but the selected provider/output is not strict ASR.")
        summary["uncertain"].append("dry-run did not download media, upload API payloads, or transcribe")
    except ProviderSelectionRequired as exc:
        summary["status"] = "requires_confirmation"
        summary["backend"] = args.transcribe_backend
        summary["provider_checkpoint"] = exc.plan
        summary["uncertain"].append(str(exc))
    except ProviderBlocked as exc:
        summary.update(provider_metadata_fields(exc.choice))
        summary["status"] = exc.choice.get("status", "blocked")
        summary["backend"] = exc.choice.get("provider") or args.transcribe_backend
        summary["provider_plan"] = public_provider_choice(exc.choice)
        if exc.choice.get("provider_checkpoint"):
            summary["provider_checkpoint"] = exc.choice["provider_checkpoint"]
        summary["failures"].append(str(exc))
    except ProviderConfigurationError as exc:
        summary["status"] = "blocked"
        summary["backend"] = args.transcribe_backend
        summary["failures"].append(str(exc))
    except Exception as exc:
        summary["status"] = "uncertain"
        summary["backend"] = args.transcribe_backend
        summary["uncertain"].append(str(exc))
    return summary


def process_video(video: dict[str, Any], output_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    summary = make_video_summary(video, output_root)
    url = video.get("_download_url")
    if not url:
        message = f"Skipping item without URL: {video.get('title') or video.get('id')}"
        print(message, file=sys.stderr)
        summary["status"] = "failed"
        summary["failures"].append(message)
        return summary

    video_dir = video_output_dir(video, output_root)
    work_dir = video_dir / "_work"
    video_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    original_path = video_dir / "original.md"
    zh_path = video_dir / "zh.md"
    if not args.force:
        existing = existing_success(video_dir)
        if existing:
            if existing_success_satisfies_request(video_dir, video, existing, args):
                summary["status"] = "skipped"
                summary["source"] = existing.get("source")
                summary["metadata"] = existing
                summary["artifacts"] = existing.get("artifacts", [])
                summary["outputs_written"] = summarize_outputs(video_dir)
                summary["uncertain"].append("Existing successful transcript was reused; use --force to overwrite.")
                if existing.get("needs_zh_translation") and not zh_path.exists():
                    summary["uncertain"].append(f"Chinese translation still needed: {zh_path}")
                return summary

            existing["requested_output_profile"] = args.output_profile
            existing["requested_artifacts"] = requested_artifacts(args)
            existing.setdefault("selection_warnings", [])
            ensure_existing_artifact_records(existing, video_dir, video)
            primary_artifact_type = str(existing.get("primary_artifact") or legacy_original_artifact_type(existing))
            primary_record = next(
                (
                    item
                    for item in existing.get("artifacts", [])
                    if item.get("artifact_type") == primary_artifact_type and item.get("status") == "generated"
                ),
                {},
            )
            generate_requested_artifacts(
                existing,
                video_dir,
                video,
                args,
                primary_artifact_type=primary_artifact_type,
                primary_provider=primary_record.get("provider") or existing.get("transcribe_provider") or existing.get("source"),
                primary_model=primary_record.get("model") or existing.get("transcribe_model"),
                primary_source_type=primary_record.get("source_type") or existing.get("transcribe_mode") or existing.get("source"),
            )
            raw_only_blocked = raw_asr_only_blocked(requested_artifacts(args), primary_artifact_type)
            existing["status"] = "blocked" if raw_only_blocked else "success"
            existing.pop("error", None)
            write_metadata(video_dir, existing)
            if not args.keep_audio:
                shutil.rmtree(work_dir, ignore_errors=True)
            summary["status"] = existing["status"]
            summary["source"] = existing.get("source")
            summary["metadata"] = existing
            summary["artifacts"] = existing.get("artifacts", [])
            summary["outputs_written"] = summarize_outputs(video_dir)
            if raw_only_blocked:
                summary["failures"].append("raw_asr was requested but the existing transcript is not strict ASR.")
            else:
                summary["uncertain"].append("Existing transcript was reused to generate missing requested artifacts.")
            if existing.get("needs_zh_translation") and not zh_path.exists():
                summary["uncertain"].append(f"Chinese translation still needed: {zh_path}")
            return summary

    metadata: dict[str, Any] = {
        "title": video.get("title"),
        "id": video.get("id"),
        "video_id": video.get("id"),
        "url": url,
        "original_path": str(original_path),
        "zh_path": str(zh_path),
        "source": None,
        "original_language": None,
        "needs_zh_translation": False,
        "status": "pending",
        "transcribe_provider": None,
        "transcribe_mode": None,
        "transcribe_model": None,
        "provider_capability_type": None,
        "provider_selection_source": None,
        "default_provider_used": False,
        "default_credential_label": None,
        "auth_env": None,
        "media_downloaded": False,
        "media_uploaded": False,
        "endpoint_label": None,
        "proxy_used": False,
        "selection_warnings": [],
        "requested_output_profile": args.output_profile,
        "requested_artifacts": requested_artifacts(args),
        "artifacts": [],
        "primary_artifact": None,
        "original_mirrors_artifact": None,
    }
    metadata.update(public_api_summary_fields(video))

    try:
        choice: dict[str, Any] | None = None
        primary_artifact_type = "raw_asr"
        primary_markdown = ""
        primary_provider: str | None = None
        primary_model: str | None = None
        primary_source_type: str | None = None
        original_lang = choose_original_subtitle(video)
        zh_lang = choose_zh_subtitle(video)
        if original_lang:
            summary["backend"] = "subtitle"
            subtitle_source = "public_api_subtitle" if original_lang in public_subtitle_languages(video) else "human_subtitle"
            summary["source"] = f"{subtitle_source} ({original_lang})"
            subtitle_file = download_subtitle(video, str(url), original_lang, work_dir, args)
            if not subtitle_file:
                raise RuntimeError(f"Could not download selected subtitle: {original_lang}")
            body = parse_subtitle_file(subtitle_file, args.timestamps)
            primary_artifact_type = "raw_asr"
            primary_provider = subtitle_source
            primary_source_type = "human_subtitle"
            primary_markdown = markdown_document(video, body, source=f"human subtitle ({original_lang})", language=original_lang)
            raw_path = write_artifact_file(artifact_path(video_dir, video, "raw_asr"), primary_markdown)
            write_artifact_file(original_path, primary_markdown)
            metadata["artifacts"].append(
                artifact_record(
                    "raw_asr",
                    raw_path,
                    source_artifact=None,
                    source_type=primary_source_type,
                    provider=primary_provider,
                    model=None,
                    derivation_stage="primary",
                )
            )
            metadata["primary_artifact"] = "raw_asr"
            metadata["original_mirrors_artifact"] = "raw_asr"
            metadata["source"] = subtitle_source
            metadata["original_language"] = original_lang

            if zh_lang and not is_zh_lang(original_lang):
                zh_subtitle_file = download_subtitle(video, str(url), zh_lang, work_dir, args)
                if zh_subtitle_file:
                    zh_body = parse_subtitle_file(zh_subtitle_file, args.timestamps)
                    zh_path.write_text(
                        markdown_document(video, zh_body, source=f"human subtitle ({zh_lang})", language=zh_lang),
                        encoding="utf-8",
                    )
                    metadata["zh_source"] = "public_api_subtitle" if zh_lang in public_subtitle_languages(video) else "human_subtitle"

            metadata["needs_zh_translation"] = not is_zh_lang(original_lang) and not zh_path.exists()
            if metadata["needs_zh_translation"] and os.environ.get("MOONSHOT_API_KEY"):
                print("Translating transcript to Chinese with Kimi...")
                zh_text = translate_to_zh_with_kimi(original_path.read_text(encoding="utf-8"), args.kimi_model)
                if zh_text:
                    zh_path.write_text(zh_text.rstrip() + "\n", encoding="utf-8")
                    metadata["zh_source"] = f"kimi_translation ({args.kimi_model})"
                    metadata["needs_zh_translation"] = False
        else:
            choice = resolve_provider_choice(args)
            metadata.update(provider_metadata_fields(choice))
            summary.update(provider_metadata_fields(choice))
            summary["backend"] = choice["provider"]
            primary_artifact_type = primary_artifact_for_choice(choice)
            if raw_asr_only_blocked(requested_artifacts(args), primary_artifact_type):
                metadata["primary_artifact"] = primary_artifact_type
                metadata["original_mirrors_artifact"] = None
                metadata["selection_warnings"].append("raw_asr was requested but the selected provider/output is not strict ASR.")
                record_missing_artifacts(
                    metadata,
                    video_dir,
                    video,
                    ["raw_asr"],
                    status="blocked",
                    reason="Selected provider/output is not strict ASR; use an ASR-capable provider for raw_asr.",
                    source_artifact=primary_artifact_type,
                    source_type=choice.get("mode"),
                    provider=choice.get("provider"),
                    model=choice.get("model"),
                )
                blocked_choice = {**choice, "status": "blocked"}
                raise ProviderBlocked(
                    "raw_asr was requested but the selected provider/output is not strict ASR.",
                    blocked_choice,
                )
            if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
                raise RuntimeError("ffmpeg and ffprobe are required for transcription fallback.")
            if choice["provider"] in ("openai", "minimax"):
                audio_path = download_audio(str(url), work_dir, args, video)
                if not audio_path:
                    raise RuntimeError("Could not download audio for transcription.")
                parts = prepare_audio_parts(audio_path, work_dir)
                if choice["provider"] == "openai":
                    body = transcribe_audio(parts, args)
                    source = f"OpenAI transcription ({choice['model']})"
                    metadata["source"] = "openai_transcription"
                    metadata["transcribe_model"] = choice["model"]
                else:
                    body = transcribe_audio_with_minimax_api(parts, args)
                    source = f"MiniMax API transcription ({choice['model']})"
                    metadata["source"] = "minimax_api_transcription"
                    metadata["minimax_model"] = choice["model"]
                    metadata["minimax_endpoint_label"] = choice.get("endpoint_label")
            elif choice["provider"] == "moonshot" and choice["mode"] == "video-understanding":
                video_path = download_video_for_kimi(str(url), work_dir, args)
                if not video_path:
                    raise RuntimeError("Could not download video for Kimi transcription.")
                kimi_video_path = compress_video_for_kimi(video_path, work_dir)
                body = transcribe_video_with_kimi(kimi_video_path, choice["model"], args.timestamps)
                source = f"Kimi video transcription ({choice['model']})"
                metadata["source"] = "kimi_video_transcription"
                metadata["kimi_model"] = choice["model"]
            elif choice["proxy_used"]:
                audio_path = download_audio(str(url), work_dir, args, video)
                if not audio_path:
                    raise RuntimeError("Could not download audio for proxy transcription.")
                parts = prepare_audio_parts(audio_path, work_dir)
                body = transcribe_audio_with_proxy(parts, args, choice)
                source = f"{choice['display_name']} proxy transcription ({choice['model']})"
                metadata["source"] = f"{choice['provider']}_proxy_transcription"
            else:
                raise ProviderBlocked(f"Provider {choice['provider']} cannot execute mode {choice['mode']} directly.", choice)
            if not body:
                raise RuntimeError("Transcription returned empty text.")
            primary_provider = choice["provider"]
            primary_model = choice["model"]
            primary_source_type = choice["mode"]
            primary_markdown = markdown_document(video, body, source=source, language=None)
            primary_path = write_artifact_file(artifact_path(video_dir, video, primary_artifact_type), primary_markdown)
            write_artifact_file(original_path, primary_markdown)
            metadata["artifacts"].append(
                artifact_record(
                    primary_artifact_type,
                    primary_path,
                    source_artifact=None,
                    source_type=primary_source_type,
                    provider=primary_provider,
                    model=primary_model,
                    derivation_stage="primary",
                )
            )
            metadata["primary_artifact"] = primary_artifact_type
            metadata["original_mirrors_artifact"] = primary_artifact_type
            metadata["needs_zh_translation"] = not has_cjk(body)
            if metadata["needs_zh_translation"] and os.environ.get("MOONSHOT_API_KEY"):
                print("Translating transcript to Chinese with Kimi...")
                zh_text = translate_to_zh_with_kimi(original_path.read_text(encoding="utf-8"), args.kimi_model)
                if zh_text:
                    zh_path.write_text(zh_text.rstrip() + "\n", encoding="utf-8")
                    metadata["zh_source"] = f"kimi_translation ({args.kimi_model})"
                    metadata["needs_zh_translation"] = False

        requested = requested_artifacts(args)
        if requested:
            generate_requested_artifacts(
                metadata,
                video_dir,
                video,
                args,
                primary_artifact_type=primary_artifact_type,
                primary_provider=primary_provider,
                primary_model=primary_model,
                primary_source_type=primary_source_type,
            )

        metadata["status"] = "success"
        write_metadata(video_dir, metadata)
        if not args.keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
        print(f"Transcript written: {original_path}")
        if zh_path.exists():
            print(f"Chinese transcript written: {zh_path}")
        elif metadata["needs_zh_translation"]:
            print(f"Chinese translation needed: {zh_path}")
            summary["uncertain"].append(f"Chinese translation still needed: {zh_path}")
        summary["status"] = "success"
        summary["source"] = metadata.get("source") or summary.get("source")
        summary["metadata"] = metadata
        summary["artifacts"] = metadata.get("artifacts", [])
        summary["outputs_written"] = summarize_outputs(video_dir)
        return summary
    except ProviderSelectionRequired as exc:
        record_missing_artifacts(
            metadata,
            video_dir,
            video,
            requested_artifacts(args),
            status="blocked",
            reason=str(exc),
        )
        metadata["error"] = str(exc)
        metadata["status"] = "blocked"
        metadata["provider_checkpoint"] = exc.plan
        write_metadata(video_dir, metadata)
        if not args.keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
        print(f"Blocked: {video.get('title') or url}: {exc}", file=sys.stderr)
        summary["status"] = "blocked"
        summary["source"] = metadata.get("source") or summary.get("source")
        summary["metadata"] = metadata
        summary["artifacts"] = metadata.get("artifacts", [])
        summary["provider_checkpoint"] = exc.plan
        summary["outputs_written"] = summarize_outputs(video_dir)
        summary["failures"].append(str(exc))
        return summary
    except ProviderBlocked as exc:
        metadata.update(provider_metadata_fields(exc.choice))
        record_missing_artifacts(
            metadata,
            video_dir,
            video,
            requested_artifacts(args),
            status="blocked",
            reason=str(exc),
            source_artifact=metadata.get("primary_artifact"),
            source_type=exc.choice.get("mode"),
            provider=exc.choice.get("provider"),
            model=exc.choice.get("model"),
        )
        metadata["error"] = str(exc)
        metadata["status"] = blocked_status(exc.choice)
        if exc.choice.get("provider_checkpoint"):
            metadata["provider_checkpoint"] = exc.choice["provider_checkpoint"]
        write_metadata(video_dir, metadata)
        if not args.keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
        print(f"Blocked: {video.get('title') or url}: {exc}", file=sys.stderr)
        summary.update(provider_metadata_fields(exc.choice))
        summary["status"] = metadata["status"]
        summary["source"] = metadata.get("source") or summary.get("source")
        summary["metadata"] = metadata
        summary["artifacts"] = metadata.get("artifacts", [])
        if exc.choice.get("provider_checkpoint"):
            summary["provider_checkpoint"] = exc.choice["provider_checkpoint"]
        summary["outputs_written"] = summarize_outputs(video_dir)
        summary["failures"].append(str(exc))
        return summary
    except ProviderConfigurationError as exc:
        record_missing_artifacts(
            metadata,
            video_dir,
            video,
            requested_artifacts(args),
            status="blocked",
            reason=str(exc),
        )
        metadata["error"] = str(exc)
        metadata["status"] = "blocked"
        write_metadata(video_dir, metadata)
        if not args.keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
        print(f"Blocked: {video.get('title') or url}: {exc}", file=sys.stderr)
        summary["status"] = "blocked"
        summary["source"] = metadata.get("source") or summary.get("source")
        summary["metadata"] = metadata
        summary["artifacts"] = metadata.get("artifacts", [])
        summary["outputs_written"] = summarize_outputs(video_dir)
        summary["failures"].append(str(exc))
        return summary
    except Exception as exc:
        record_missing_artifacts(
            metadata,
            video_dir,
            video,
            requested_artifacts(args),
            status="skipped",
            reason=str(exc),
        )
        metadata["error"] = str(exc)
        metadata["status"] = "failed"
        write_metadata(video_dir, metadata)
        if not args.keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)
        print(f"Failed: {video.get('title') or url}: {exc}", file=sys.stderr)
        summary["status"] = "failed"
        summary["source"] = metadata.get("source") or summary.get("source")
        summary["metadata"] = metadata
        summary["artifacts"] = metadata.get("artifacts", [])
        summary["outputs_written"] = summarize_outputs(video_dir)
        summary["failures"].append(str(exc))
        return summary


def main() -> int:
    reexec_in_venv(sys.argv[1:])
    args = parse_args()

    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    run_summary = make_run_summary(args, output_root)

    if args.clear_default_provider:
        cleared = clear_default_provider()
        item = {
            "title": "default-provider",
            "id": None,
            "url": None,
            "status": "success",
            "backend": None,
            "transcribe_provider": None,
            "transcribe_mode": None,
            "source": "clear-default-provider",
            "output_paths": {"default_provider_path": str(cleared)},
            "outputs_written": [],
            "failures": [],
            "uncertain": [],
        }
        run_summary["items"].append(item)
        print(f"Default provider cleared: {cleared}")
        if not args.urls:
            write_summary_files(output_root, run_summary)
            return 0

    if args.save_default_provider:
        try:
            choice = resolve_provider_choice(args, allow_default=False)
        except ProviderSelectionRequired as exc:
            print(str(exc), file=sys.stderr)
            run_summary["failures"].append(str(exc))
            write_summary_files(output_root, run_summary)
            return 1
        except ProviderBlocked as exc:
            print(str(exc), file=sys.stderr)
            run_summary["failures"].append(str(exc))
            write_summary_files(output_root, run_summary)
            return 1
        except ProviderConfigurationError as exc:
            print(str(exc), file=sys.stderr)
            run_summary["failures"].append(str(exc))
            write_summary_files(output_root, run_summary)
            return 1
        saved_path = save_default_provider(choice)
        run_summary["transcribe_provider"] = choice["provider"]
        run_summary["transcribe_mode"] = choice["mode"]
        run_summary["default_provider_used"] = False
        print(f"Default provider saved: {choice['provider']} ({choice['mode']}) -> {saved_path}")
        if not args.urls:
            run_summary["items"].append(
                {
                    "title": "default-provider",
                    "id": None,
                    "url": None,
                    "status": "success",
                    "backend": choice["provider"],
                    **provider_metadata_fields(choice),
                    "source": "save-default-provider",
                    "output_paths": {"default_provider_path": str(saved_path)},
                    "outputs_written": [str(saved_path)],
                    "failures": [],
                    "uncertain": [],
                }
            )
            write_summary_files(output_root, run_summary)
            return 0

    if args.doctor:
        status, item = doctor_report(args, output_root)
        run_summary["items"].append(item)
        run_summary["backend"] = args.transcribe_backend
        write_summary_files(output_root, run_summary)
        print(f"\nDoctor summary written: {output_root / 'run-summary.json'}")
        return status

    failures = 0
    for url in args.urls:
        info = fetch_info(url, args)
        if not info:
            fallback_plan = public_api_plan(
                url,
                disabled=public_api_fallback_disabled(args),
                stages=PUBLIC_API_STAGES,
            )
            failures += 1
            item = {
                "title": None,
                "id": None,
                "url": redact_url(url),
                "status": "failed",
                "backend": args.transcribe_backend,
                "source": "yt_dlp_metadata",
                "output_paths": {},
                "outputs_written": [],
                "failures": [f"Failed to inspect URL: {redact_url(url)}"],
                "uncertain": [],
            }
            item.update(public_api_summary_fields(fallback_plan))
            run_summary["items"].append(item)
            continue
        for video in iter_videos(info, url):
            item = dry_run_video(video, output_root, args) if args.dry_run else process_video(video, output_root, args)
            run_summary["items"].append(item)
            if item.get("status") in {"failed", "blocked", "requires-proxy"}:
                failures += 1
    backends = sorted({str(item.get("backend")) for item in run_summary["items"] if item.get("backend")})
    run_summary["backend"] = backends[0] if len(backends) == 1 else "mixed" if backends else args.transcribe_backend
    providers = sorted({str(item.get("transcribe_provider")) for item in run_summary["items"] if item.get("transcribe_provider")})
    modes = sorted({str(item.get("transcribe_mode")) for item in run_summary["items"] if item.get("transcribe_mode")})
    run_summary["transcribe_provider"] = providers[0] if len(providers) == 1 else "mixed" if providers else None
    run_summary["transcribe_mode"] = modes[0] if len(modes) == 1 else "mixed" if modes else None
    run_summary["default_provider_used"] = any(bool(item.get("default_provider_used")) for item in run_summary["items"])
    write_summary_files(output_root, run_summary)

    if args.dry_run:
        print(f"\nDry run complete. Summaries are in: {output_root}")
    else:
        print(f"\nDone. Transcript folders are in: {output_root}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
