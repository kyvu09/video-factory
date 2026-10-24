"""
Lưu trữ cấu hình cục bộ (API Key, Model mặc định...) cho tính năng AI.
File `.ai_config.json` đã được loại trừ trong `.gitignore` để bảo mật khóa API.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / ".ai_config.json"
ENV_PATH = BASE_DIR / ".env"

DEFAULT_AI_CONFIG: dict[str, Any] = {
    "api_key": "",
    "model": "gemini-3.8-flash",
    "default_duration": 45,
    "default_style": "channel_dark",
    "default_aspect_ratio": "16:9",
    "default_resolution": "-l",
    "max_fix_retries": 3,
    "tts_enabled": True,
    "tts_voice": "Hải Đăng",
    "tts_speed": 1.0,
}


def _read_env_api_key() -> str:
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    if env_key:
        return env_key.strip()
    if ENV_PATH.is_file():
        try:
            for line in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                k, v = stripped.split("=", 1)
                if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                    return v.strip().strip('"').strip("'")
        except Exception:
            pass
    return ""


def load_ai_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_AI_CONFIG)
    if CONFIG_PATH.is_file():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass
    if not cfg.get("api_key"):
        cfg["api_key"] = _read_env_api_key()
    # Gemini 2.0 Flash was shut down; upgrade saved local configs on load.
    if cfg.get("model") == "gemini-2.0-flash":
        cfg["model"] = "gemini-3.8-flash"
    return cfg


def save_ai_config(updates: dict[str, Any]) -> dict[str, Any]:
    cfg = load_ai_config()
    cfg.update(updates)
    if cfg.get("model") == "gemini-2.0-flash":
        cfg["model"] = "gemini-3.8-flash"
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass
    return cfg
