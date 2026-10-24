"""
Dịch vụ Thuyết minh Giọng đọc AI Tiếng Việt Offline (VieNeu-TTS 48kHz) &
Đồng bộ Âm thanh – Hình ảnh theo từng Phân cảnh (Zero-Drift Per-Scene Audio Sync).

Tính năng chính:
  1. Bóc tách lời dẫn (`Lời dẫn / Ý giảng`) từng phân cảnh từ kịch bản đã duyệt & chuẩn hóa ký hiệu Toán/IT sang văn nói tự nhiên.
  2. Tổng hợp giọng đọc Tiếng Việt 48kHz 100% offline bằng `VieNeu-TTS` (kèm bộ nhớ đệm `audio_manifest.json` tránh đọc lại cảnh chưa sửa).
  3. Ghép (mux) âm thanh khớp chính xác từng phân cảnh vào video `.mp4` của ManimGL bằng `ffmpeg` (`tpad=stop_mode=clone` giữ khung hình tĩnh cuối cảnh nếu lời giảng dài hơn hoạt ảnh, đảm bảo không bao giờ đứt câu hoặc lệch cảnh).
  4. Phát nghe thử (`winsound`) ngay trên giao diện `Video Factory Studio`.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from typing import Any, Callable

import numpy as np
import soundfile as sf

# Ẩn các cảnh báo tải không cần thiết của HuggingFace Hub khi chạy offline
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

DEFAULT_TTS_VOICE = "Hải Đăng"

# Danh sách 25 giọng đọc chuẩn của VieNeu-TTS 48kHz (ưu tiên giọng giảng bài tự nhiên lên đầu)
VIENEU_PRESET_VOICES: list[tuple[str, str]] = [
    ("⭐ Hải Đăng — Nam · Bắc · Tự nhiên (Khuyên dùng)", "Hải Đăng"),
    ("⭐ Thiện Minh — Nam · Bắc · Kể chuyện ấm áp", "Thiện Minh"),
    ("⭐ Trúc Ly — Nữ · Bắc · Tự nhiên trong trẻo", "Trúc Ly"),
    ("⭐ Mai Anh — Nữ · Bắc · Tin tức rõ ràng", "Mai Anh"),
    ("⭐ Thùy Dung — Nữ · Nam · Tin tức truyền cảm", "Thùy Dung"),
    ("⭐ Ngọc Huyền — Nữ · Bắc · Giọng đọc tự nhiên", "Ngọc Huyền"),
    ("⭐ Quang Sơn — Nam · Trung · Tự nhiên", "Quang Sơn"),
    ("⭐ Ngọc Trân — Nữ · Trung · Tự nhiên", "Ngọc Trân"),
    ("⭐ Thiền Tâm Đức — Nam · Bắc · Trầm ấm", "Thiền Tâm Đức"),
    ("Minh Đức — Nam · Bắc · Tin tức", "Minh Đức"),
    ("Phạm Tuyên — Nam · Bắc · Tự nhiên", "Phạm Tuyên"),
    ("Thái Sơn — Nam · Nam · Kể chuyện", "Thái Sơn"),
    ("Xuân Vĩnh — Nam · Bắc · Tự nhiên", "Xuân Vĩnh"),
    ("Thanh Bình — Nam · Bắc · Kể chuyện", "Thanh Bình"),
    ("Ngọc Linh — Nữ · Bắc · Kể chuyện", "Ngọc Linh"),
    ("Đoan Trang — Nữ · Bắc · Tự nhiên", "Đoan Trang"),
    ("Thục Đoan — Nữ · Nam · Kể chuyện", "Thục Đoan"),
    ("Minh Triết — Nam · Nam · Tin tức", "Minh Triết"),
    ("Mỹ Duyên — Nữ · Nam · Đọc truyện", "Mỹ Duyên"),
    ("Quỳnh Anh — Nữ · Bắc · Đọc truyện", "Quỳnh Anh"),
    ("Đức Trí — Nam · Nam · Đọc truyện", "Đức Trí"),
    ("Kim Thanh — Nữ · Nam · Đọc truyện", "Kim Thanh"),
    ("Adam — Nam · Nam · Tự nhiên", "Adam"),
    ("Quốc Tuấn — Nam · Bắc · Tự nhiên", "Quốc Tuấn"),
    ("⭐ Adam bựa — Nam · Bắc · Sôi nổi", "Adam bựa"),
]

TTS_SPEED_OPTIONS: list[tuple[str, float]] = [
    ("0.9x (Chậm rãi)", 0.9),
    ("1.0x (Chuẩn tự nhiên)", 1.0),
    ("1.1x (Nhanh vừa)", 1.1),
    ("1.2x (Nhanh)", 1.2),
]


@dataclass
class SceneNarration:
    index: int
    title: str
    raw_text: str
    clean_text: str


@dataclass
class SceneAudioClip:
    index: int
    title: str
    text: str
    wav_path: Path
    duration_sec: float


@dataclass
class ScriptAudioPack:
    voice: str
    speed: float
    sample_rate: int
    clips: list[SceneAudioClip]
    preview_wav_path: Path
    total_audio_duration: float

    def target_scene_durations(self, pad_sec: float = 0.65) -> list[float]:
        """Thời lượng hoạt ảnh khuyến nghị cho từng phân cảnh (bằng lời đọc + khoảng nghỉ tự nhiên)."""
        return [round(max(4.0, c.duration_sec + pad_sec), 1) for c in self.clips]


# ------------------------------------------------------------------
# CHUẨN HÓA VĂN BẢN & BÓC TÁCH LỜI DẪN TỪ KỊCH BẢN
# ------------------------------------------------------------------
def sanitize_text_for_tts(text: str) -> str:
    """Làm sạch ký hiệu Toán học / Lập trình để VieNeu-TTS đọc Tiếng Việt mượt và tự nhiên."""
    if not text:
        return ""
    s = str(text).strip()

    # Loại bỏ cặp dấu $...$ bao quanh công thức ngắn nếu có
    s = s.replace("$", " ")
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)

    # Ký hiệu độ phức tạp thuật toán phổ biến
    s = re.sub(r"\bO\(\s*1\s*\)", "O 1", s)
    s = re.sub(r"\bO\(\s*[nN]\s*\)", "O N", s)
    s = re.sub(r"\bO\(\s*[nN]\s*\^\s*2\s*\)", "O N bình phương", s)
    s = re.sub(r"\bO\(\s*2\s*\^\s*[nN]\s*\)", "O hai mũ N", s)
    s = re.sub(r"\bO\(\s*[nN]\s*log\s*[nN]\s*\)", "O N lốc N", s, flags=re.I)
    s = re.sub(r"\bO\(\s*log\s*[nN]\s*\)", "O lốc N", s, flags=re.I)

    # Biểu thức mảng / lũy thừa cơ bản
    s = re.sub(r"\bdp\[\s*([a-zA-Z0-9_+-]+)\s*\]", r"d p \1", s)
    s = re.sub(r"\b([a-zA-Z])\s*\^\s*2\b", r"\1 bình phương", s)
    s = re.sub(r"\b([a-zA-Z])\s*\^\s*3\b", r"\1 lập phương", s)

    # Mũi tên & toán tử so sánh
    s = re.sub(r"\s*(?:->|=>|➔|⟶|\\to|\\rightarrow)\s*", ", ", s)
    s = s.replace("!=", " khác ").replace(">=", " lớn hơn hoặc bằng ").replace("<=", " nhỏ hơn hoặc bằng ")

    # Gạch ngang dài chuyển thành dấu phẩy nghỉ nhịp tự nhiên
    s = re.sub(r"\s+[–—-]\s+", ", ", s)

    # Bỏ ngoặc kép / nháy đơn / backtick bọc quanh từ khóa
    s = s.replace("`", "").replace('"', "").replace("“", "").replace("”", "")
    s = re.sub(r"(?<!\w)'([^']+)'(?!\w)", r"\1", s)

    # Thu gọn khoảng trắng thừa
    s = re.sub(r"\s+", " ", s).strip()
    if s and s[-1] not in ".?!…":
        s += "."
    return s


def extract_scene_narrations(script_text: str) -> list[SceneNarration]:
    """
    Trích xuất danh sách `SceneNarration` theo đúng thứ tự các phân cảnh trong kịch bản.
    Hỗ trợ cả định dạng chuẩn `### Phân cảnh k ...` lẫn văn bản tự do do người dùng gõ.
    """
    if not script_text or not script_text.strip():
        return []

    # Cắt bỏ phần ghi chú hướng dẫn cuối file (`# Ghi chú chỉnh sửa thêm...`)
    cleaned_doc = re.split(r"\n#\s*Ghi chú chỉnh sửa thêm", script_text, maxsplit=1)[0]

    scene_header_pat = re.compile(r"^###\s*Phân cảnh\s*(\d+)(.*)$", flags=re.M)
    matches = list(scene_header_pat.finditer(cleaned_doc))

    narrations: list[SceneNarration] = []
    if matches:
        for idx_pos, m in enumerate(matches):
            sc_num = int(m.group(1))
            header_tail = m.group(2).strip(" —-:")
            start = m.end()
            end = matches[idx_pos + 1].start() if idx_pos + 1 < len(matches) else len(cleaned_doc)
            block = cleaned_doc[start:end]

            narration_raw = _extract_narration_from_block(block)
            if not narration_raw:
                # Dự phòng nếu người dùng xóa dòng `Lời dẫn`: ghép các chữ hiển thị hoặc tiêu đề phân cảnh
                quoted = re.findall(r'\+\s*"([^"]+)"', block)
                narration_raw = ". ".join(quoted) if quoted else header_tail

            clean = sanitize_text_for_tts(narration_raw)
            if clean:
                narrations.append(
                    SceneNarration(
                        index=sc_num,
                        title=header_tail or f"Phân cảnh {sc_num}",
                        raw_text=narration_raw.strip(),
                        clean_text=clean,
                    )
                )
        return narrations

    # Fallback: Người dùng tự gõ kịch bản tự do không có `### Phân cảnh`
    explicit_lines = re.findall(
        r"(?:Lời dẫn(?:\s*/\s*Ý giảng)?|Thuyết minh)\s*:\s*(.+)",
        cleaned_doc,
        flags=re.I,
    )
    if explicit_lines:
        for i, raw in enumerate(explicit_lines, start=1):
            clean = sanitize_text_for_tts(raw)
            if clean:
                narrations.append(SceneNarration(index=i, title=f"Đoạn {i}", raw_text=raw.strip(), clean_text=clean))
        return narrations

    # Fallback cuối: tách theo đoạn văn không bắt đầu bằng `#` hoặc `---`
    paragraphs: list[str] = []
    buf: list[str] = []
    for line in cleaned_doc.splitlines():
        s = line.strip()
        if not s or s.startswith("---") or s.startswith("#"):
            if buf:
                paragraphs.append(" ".join(buf))
                buf = []
            continue
        s = re.sub(r"^[-*+]\s*", "", s)
        buf.append(s)
    if buf:
        paragraphs.append(" ".join(buf))

    for i, raw in enumerate(paragraphs[:12], start=1):
        clean = sanitize_text_for_tts(raw)
        if clean:
            narrations.append(SceneNarration(index=i, title=f"Đoạn {i}", raw_text=raw, clean_text=clean))
    return narrations


def _extract_narration_from_block(block: str) -> str:
    """Lấy nội dung của mục `- Lời dẫn / Ý giảng:` (hỗ trợ trường hợp người dùng xuống dòng viết tiếp)."""
    lines = block.splitlines()
    collecting = False
    collected: list[str] = []
    start_pat = re.compile(r"^\s*[-*•]?\s*(?:Lời dẫn(?:\s*/\s*Ý giảng)?|Thuyết minh)\s*:\s*(.*)$", flags=re.I)

    for line in lines:
        stripped = line.strip()
        m = start_pat.match(line)
        if m:
            collecting = True
            first = m.group(1).strip()
            if first:
                collected.append(first)
            continue

        if collecting:
            if not stripped or stripped.startswith("---") or stripped.startswith("#"):
                break
            if re.match(r"^\s*[-*]\s+[A-ZÀ-Ỹ]", line):
                break
            collected.append(stripped)

    return " ".join(collected).strip()


# ------------------------------------------------------------------
# ENGINE TỔNG HỢP GIỌNG NÓI VIENEU-TTS (SINGLETON AN TOÀN LUỒNG)
# ------------------------------------------------------------------
class VieNeuTTSService:
    _instance: VieNeuTTSService | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._engine: Any = None
        self._engine_lock = threading.Lock()
        self._available_voice_ids: set[str] = set()
        self._sample_rate: int = 48000

    @classmethod
    def get_instance(cls) -> VieNeuTTSService:
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _ensure_engine(self, on_log: Callable[[str], None] | None = None) -> Any:
        if self._engine is not None:
            return self._engine

        log = on_log or (lambda _msg: None)
        log("🎙️ Đang khởi tạo bộ đọc giọng AI Tiếng Việt `VieNeu-TTS` (48kHz Offline)...\n")
        from vieneu import Vieneu

        engine = Vieneu()
        self._sample_rate = int(getattr(engine, "sample_rate", 48000) or 48000)
        try:
            presets = engine.list_preset_voices() or []
            self._available_voice_ids = {str(v_id) for _desc, v_id in presets}
        except Exception:
            self._available_voice_ids = {v_id for _lbl, v_id in VIENEU_PRESET_VOICES}

        self._engine = engine
        return engine

    def resolve_voice_id(self, requested_voice: str | None) -> str:
        v = (requested_voice or DEFAULT_TTS_VOICE).strip()
        if not self._available_voice_ids:
            return v or DEFAULT_TTS_VOICE
        if v in self._available_voice_ids:
            return v
        if DEFAULT_TTS_VOICE in self._available_voice_ids:
            return DEFAULT_TTS_VOICE
        return next(iter(self._available_voice_ids))

    def synthesize_to_wav(
        self,
        text: str,
        output_wav: str | Path,
        voice: str = DEFAULT_TTS_VOICE,
        speed: float = 1.0,
        on_log: Callable[[str], None] | None = None,
    ) -> float:
        """Tổng hợp 1 đoạn văn bản Tiếng Việt ra file WAV 48kHz PCM_16, trả về thời lượng (giây)."""
        out_path = Path(output_wav)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        clean_text = sanitize_text_for_tts(text)
        if not clean_text:
            silence = np.zeros(int(48000 * 0.5), dtype=np.float32)
            sf.write(str(out_path), silence, 48000, subtype="PCM_16")
            return 0.5

        with self._engine_lock:
            engine = self._ensure_engine(on_log=on_log)
            voice_id = self.resolve_voice_id(voice)
            audio = np.asarray(engine.infer(clean_text, voice=voice_id), dtype=np.float32).reshape(-1)
            sr = self._sample_rate

        if audio.size == 0:
            audio = np.zeros(int(sr * 0.5), dtype=np.float32)

        # Chuẩn hóa biên độ giọng đọc rõ ràng, đồng đều (-1.2 dBFS peak ~ 0.87)
        peak = float(np.max(np.abs(audio)))
        if peak > 1e-4:
            target_peak = 0.87
            gain = min(2.2, target_peak / peak)
            audio = np.clip(audio * gain, -0.98, 0.98)

        clamped_speed = max(0.75, min(1.5, float(speed or 1.0)))
        if abs(clamped_speed - 1.0) <= 0.02 or not shutil.which("ffmpeg"):
            sf.write(str(out_path), audio, sr, subtype="PCM_16")
            return round(float(len(audio)) / float(sr), 3)

        raw_tmp = out_path.with_suffix(".raw_speed.wav")
        sf.write(str(raw_tmp), audio, sr, subtype="PCM_16")
        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_tmp),
                "-filter:a",
                f"atempo={clamped_speed:.3f}",
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                str(sr),
                "-ac",
                "1",
                str(out_path),
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                creationflags=creation_flags,
                timeout=60,
            )
            if res.returncode != 0 or not out_path.is_file():
                os.replace(raw_tmp, out_path)
        finally:
            if raw_tmp.is_file():
                try:
                    raw_tmp.unlink()
                except Exception:
                    pass

        info = sf.info(str(out_path))
        return round(float(info.duration), 3)

    def synthesize_script_scenes(
        self,
        script_text: str,
        project_dir: str | Path,
        voice: str = DEFAULT_TTS_VOICE,
        speed: float = 1.0,
        stop_event: threading.Event | None = None,
        on_log: Callable[[str], None] | None = None,
    ) -> ScriptAudioPack | None:
        """
        Tạo file `.wav` cho từng phân cảnh trong `projects/<slug>/audio/` (tự động dùng cache nếu không đổi chữ/giọng)
        và xuất kèm `narration_preview.wav` nối liền toàn bài để nghe thử trên GUI.
        """
        log = on_log or (lambda _msg: None)
        scenes = extract_scene_narrations(script_text)
        if not scenes:
            log("⚠️ Không tìm thấy nội dung lời dẫn trong kịch bản để tạo giọng đọc.\n")
            return None

        audio_dir = Path(project_dir) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = audio_dir / "audio_manifest.json"

        cached_manifest: dict[str, Any] = {}
        if manifest_path.is_file():
            try:
                cached_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                cached_manifest = {}

        cached_entries: dict[str, dict[str, Any]] = cached_manifest.get("entries") or {}
        new_entries: dict[str, dict[str, Any]] = {}
        clips: list[SceneAudioClip] = []

        log(
            f"\n🎙️ [TTS] Đang tạo giọng thuyết minh cho {len(scenes)} phân cảnh "
            f"(Giọng: {voice} | Tốc độ: {speed:.1f}x)...\n"
        )

        for pos, sc in enumerate(scenes, start=1):
            if stop_event and stop_event.is_set():
                return None

            wav_name = f"scene_{pos:02d}.wav"
            wav_path = audio_dir / wav_name
            sig_key = hashlib.sha256(f"{voice}|{speed:.2f}|{sc.clean_text}".encode("utf-8")).hexdigest()[:20]

            prev = cached_entries.get(wav_name)
            if prev and prev.get("sig") == sig_key and wav_path.is_file():
                dur = float(prev.get("duration_sec") or sf.info(str(wav_path)).duration)
                log(f"   • Phân cảnh {sc.index}: {dur:.1f}s (dùng lại bản thu chuẩn)\n")
            else:
                dur = self.synthesize_to_wav(
                    text=sc.clean_text,
                    output_wav=wav_path,
                    voice=voice,
                    speed=speed,
                    on_log=log,
                )
                log(f"   • Phân cảnh {sc.index}: đã thu {dur:.1f}s — \"{sc.clean_text[:68]}{'...' if len(sc.clean_text) > 68 else ''}\"\n")

            new_entries[wav_name] = {
                "sig": sig_key,
                "index": sc.index,
                "voice": voice,
                "speed": speed,
                "text": sc.clean_text,
                "duration_sec": round(dur, 3),
            }
            clips.append(
                SceneAudioClip(
                    index=sc.index,
                    title=sc.title,
                    text=sc.clean_text,
                    wav_path=wav_path,
                    duration_sec=round(dur, 3),
                )
            )

        # Tạo bản nối liền `narration_preview.wav` để nghe thử mượt mà trên GUI
        preview_path = audio_dir / "narration_preview.wav"
        sr = self._sample_rate
        pause_samples = np.zeros(int(sr * 0.42), dtype=np.float32)
        pieces: list[np.ndarray] = []
        for idx_c, clip in enumerate(clips):
            data, file_sr = sf.read(str(clip.wav_path), dtype="float32")
            if data.ndim > 1:
                data = data.mean(axis=1)
            if file_sr != sr and len(data) > 1:
                # Nội suy tuyến tính nhẹ nếu tần số mẫu khác
                new_len = int(round(len(data) * sr / file_sr))
                data = np.interp(
                    np.linspace(0.0, 1.0, new_len, endpoint=False),
                    np.linspace(0.0, 1.0, len(data), endpoint=False),
                    data,
                ).astype(np.float32)
            pieces.append(data)
            if idx_c < len(clips) - 1:
                pieces.append(pause_samples)

        combined = np.concatenate(pieces) if pieces else np.zeros(int(sr * 0.5), dtype=np.float32)
        sf.write(str(preview_path), combined, sr, subtype="PCM_16")
        total_dur = round(sum(c.duration_sec for c in clips), 2)

        manifest_data = {
            "voice": voice,
            "speed": speed,
            "sample_rate": sr,
            "total_audio_duration": total_dur,
            "entries": new_entries,
        }
        manifest_path.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

        log(f"✅ [TTS Hoàn tất] Tổng thời lượng giọng đọc: {total_dur:.1f}s (48kHz WAV).\n")
        return ScriptAudioPack(
            voice=voice,
            speed=speed,
            sample_rate=sr,
            clips=clips,
            preview_wav_path=preview_path,
            total_audio_duration=total_dur,
        )


# ------------------------------------------------------------------
# ĐỒNG BỘ & GHÉP ÂM THANH THEO TỪNG PHÂN CẢNH VÀO MP4 (FFMPEG)
# ------------------------------------------------------------------
def probe_media_duration(media_path: str | Path) -> float:
    """Đọc thời lượng thực tế (giây) của file MP4/WAV bằng `ffprobe`."""
    p = Path(media_path)
    if not p.is_file() or not shutil.which("ffprobe"):
        return 0.0
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(p),
    ]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
            timeout=20,
        )
        return max(0.0, float((res.stdout or "0").strip()))
    except Exception:
        return 0.0


def _choose_best_subsequence(candidates: list[float], targets: list[float]) -> list[float]:
    """Chọn dãy con tăng ngặt độ dài `len(targets)` từ `candidates` gần với `targets` nhất."""
    m = len(targets)
    n = len(candidates)
    if m == 0 or n < m:
        return candidates[:m]
    if n == m:
        return list(candidates)

    # Quy hoạch động O(m * n^2) với n <= 30 (chạy tức thì < 0.1ms)
    inf = 1e18
    dp = [[inf] * n for _ in range(m)]
    parent = [[-1] * n for _ in range(m)]

    for j in range(n):
        dp[0][j] = abs(candidates[j] - targets[0])

    for i in range(1, m):
        for j in range(i, n):
            cost = abs(candidates[j] - targets[i])
            for prev_j in range(i - 1, j):
                if dp[i - 1][prev_j] + cost < dp[i][j]:
                    dp[i][j] = dp[i - 1][prev_j] + cost
                    parent[i][j] = prev_j

    best_last = min(range(m - 1, n), key=lambda j: dp[m - 1][j])
    chosen = [0.0] * m
    cur = best_last
    for i in range(m - 1, -1, -1):
        chosen[i] = candidates[cur]
        cur = parent[i][cur]
    return chosen


def _resolve_segment_boundaries(
    cut_times: list[float],
    header_times: list[float],
    virtual_dur: float,
    actual_video_dur: float,
    clip_durs: list[float],
) -> list[float]:
    """Tính danh sách `K + 1` mốc thời gian `[0.0, b_1, ..., b_{K-1}, actual_video_dur]` chia video thành `K` phân cảnh."""
    k = len(clip_durs)
    if k <= 1 or actual_video_dur <= 1.2:
        return [0.0, max(0.5, actual_video_dur)]

    scale = (actual_video_dur / virtual_dur) if (virtual_dur > 0.5 and actual_video_dur > 0.5) else 1.0
    scaled_cuts = sorted({round(c * scale, 3) for c in cut_times if 0.8 <= c * scale <= actual_video_dur - 1.0})
    scaled_hdrs = sorted({round(max(0.8, h * scale - 0.45), 3) for h in header_times if 1.3 <= h * scale <= actual_video_dur - 1.0})

    weights = [max(2.0, d) for d in clip_durs]
    total_w = sum(weights)
    cum_targets = [
        round(actual_video_dur * sum(weights[:i]) / total_w, 3)
        for i in range(1, k)
    ]

    if len(scaled_cuts) == k - 1:
        interior = scaled_cuts
    elif len(scaled_cuts) > k - 1:
        interior = _choose_best_subsequence(scaled_cuts, cum_targets)
    elif len(scaled_hdrs) == k - 1:
        interior = scaled_hdrs
    elif len(scaled_hdrs) > k - 1:
        interior = _choose_best_subsequence(scaled_hdrs, cum_targets)
    else:
        # Kết hợp mốc chia tỷ lệ và bám vào các điểm `clear_stage` thực tế nếu ở gần
        interior = []
        used_cuts: set[float] = set()
        for t_goal in cum_targets:
            near = [c for c in scaled_cuts if c not in used_cuts and abs(c - t_goal) <= 2.5]
            if near:
                pick = min(near, key=lambda c: abs(c - t_goal))
                used_cuts.add(pick)
                interior.append(pick)
            else:
                interior.append(t_goal)

    # Đảm bảo tính tăng ngặt cách nhau tối thiểu 0.45s
    boundaries = [0.0]
    min_step = 0.45
    for idx, val in enumerate(interior):
        rem_After = (k - 1) - idx
        lo = boundaries[-1] + min_step
        hi = actual_video_dur - rem_After * min_step
        boundaries.append(round(max(lo, min(hi, val)), 3))
    boundaries.append(round(actual_video_dur, 3))
    return boundaries


def mux_scene_audio_into_video(
    video_path: str | Path,
    audio_pack: ScriptAudioPack,
    output_video_path: str | Path | None = None,
    cut_times: list[float] | None = None,
    header_times: list[float] | None = None,
    virtual_duration: float = 0.0,
    on_log: Callable[[str], None] | None = None,
) -> Path:
    """
    Ghép các file âm thanh `scene_01.wav .. scene_0K.wav` khớp chính xác từng phân cảnh vào `video_path`.
    Nếu lời thuyết minh của một cảnh dài hơn thời lượng hình của cảnh đó, tự động giữ tĩnh (freeze-clone)
    khung hình cuối cảnh trước khi chuyển sang cảnh kế tiếp — không bao giờ cắt chữ hay trôi lệch!
    """
    log = on_log or (lambda _msg: None)
    src_mp4 = Path(video_path)
    dest_mp4 = Path(output_video_path) if output_video_path is not None else src_mp4
    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    if not src_mp4.is_file():
        raise FileNotFoundError(f"Không tìm thấy file video để lồng tiếng: {src_mp4}")
    if not audio_pack.clips:
        return dest_mp4
    if not shutil.which("ffmpeg"):
        log("⚠️ Không tìm thấy `ffmpeg` trong PATH nên giữ nguyên video chưa ghép tiếng.\n")
        return src_mp4

    actual_vid_dur = probe_media_duration(src_mp4)
    if actual_vid_dur <= 0.2:
        actual_vid_dur = max(virtual_duration, sum(c.duration_sec for c in audio_pack.clips))

    clips = audio_pack.clips
    k = len(clips)
    boundaries = _resolve_segment_boundaries(
        cut_times=cut_times or [],
        header_times=header_times or [],
        virtual_dur=virtual_duration,
        actual_video_dur=actual_vid_dur,
        clip_durs=[c.duration_sec for c in clips],
    )

    log(f"🔊 [Muxing] Đang đồng bộ {k} phân cảnh giọng đọc (48kHz AAC) vào `{dest_mp4.name}`...\n")

    tmp_out = dest_mp4.with_suffix(".voiced_tmp.mp4")
    cmd: list[str] = ["ffmpeg", "-y", "-i", str(src_mp4)]
    for clip in clips:
        cmd.extend(["-i", str(clip.wav_path)])

    filter_parts: list[str] = []
    concat_inputs: list[str] = []

    for i, clip in enumerate(clips):
        seg_start = boundaries[i]
        seg_end = boundaries[i + 1]
        vis_dur = max(0.3, seg_end - seg_start)

        lead_in = 0.18 if i == 0 else 0.32
        tail_pad = 0.28
        needed_dur = lead_in + clip.duration_sec + tail_pad
        target_dur = round(max(vis_dur, needed_dur), 3)
        extra_freeze = round(max(0.0, target_dur - vis_dur), 3)
        lead_ms = int(round(lead_in * 1000))

        if extra_freeze > 0.04:
            v_chain = (
                f"[0:v]trim=start={seg_start:.3f}:end={seg_end:.3f},setpts=PTS-STARTPTS,"
                f"tpad=stop_mode=clone:stop_duration={extra_freeze:.3f}[v{i}]"
            )
        else:
            v_chain = f"[0:v]trim=start={seg_start:.3f}:end={seg_end:.3f},setpts=PTS-STARTPTS[v{i}]"

        a_chain = (
            f"[{i + 1}:a]aresample=48000,"
            f"aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"adelay={lead_ms}|{lead_ms},"
            f"apad=whole_dur={target_dur:.3f},"
            f"atrim=0:{target_dur:.3f},"
            f"asetpts=PTS-STARTPTS[a{i}]"
        )
        filter_parts.append(v_chain)
        filter_parts.append(a_chain)
        concat_inputs.append(f"[v{i}][a{i}]")

    if k == 1:
        v_map = "[v0]"
        a_map = "[a0]"
    else:
        filter_parts.append(f"{''.join(concat_inputs)}concat=n={k}:v=1:a=1[vout][aout]")
        v_map = "[vout]"
        a_map = "[aout]"

    filter_complex = ";".join(filter_parts)
    cmd.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            v_map,
            "-map",
            a_map,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(tmp_out),
        ]
    )

    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creation_flags,
        timeout=240,
    )

    if proc.returncode != 0 or not tmp_out.is_file():
        if tmp_out.is_file():
            try:
                tmp_out.unlink()
            except Exception:
                pass
        err_tail = (proc.stderr or "")[-600:]
        log(f"⚠️ Ghép phân cảnh nâng cao gặp lỗi, đang chuyển sang ghép nối liền dự phòng...\n{err_tail}\n")
        return _fallback_simple_mux(src_mp4, dest_mp4, audio_pack.preview_wav_path, log)

    try:
        os.replace(tmp_out, dest_mp4)
    except PermissionError:
        alt_dest = dest_mp4.with_name(f"{dest_mp4.stem}_voiced.mp4")
        os.replace(tmp_out, alt_dest)
        dest_mp4 = alt_dest
        log(f"ℹ️ File gốc đang mở trong trình phát nên đã lưu bản lồng tiếng sang `{dest_mp4.name}`.\n")

    final_dur = probe_media_duration(dest_mp4)
    log(f"✅ Đã lồng tiếng thành công vào `{dest_mp4.name}` (Thời lượng hoàn chỉnh: {final_dur:.1f}s)!\n")
    return dest_mp4


def _fallback_simple_mux(src_mp4: Path, dest_mp4: Path, wav_path: Path, log: Callable[[str], None]) -> Path:
    """Phương án dự phòng an toàn: ghép trực tiếp file `narration_preview.wav` vào MP4."""
    if not wav_path.is_file():
        return src_mp4
    tmp_out = dest_mp4.with_suffix(".simple_voiced.mp4")
    vid_dur = probe_media_duration(src_mp4)
    aud_dur = probe_media_duration(wav_path)
    extra = max(0.0, aud_dur + 0.3 - vid_dur)

    vf_args = ["-vf", f"tpad=stop_mode=clone:stop_duration={extra:.3f}"] if extra > 0.05 else ["-c:v", "copy"]
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src_mp4),
        "-i",
        str(wav_path),
        *vf_args,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        str(tmp_out),
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    res = subprocess.run(cmd, capture_output=True, creationflags=creation_flags, timeout=180)
    if res.returncode == 0 and tmp_out.is_file():
        try:
            os.replace(tmp_out, dest_mp4)
        except PermissionError:
            dest_mp4 = dest_mp4.with_name(f"{dest_mp4.stem}_voiced.mp4")
            os.replace(tmp_out, dest_mp4)
        log(f"✅ Đã ghép giọng đọc dự phòng vào `{dest_mp4.name}`!\n")
        return dest_mp4
    elif tmp_out.is_file():
        try:
            tmp_out.unlink()
        except Exception:
            pass
    return src_mp4


# ------------------------------------------------------------------
# PHÁT NGHE THỬ TRỰC TIẾP TRÊN WINDOWS (KHÔNG CẦN THƯ VIỆN NGOÀI)
# ------------------------------------------------------------------
def play_wav_async(wav_path: str | Path) -> bool:
    """Phát file WAV bất đồng bộ trên Windows bằng `winsound`."""
    p = Path(wav_path)
    if not p.is_file():
        return False
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(None, winsound.SND_PURGE)
        winsound.PlaySound(str(p), winsound.SND_FILENAME | winsound.SND_ASYNC)
        return True
    return False


def stop_wav_playback() -> None:
    """Dừng phát âm thanh nghe thử hiện tại."""
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(None, winsound.SND_PURGE)
