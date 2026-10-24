"""
Core AI & Pipeline modules cho hệ thống Video Factory.
"""
from .config_store import load_ai_config, save_ai_config
from .prompt_builder import (
    parse_duration_from_topic,
    format_plan_to_review_text,
)
from .gemini_service import GeminiService, GeminiResult, GeminiAPIError
from .ai_pipeline import (
    AIPipeline,
    CodeSession,
    PlanSession,
    parse_scenes_from_file,
    revoice_project_video,
)
from .layout_auditor import AuditOutcome, audit_scene_file
from .tts_service import (
    DEFAULT_TTS_VOICE,
    TTS_SPEED_OPTIONS,
    VIENEU_PRESET_VOICES,
    ScriptAudioPack,
    VieNeuTTSService,
    extract_scene_narrations,
    mux_scene_audio_into_video,
    play_wav_async,
    stop_wav_playback,
)

__all__ = [
    "load_ai_config",
    "save_ai_config",
    "parse_duration_from_topic",
    "format_plan_to_review_text",
    "GeminiService",
    "GeminiResult",
    "GeminiAPIError",
    "AIPipeline",
    "PlanSession",
    "CodeSession",
    "parse_scenes_from_file",
    "revoice_project_video",
    "AuditOutcome",
    "audit_scene_file",
    "DEFAULT_TTS_VOICE",
    "VIENEU_PRESET_VOICES",
    "TTS_SPEED_OPTIONS",
    "ScriptAudioPack",
    "VieNeuTTSService",
    "extract_scene_narrations",
    "mux_scene_audio_into_video",
    "play_wav_async",
    "stop_wav_playback",
]
