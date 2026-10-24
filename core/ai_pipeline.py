"""
Điều phối quy trình 3 bước tạo video bằng AI:
  - Bước 1 (Planner): Chủ đề -> Kịch bản JSON & bản nháp Tiếng Việt để người dùng duyệt/sửa
  - Bước 2 (Coder)  : Kịch bản đã duyệt -> Sinh file `scene.py` chuẩn ManimGL & kiểm định bố cục tự động
  - Bước 3 (Runner) : Đảm bảo vượt qua `layout_auditor` + Render `.mp4` + Tự vá lỗi (Self-Healing)
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import unicodedata
from typing import Any, Callable

from .gemini_service import GeminiResult, GeminiService
from .layout_auditor import audit_scene_file
from .prompt_builder import (
    build_coder_prompts,
    build_fixer_prompts,
    build_planner_prompts,
    format_plan_to_review_text,
    parse_duration_from_topic,
)
from .tts_service import (
    DEFAULT_TTS_VOICE,
    ScriptAudioPack,
    VieNeuTTSService,
    mux_scene_audio_into_video,
)

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECTS_DIR = BASE_DIR / "projects"
VIDEOS_DIR = BASE_DIR / "videos"


def slugify_topic(topic: str, max_len: int = 42) -> str:
    """Chuyển tiêu đề Tiếng Việt thành slug tên thư mục/file an toàn."""
    s = (topic or "bai_giang_moi").strip()
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.lower()).strip("_")
    if not s:
        s = "bai_giang_moi"
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s


def slug_to_scene_class(slug: str) -> str:
    """Chuyển slug thành tên class PascalCase hợp lệ kết thúc bằng Scene."""
    parts = [p for p in slug.split("_") if p and not p.isdigit()]
    if not parts:
        parts = ["GeneratedLesson"]
    pascal = "".join(p.capitalize() for p in parts[:6])
    if pascal[0].isdigit():
        pascal = "Lesson" + pascal
    if not pascal.endswith("Scene"):
        pascal += "Scene"
    return pascal


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Bóc tách đối tượng JSON từ phản hồi của LLM."""
    cleaned = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.S)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def extract_python_code(raw_text: str) -> str:
    """Bóc tách mã nguồn Python sạch từ phản hồi của LLM."""
    cleaned = raw_text.strip()
    fence_matches = re.findall(r"```(?:python|py)?\s*\n(.*?)```", cleaned, flags=re.S)
    if fence_matches:
        cleaned = max(fence_matches, key=len).strip()
    elif cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    return cleaned + "\n"


def parse_scenes_from_file(filepath: str | Path) -> list[str]:
    """Tìm tên các class kế thừa Scene trong file Python bằng AST."""
    scenes: list[str] = []
    p = Path(filepath)
    if not p.is_file():
        return scenes
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"), filename=str(p))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                base_names = []
                for b in node.bases:
                    if isinstance(b, ast.Name):
                        base_names.append(b.id)
                    elif isinstance(b, ast.Attribute):
                        base_names.append(b.attr)
                if any("Scene" in b for b in base_names) or node.name.endswith(("Scene", "Tutorial")):
                    scenes.append(node.name)
        if not scenes:
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name != "StickmanTeacher":
                    scenes.append(node.name)
    except Exception:
        pass
    return scenes


@dataclass
class PlanSession:
    topic: str
    slug: str
    scene_class_name: str
    style_mode: str
    duration_sec: int
    project_dir: Path
    script_json_path: Path
    review_md_path: Path
    plan_data: dict[str, Any]
    review_text: str
    gemini_result: GeminiResult
    aspect_ratio: str = "16:9" 


@dataclass
class CodeSession:
    slug: str
    scene_class_name: str
    project_dir: Path
    scene_py_path: Path
    approved_script_path: Path
    code: str
    gemini_result: GeminiResult
    fix_tokens_used: int = 0
    audit_passed: bool = False
    audio_pack: ScriptAudioPack | None = None
    scene_cut_times: list[float] = field(default_factory=list)
    header_times: list[float] = field(default_factory=list)
    virtual_duration: float = 0.0
    aspect_ratio: str = "16:9" 


class AIPipeline:
    def __init__(self, gemini: GeminiService):
        self.gemini = gemini
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # BƯỚC 1: LẬP KỊCH BẢN PHÂN CẢNH (CHƯA VIẾT CODE)
    # ------------------------------------------------------------------
    def generate_plan(
        self,
        topic: str,
        duration_sec: int | None = None,
        style_mode: str = "channel_dark",
        aspect_ratio: str = "16:9",
        on_log: Callable[[str], None] | None = None,
    ) -> PlanSession:
        log = on_log or (lambda _msg: None)
        final_duration = parse_duration_from_topic(topic, fallback_sec=duration_sec or 45)
        slug = slugify_topic(topic)
        scene_class_name = slug_to_scene_class(slug)
        project_dir = PROJECTS_DIR / slug
        project_dir.mkdir(parents=True, exist_ok=True)

        log(f"📝 [Bước 1] Đang phân tích chủ đề: \"{topic}\"\n")
        log(f"   • Thời lượng mục tiêu: {final_duration} giây | Phong cách: {style_mode}\n")
        log(f"   • Thư mục dự án: projects/{slug}/\n")
        log(f"   • Đang gọi Gemini ({self.gemini.model}) lập kịch bản phân cảnh...\n")

        sys_inst, usr_prompt = build_planner_prompts(
            topic=topic,
            duration_sec=final_duration,
            style_mode=style_mode,
            aspect_ratio=aspect_ratio,
        )
        res = self.gemini.generate(
            system_instruction=sys_inst,
            user_prompt=usr_prompt,
            temperature=0.3,
            json_output=True,
        )

        try:
            plan_data = extract_json_object(res.text)
        except Exception:
            plan_data = {
                "topic": topic,
                "style_mode": style_mode,
                "target_duration_sec": final_duration,
                "color_contract": {"primary": "Khái niệm chính", "highlight": "Điểm nhấn"},
                "scenes": [],
            }
            review_text = res.text
        else:
            plan_data.setdefault("topic", topic)
            plan_data.setdefault("style_mode", style_mode)
            plan_data.setdefault("target_duration_sec", final_duration)
            review_text = format_plan_to_review_text(plan_data)

        script_json_path = project_dir / "script.json"
        review_md_path = project_dir / "script_review.md"
        script_json_path.write_text(
            json.dumps(plan_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        review_md_path.write_text(review_text, encoding="utf-8")

        log(
            f"✅ [Bước 1 Hoàn tất] Đã tạo kịch bản! "
            f"(Token tiêu thụ: {res.total_tokens:,} = {res.prompt_tokens:,} in + {res.output_tokens:,} out)\n"
        )
        log("👉 Mời bạn xem và chỉnh sửa trực tiếp kịch bản ở khung bên trên trước khi bấm Sinh Code.\n")

        return PlanSession(
            topic=topic,
            slug=slug,
            scene_class_name=scene_class_name,
            style_mode=plan_data.get("style_mode", style_mode),
            duration_sec=int(plan_data.get("target_duration_sec", final_duration)),
            project_dir=project_dir,
            script_json_path=script_json_path,
            review_md_path=review_md_path,
            plan_data=plan_data,
            review_text=review_text,
            gemini_result=res,
            aspect_ratio=plan_data.get("aspect_ratio", aspect_ratio),
        )

    # ------------------------------------------------------------------
    # BƯỚC 2: SINH MÃ NGUỒN MANIMGL + KIỂM ĐỊNH BỐ CỤC TỰ ĐỘNG
    # ------------------------------------------------------------------
    def generate_code_from_approved_script(
        self,
        approved_script_text: str,
        slug: str,
        scene_class_name: str,
        duration_sec: int = 45,
        style_mode: str = "channel_dark",
        aspect_ratio: str = "16:9",
        auto_fix_layout: bool = True,
        max_layout_retries: int = 4,
        tts_enabled: bool = True,
        tts_voice: str = DEFAULT_TTS_VOICE,
        tts_speed: float = 1.0,
        stop_event: threading.Event | None = None,
        on_log: Callable[[str], None] | None = None,
    ) -> CodeSession:
        log = on_log or (lambda _msg: None)
        project_dir = PROJECTS_DIR / slug
        project_dir.mkdir(parents=True, exist_ok=True)

        approved_path = project_dir / "script_approved.md"
        approved_path.write_text(approved_script_text, encoding="utf-8")

        audio_pack: ScriptAudioPack | None = None
        scene_durations: list[float] | None = None
        if tts_enabled and not (stop_event and stop_event.is_set()):
            try:
                audio_pack = VieNeuTTSService.get_instance().synthesize_script_scenes(
                    script_text=approved_script_text,
                    project_dir=project_dir,
                    voice=tts_voice,
                    speed=tts_speed,
                    stop_event=stop_event,
                    on_log=log,
                )
                if audio_pack:
                    scene_durations = audio_pack.target_scene_durations()
            except Exception as tts_err:
                log(f"⚠️ Không thể thu âm trước ở Bước 2 ({tts_err}), sẽ tiếp tục sinh code bình thường.\n")

        log(f"\n💻 [Bước 2] Đang gọi Gemini ({self.gemini.model}) viết code ManimGL cho `{scene_class_name}`...\n")
        sys_inst, usr_prompt = build_coder_prompts(
            approved_script_text=approved_script_text,
            scene_class_name=scene_class_name,
            duration_sec=duration_sec,
            style_mode=style_mode,
            scene_durations=scene_durations,
            aspect_ratio=aspect_ratio,
        )
        res = self.gemini.generate(
            system_instruction=sys_inst,
            user_prompt=usr_prompt,
            temperature=0.2,
            json_output=False,
        )
        code = extract_python_code(res.text)
        fix_tokens = 0

        # 2.1. Kiểm tra cú pháp AST
        try:
            ast.parse(code)
        except SyntaxError as syn_err:
            log(f"⚠️ Phát hiện lỗi cú pháp Python ({syn_err}), đang tự động chỉnh lại...\n")
            fix_sys, fix_usr = build_fixer_prompts(
                broken_code=code,
                error_traceback=f"SyntaxError: {syn_err}",
                scene_class_name=scene_class_name,
            )
            fix_res = self.gemini.generate(fix_sys, fix_usr, temperature=0.1)
            code = extract_python_code(fix_res.text)
            fix_tokens += fix_res.total_tokens

        scene_py_path = project_dir / "scene.py"
        scene_py_path.write_text(code, encoding="utf-8")

        detected_scenes = parse_scenes_from_file(scene_py_path)
        actual_scene_name = (
            scene_class_name
            if scene_class_name in detected_scenes
            else (detected_scenes[0] if detected_scenes else scene_class_name)
        )

        # 2.2. Kiểm định Bố cục, Tràn viền, Đè chữ & Mũi tên tự động (trước khi render MP4)
        audit_passed = False
        last_cut_times: list[float] = []
        last_hdr_times: list[float] = []
        last_virt_dur: float = 0.0
        if auto_fix_layout and max_layout_retries >= 0:
            for check_idx in range(1, max_layout_retries + 2):
                if stop_event and stop_event.is_set():
                    break
                log(f"🔍 Đang kiểm tra tự động bố cục, tràn viền & đè chữ (Lần {check_idx})...\n")
                audit = audit_scene_file(scene_py_path, actual_scene_name, aspect_ratio=aspect_ratio)
                if audit.virtual_duration > 0:
                    last_cut_times = audit.scene_cut_times
                    last_hdr_times = audit.header_times
                    last_virt_dur = audit.virtual_duration
                if audit.ok:
                    audit_passed = True
                    log("✅ Kiểm định bố cục đạt chuẩn: Không lỗi API, không tràn lề, không đè chữ/mũi tên!\n")
                    break

                if audit.runtime_error:
                    err_lines = audit.runtime_error.strip().splitlines()
                    log("⚠️ Phát hiện lỗi thực thi khi chạy thử Scene:\n")
                    log(f"   {err_lines[-1] if err_lines else audit.runtime_error}\n")
                else:
                    log(f"⚠️ Phát hiện {len(audit.layout_issues)} lỗi bố cục (tràn viền / đè chữ / mũi tên cắt hình):\n")
                    for issue in audit.layout_issues[:6]:
                        log(f"   • {issue}\n")

                if check_idx > max_layout_retries:
                    log("⚠️ Đã dùng hết lượt căn chỉnh ở Bước 2; Bước 3 sẽ tiếp tục kiểm tra & sửa trước khi xuất MP4.\n")
                    break

                log(f"🔧 Đang gọi Gemini Fixer tự động sửa lỗi & căn chỉnh bố cục ({check_idx}/{max_layout_retries})...\n")
                fix_sys, fix_usr = build_fixer_prompts(
                    broken_code=code,
                    error_traceback=audit.format_for_fixer(),
                    scene_class_name=actual_scene_name,
                    aspect_ratio=aspect_ratio,
                )
                fix_res = self.gemini.generate(fix_sys, fix_usr, temperature=0.15)
                code = extract_python_code(fix_res.text)
                fix_tokens += fix_res.total_tokens
                scene_py_path.write_text(code, encoding="utf-8")

                detected_scenes = parse_scenes_from_file(scene_py_path)
                if detected_scenes and actual_scene_name not in detected_scenes:
                    actual_scene_name = detected_scenes[0]

        log(
            f"✅ [Bước 2 Hoàn tất] Đã lưu mã nguồn tại: projects/{slug}/scene.py\n"
            f"   • Scene class: `{actual_scene_name}` | "
            f"Tổng token Bước 2: {res.total_tokens + fix_tokens:,}\n"
        )

        return CodeSession(
            slug=slug,
            scene_class_name=actual_scene_name,
            project_dir=project_dir,
            scene_py_path=scene_py_path,
            approved_script_path=approved_path,
            code=code,
            gemini_result=res,
            fix_tokens_used=fix_tokens,
            audit_passed=audit_passed,
            audio_pack=audio_pack,
            scene_cut_times=last_cut_times,
            header_times=last_hdr_times,
            virtual_duration=last_virt_dur,
            aspect_ratio=aspect_ratio,
        )

    # ------------------------------------------------------------------
    # BƯỚC 3: RENDER VIDEO & VÒNG LẶP TỰ SỬA LỖI (LUÔN QUA LAYOUT AUDITOR)
    # ------------------------------------------------------------------
    def render_with_self_healing(
        self,
        code_session: CodeSession,
        resolution_flag: str = "-l",
        aspect_ratio: str | None = None,
        open_after: bool = True,
        max_fix_retries: int = 3,
        tts_enabled: bool = True,
        tts_voice: str = DEFAULT_TTS_VOICE,
        tts_speed: float = 1.0,
        script_text: str | None = None,
        stop_event: threading.Event | None = None,
        on_process_created: Callable[[subprocess.Popen], None] | None = None,
        on_log: Callable[[str], None] | None = None,
    ) -> tuple[bool, Path | None]:
        log = on_log or (lambda _msg: None)
        scene_path = code_session.scene_py_path
        current_code = (
            scene_path.read_text(encoding="utf-8")
            if scene_path.is_file()
            else code_session.code
        )
        scene_name = code_session.scene_class_name
        output_file_stem = code_session.slug
        eff_aspect_ratio = aspect_ratio or getattr(code_session, "aspect_ratio", "16:9")
        is_vertical = (eff_aspect_ratio == "9:16") or ("vertical" in str(eff_aspect_ratio).lower())

        # Nếu file chưa được duyệt qua layout_auditor (hoặc vừa bị chỉnh sửa tay), bắt buộc kiểm định trước khi xuất MP4
        verified_clean = bool(code_session.audit_passed and current_code == code_session.code)

        attempt = 0
        total_attempts = 1 + max(0, max_fix_retries)

        while attempt < total_attempts:
            if stop_event and stop_event.is_set():
                log("\n⏹️ Tiến trình đã dừng theo yêu cầu người dùng.\n")
                return False, None

            attempt += 1

            # 3.1. Chốt chặn Kiểm định Bố cục trước khi gọi manimlib -w xuất MP4
            if not verified_clean:
                log(f"\n🔍 [Bước 3 - Kiểm định {attempt}/{total_attempts}] Đang rà soát lỗi thực thi & đè chữ trước khi xuất MP4...\n")
                audit = audit_scene_file(scene_path, scene_name, aspect_ratio=eff_aspect_ratio)
                if audit.virtual_duration > 0:
                    code_session.scene_cut_times = audit.scene_cut_times
                    code_session.header_times = audit.header_times
                    code_session.virtual_duration = audit.virtual_duration
                if audit.ok:
                    verified_clean = True
                    log("✅ Kiểm định bố cục đạt chuẩn! Bắt đầu kết xuất video MP4...\n")
                else:
                    if audit.runtime_error:
                        err_lines = audit.runtime_error.strip().splitlines()
                        log(f"⚠️ Phát hiện lỗi thực thi: {err_lines[-1] if err_lines else audit.runtime_error}\n")
                    else:
                        log(f"⚠️ Phát hiện {len(audit.layout_issues)} lỗi đè chữ / tràn viền cần sửa trước khi xuất video:\n")
                        for issue in audit.layout_issues[:6]:
                            log(f"   • {issue}\n")

                    if attempt < total_attempts:
                        log(f"🔧 [Self-Healing {attempt}/{max_fix_retries}] Đang gửi báo cáo cho Gemini Fixer tự động sửa code...\n")
                        fix_sys, fix_usr = build_fixer_prompts(
                            broken_code=current_code,
                            error_traceback=audit.format_for_fixer(),
                            scene_class_name=scene_name,
                            aspect_ratio=eff_aspect_ratio,
                        )
                        fix_res = self.gemini.generate(
                            system_instruction=fix_sys,
                            user_prompt=fix_usr,
                            temperature=0.15,
                            json_output=False,
                        )
                        current_code = extract_python_code(fix_res.text)
                        scene_path.write_text(current_code, encoding="utf-8")

                        detected = parse_scenes_from_file(scene_path)
                        if detected and scene_name not in detected:
                            scene_name = detected[0]

                        log(
                            f"✅ Đã cập nhật bản vá vào `projects/{code_session.slug}/scene.py` "
                            f"(Token sửa lỗi: {fix_res.total_tokens:,}). Đang kiểm định lại...\n"
                        )
                        continue
                    else:
                        log("🛡️ Đã hết lượt Gemini Fixer. Hệ thống Auto-Framer Guard tại `style.py` sẽ tự động bảo vệ khung hình khi render!\n")

            log(f"\n🎬 [Bước 3] Đang chạy ManimGL xuất video MP4 (Lần {attempt}/{total_attempts})...\n")

            cmd = [
                sys.executable,
                "-m",
                "manimlib",
                str(scene_path),
                scene_name,
                "-w",
                resolution_flag,
            ]
            if is_vertical and not resolution_flag.startswith("-r"):
                cmd.append("--vertical")
            cmd.extend([
                "--video_dir",
                str(VIDEOS_DIR),
                "--file_name",
                output_file_stem,
            ])
            # Không truyền -o cho manimlib khi bật TTS để tránh trình phát khóa file trước lúc ghép âm thanh
            if open_after and not tts_enabled:
                cmd.append("-o")

            log(f"   Lệnh: {' '.join(cmd)}\n\n")

            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            proc = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creation_flags,
            )
            if on_process_created:
                on_process_created(proc)

            captured_lines: list[str] = []
            assert proc.stdout is not None
            for line in iter(proc.stdout.readline, ""):
                if line:
                    captured_lines.append(line)
                    log(line)
                if stop_event and stop_event.is_set():
                    proc.terminate()
                    break

            proc.stdout.close()
            rc = proc.wait()

            full_output = "".join(captured_lines)
            (code_session.project_dir / "render.log").write_text(full_output, encoding="utf-8")

            if stop_event and stop_event.is_set():
                return False, None

            if rc == 0:
                mp4_path = VIDEOS_DIR / f"{output_file_stem}.mp4"
                code_session.code = current_code
                code_session.audit_passed = True
                if mp4_path.is_file():
                    # Lưu bản gốc hình ảnh thuần ManimGL để có thể đổi giọng đọc / lồng tiếng lại bất kỳ lúc nào
                    raw_visual_backup = code_session.project_dir / "raw_visual.mp4"
                    try:
                        shutil.copy2(mp4_path, raw_visual_backup)
                    except Exception:
                        raw_visual_backup = mp4_path

                    if tts_enabled and not (stop_event and stop_event.is_set()):
                        try:
                            pack = code_session.audio_pack
                            if (
                                pack is None
                                or pack.voice != tts_voice
                                or abs(pack.speed - tts_speed) > 0.02
                            ):
                                eff_script = script_text or ""
                                if not eff_script and code_session.approved_script_path.is_file():
                                    eff_script = code_session.approved_script_path.read_text(encoding="utf-8")
                                if eff_script:
                                    pack = VieNeuTTSService.get_instance().synthesize_script_scenes(
                                        script_text=eff_script,
                                        project_dir=code_session.project_dir,
                                        voice=tts_voice,
                                        speed=tts_speed,
                                        stop_event=stop_event,
                                        on_log=log,
                                    )
                                    code_session.audio_pack = pack

                            if pack and pack.clips:
                                if code_session.virtual_duration <= 0.1:
                                    timing_probe = audit_scene_file(scene_path, scene_name)
                                    code_session.scene_cut_times = timing_probe.scene_cut_times
                                    code_session.header_times = timing_probe.header_times
                                    code_session.virtual_duration = timing_probe.virtual_duration

                                mp4_path = mux_scene_audio_into_video(
                                    video_path=raw_visual_backup,
                                    audio_pack=pack,
                                    output_video_path=mp4_path,
                                    cut_times=code_session.scene_cut_times,
                                    header_times=code_session.header_times,
                                    virtual_duration=code_session.virtual_duration,
                                    on_log=log,
                                )
                        except Exception as mux_err:
                            log(f"⚠️ Lỗi khi lồng tiếng vào MP4 ({mux_err}); vẫn giữ bản video hình ảnh chuẩn.\n")

                    log("\n🎉 HOÀN TẤT VIDEO THÀNH CÔNG!\n")
                    log(f"📁 File video: {mp4_path}\n")
                    if open_after and tts_enabled:
                        _open_file_default(mp4_path)
                    return True, mp4_path

                log("\n🎉 HOÀN TẤT VIDEO THÀNH CÔNG!\n")
                return True, VIDEOS_DIR

            log(f"\n⚠️ Render gặp lỗi (mã thoát {rc}).\n")
            if attempt >= total_attempts:
                log("❌ Đã hết số lần tự động sửa lỗi. Bạn có thể xem chi tiết ở log trên hoặc chỉnh `scene.py`.\n")
                return False, None

            log(f"🔧 [Self-Healing {attempt}/{max_fix_retries}] Đang gửi Traceback cho Gemini Fixer tự động sửa code...\n")
            fix_sys, fix_usr = build_fixer_prompts(
                broken_code=current_code,
                error_traceback=full_output,
                scene_class_name=scene_name,
                aspect_ratio=eff_aspect_ratio,
            )
            fix_res = self.gemini.generate(
                system_instruction=fix_sys,
                user_prompt=fix_usr,
                temperature=0.15,
                json_output=False,
            )
            current_code = extract_python_code(fix_res.text)
            scene_path.write_text(current_code, encoding="utf-8")
            verified_clean = False  # Bắt buộc chạy lại layout_auditor sau khi sửa code!

            detected = parse_scenes_from_file(scene_path)
            if detected and scene_name not in detected:
                scene_name = detected[0]

            log(
                f"✅ Đã cập nhật bản vá vào `projects/{code_session.slug}/scene.py` "
                f"(Token sửa lỗi: {fix_res.total_tokens:,}). Chuẩn bị kiểm định & render lại...\n"
            )

        return False, None


def _open_file_default(file_path: Path) -> None:
    if not file_path.is_file():
        return
    try:
        if sys.platform == "win32":
            os.startfile(str(file_path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(file_path)])
        else:
            subprocess.Popen(["xdg-open", str(file_path)])
    except Exception:
        pass


def revoice_project_video(
    slug: str,
    script_text: str,
    voice: str = DEFAULT_TTS_VOICE,
    speed: float = 1.0,
    open_after: bool = True,
    stop_event: threading.Event | None = None,
    on_log: Callable[[str], None] | None = None,
) -> Path | None:
    """
    Lồng tiếng mới (100% Offline bằng VieNeu-TTS) vào video `.mp4` đã render sẵn của dự án `slug`
    mà KHÔNG cần gọi lại Gemini API hay render lại ManimGL!
    """
    log = on_log or (lambda _msg: None)
    project_dir = PROJECTS_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    target_mp4 = VIDEOS_DIR / f"{slug}.mp4"
    raw_visual = project_dir / "raw_visual.mp4"

    if not raw_visual.is_file():
        if not target_mp4.is_file():
            raise FileNotFoundError(
                f"Chưa tìm thấy video `videos/{slug}.mp4`! Hãy bấm '🎬 Duyệt & Tạo Video' ít nhất 1 lần trước."
            )
        # Lưu bản sao sạch lần đầu từ target_mp4
        try:
            shutil.copy2(target_mp4, raw_visual)
        except Exception:
            raw_visual = target_mp4

    pack = VieNeuTTSService.get_instance().synthesize_script_scenes(
        script_text=script_text,
        project_dir=project_dir,
        voice=voice,
        speed=speed,
        stop_event=stop_event,
        on_log=log,
    )
    if not pack or not pack.clips:
        return None
    if stop_event and stop_event.is_set():
        return None

    cut_times: list[float] = []
    hdr_times: list[float] = []
    virt_dur: float = 0.0
    scene_py = project_dir / "scene.py"
    if scene_py.is_file():
        scenes = parse_scenes_from_file(scene_py)
        if scenes:
            probe = audit_scene_file(scene_py, scenes[0])
            cut_times = probe.scene_cut_times
            hdr_times = probe.header_times
            virt_dur = probe.virtual_duration

    final_mp4 = mux_scene_audio_into_video(
        video_path=raw_visual,
        audio_pack=pack,
        output_video_path=target_mp4,
        cut_times=cut_times,
        header_times=hdr_times,
        virtual_duration=virt_dur,
        on_log=log,
    )
    if open_after and final_mp4.is_file():
        _open_file_default(final_mp4)
    return final_mp4

