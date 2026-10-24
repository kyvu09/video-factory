"""
Bộ nạp và lắp ghép System Prompt từ thư mục `references/` cho Gemini API.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
REF_DIR = BASE_DIR / "references"


def _read_ref(filename: str) -> str:
    path = REF_DIR / filename
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_skill_section(marker: str) -> str:
    """Trích xuất một khối `[PROMPT X: ...]` từ `references/ai-animation-skill.md`."""
    full_text = _read_ref("ai-animation-skill.md")
    if not full_text:
        return ""
    pattern = rf"(## \[{re.escape(marker)}\].*?)(?=\n## \[PROMPT |\Z)"
    m = re.search(pattern, full_text, flags=re.S)
    return m.group(1).strip() if m else full_text


def parse_duration_from_topic(topic: str, fallback_sec: int = 45) -> int:
    """
    Tự động nhận diện thời lượng nếu người dùng ghi trực tiếp trong chủ đề.
    Ví dụ: 'Giải thích Định lý Pytago trong 45 giây' -> 45
           'Tìm kiếm nhị phân 2 phút' -> 120
    """
    if not topic:
        return fallback_sec

    m_min = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:phút|phut|mins?|minutes?)\b", topic, flags=re.I)
    if m_min:
        val = float(m_min.group(1).replace(",", "."))
        sec = int(round(val * 60))
        return max(15, min(sec, 300))

    m_sec = re.search(r"(\d{2,3})\s*(?:giây|giay|secs?|seconds?|s)\b", topic, flags=re.I)
    if m_sec:
        sec = int(m_sec.group(1))
        return max(15, min(sec, 300))

    return fallback_sec


def build_planner_prompts(topic: str, duration_sec: int, style_mode: str) -> tuple[str, str]:
    """Ghép (system_instruction, user_prompt) cho Bước 1: Lập Kịch Bản."""
    planner_rules = _extract_skill_section("PROMPT 1: PLANNER")
    storytelling = _read_ref("storytelling.md")
    project_sdk = _read_ref("project-sdk.md")

    chunk_count = max(2, int(round(duration_sec / 15.0)))
    style_desc = (
        "channel_dark — Kế thừa `ChannelScene` (nền tối hiện đại `#0A0F1E`, bảng màu `STYLE`)"
        if style_mode == "channel_dark"
        else "teacher_light — Bảng sáng `#F8FAFC` có nhân vật thầy giáo `StickmanTeacher` cầm que chỉ bảng"
    )

    system_instruction = f"""{planner_rules}

---
{storytelling}

---
{project_sdk}

QUAN TRỌNG: Chỉ trả về DUY NHẤT một đối tượng JSON hợp lệ theo đúng cấu trúc mẫu (không kèm markdown giải thích bên ngoài).
"""

    user_prompt = f"""Hãy thiết kế kịch bản video hoạt ảnh giáo dục chi tiết, giàu tính điện ảnh cho yêu cầu sau:
- Chủ đề / Yêu cầu: {topic}
- Thời lượng mục tiêu: {duration_sec} giây (chia thành khoảng {chunk_count} phân cảnh nối tiếp theo cấu trúc 3 hồi Hook -> Build -> Resolution)
- Phong cách trình bày (`style_mode`): {style_desc}

Yêu cầu bắt buộc về BỐ CỤC CÂN ĐỐI & CHUYỂN ĐỘNG SỐNG ĐỘNG:
1. Mỗi phân cảnh phải chỉ định rõ `layout_mode` là `"center_focus"` hoặc `"two_columns"`, đảm bảo lấp đầy cân đối khung hình (không để một góc trống trải hoặc một cột quá bé so với cột kia).
2. TUYỆT ĐỐI KHÔNG giữ nguyên hình minh họa cũ ở giữa màn hình rồi cho hiện công thức/tiêu đề mới đè lên giữa màn hình!
   - Khi sang phân cảnh mới: Hoặc xóa sạch phân cảnh trước (`clear_stage`), hoặc tách cân xứng Cột Trái (`x = -3.35`) và Cột Phải (`x = +3.35`).
   - Nếu có bảng mảng / bảng băm: chỉ thiết kế gọn 4–6 ô thoáng mắt.
3. Trong `visual_steps`, hãy thiết kế hiệu ứng chuyển động mượt mà như 3Blue1Brown (hạt sáng di chuyển minh họa, mũi tên mọc `GrowArrow`, dữ liệu/con số bay theo cung tròn vào ô nhớ `TransformFromCopy`, tia sáng neon chạy viền nhấn mạnh `FlashAround`, nhãn pill `make_badge`) thay vì chỉ hiện chữ tĩnh.
4. Trong trường `narration_vi` của mỗi phân cảnh: Viết lời thuyết minh Tiếng Việt mạch lạc, truyền cảm, tự nhiên như người dẫn chương trình để đưa trực tiếp vào bộ đọc giọng AI (`VieNeu-TTS`). TUYỆT ĐỐI KHÔNG viết ký hiệu LaTeX thô (`\\frac`, `\\sqrt`, `\\to`, `dp[i-1]`) trong `narration_vi` — hãy viết phiên âm lời nói tự nhiên (ví dụ: "a bình cộng b bình bằng c bình", "độ phức tạp O N", "giá trị tại bậc i bằng tổng hai bậc liền trước").
5. Trả về JSON hợp lệ với đầy đủ các trường: `topic`, `style_mode`, `target_duration_sec`, `color_contract`, `scenes`.
"""
    return system_instruction, user_prompt


def format_plan_to_review_text(plan: dict[str, Any]) -> str:
    """
    Chuyển đối tượng JSON kịch bản ở Bước 1 thành văn bản Tiếng Việt rõ ràng,
    dễ đọc và dễ chỉnh sửa trực tiếp trên giao diện trước khi sinh code.
    """
    topic = plan.get("topic", "Bài giảng mới")
    style_mode = plan.get("style_mode", "channel_dark")
    duration = plan.get("target_duration_sec", 45)
    style_label = (
        "Nền tối hiện đại (ChannelScene)"
        if style_mode == "channel_dark"
        else "Bảng trắng + Thầy giáo Stickman (StickmanTeacher)"
    )

    lines: list[str] = [
        f"# KỊCH BẢN VIDEO: {topic}",
        f"- Phong cách ({style_mode}): {style_label}",
        f"- Thời lượng mục tiêu: {duration} giây",
        "",
        "## Quy ước màu sắc (Color Contract)",
    ]

    color_contract = plan.get("color_contract") or {}
    if isinstance(color_contract, dict) and color_contract:
        for k, v in color_contract.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- primary: Khái niệm / đối tượng chính")
        lines.append("- highlight: Ý nhấn mạnh / kết quả quan trọng")

    scenes = plan.get("scenes") or []
    for idx, sc in enumerate(scenes, start=1):
        role = sc.get("role", "Build")
        layout_mode = sc.get("layout_mode", "center_focus")
        dur = sc.get("duration_sec", 15)
        concept = sc.get("concept", "")
        lines.append("")
        lines.append("---")
        lines.append(
            f"### Phân cảnh {sc.get('index', idx)} [{role} | Bố cục: {layout_mode}] ({dur} giây) — {concept}"
        )

        v_steps = sc.get("visual_steps") or []
        if v_steps:
            lines.append("- Diễn hoạt hình ảnh:")
            for step in v_steps:
                lines.append(f"  + {step}")

        texts = sc.get("on_screen_texts") or []
        if texts:
            lines.append("- Chữ hiển thị (Tiếng Việt):")
            for t in texts:
                lines.append(f'  + "{t}"')

        formulas = sc.get("latex_formulas") or []
        if formulas:
            lines.append("- Công thức Toán (LaTeX):")
            for f in formulas:
                lines.append(f"  + {f}")

        narration = sc.get("narration_vi", "").strip()
        if narration:
            lines.append(f"- Lời dẫn / Ý giảng: {narration}")

    lines.append("")
    lines.append("---")
    lines.append("# Ghi chú chỉnh sửa thêm của bạn (nếu có):")
    lines.append("# (Bạn có thể sửa trực tiếp mọi chữ/số liệu ở trên hoặc viết thêm yêu cầu tại đây trước khi bấm Sinh Code)")
    return "\n".join(lines)


def build_coder_prompts(
    approved_script_text: str,
    scene_class_name: str,
    duration_sec: int,
    style_mode: str,
    scene_durations: list[float] | None = None,
) -> tuple[str, str]:
    """Ghép (system_instruction, user_prompt) cho Bước 2: Sinh Code ManimGL."""
    coder_rules = _extract_skill_section("PROMPT 2: CODER")
    manim_api = _read_ref("manim-gl-api.md")
    project_sdk = _read_ref("project-sdk.md")
    math_recipes = _read_ref("math-visual-recipes.md")

    system_instruction = f"""{coder_rules}

---
{project_sdk}

---
{manim_api}

---
{math_recipes}

QUAN TRỌNG:
- Chỉ trả về DUY NHẤT mã nguồn Python hợp lệ (không viết lời giải thích ngoài code).
- Toàn bộ bài giảng được viết gọn trong MỘT class Scene duy nhất tên là `{scene_class_name}` nối tiếp mượt mà giữa các phân cảnh.
"""

    if style_mode == "teacher_light":
        style_hint = (
            f"Sử dụng phong cách Bảng sáng + Thầy giáo Stickman:\n"
            f"- Kế thừa `Scene`, đặt `default_camera_config = {{\"background_color\": \"#F8FAFC\"}}`.\n"
            f"- Import `from components import StickmanTeacher, RightAngle`.\n"
            f"- Đặt nhân vật `teacher = StickmanTeacher()` bên trái (`x ≈ -4.8`) và toàn bộ hình/chữ bên phải bảng (`x in [-1.8, 5.8]`, `y in [-3.2, 3.0]`)."
        )
    else:
        style_hint = (
            f"Sử dụng phong cách Motion Design Studio hiện đại của kênh (`ChannelScene` v2):\n"
            f"- Import `from style import STYLE, ChannelScene` (và `from components import RightAngle` nếu vẽ góc vuông).\n"
            f"- Class `{scene_class_name}(ChannelScene)` sử dụng hệ thống bố cục đầy đặn & hiệu ứng chuyển động mượt:\n"
            f"  + `self.place_header(title, subtitle)` cho tiêu đề gradient trên cùng; `self.place_footer(caption)` cho thanh pill chú thích dưới đáy.\n"
            f"  + `self.make_box(content, color=...)` cho hộp chữ/công thức; `self.make_badge(text, color=...)` cho nhãn pill độ phức tạp/trạng thái; `self.make_arrow(start, end, color=..., path_arc=...)` cho mũi tên.\n"
            f"  + `self.fit_text_in(text_mob, slot)` khi đặt chữ vào bên trong ô bảng / mảng.\n"
            f"  + Gom TẤT CẢ phần tử của vùng/cột vào 1 `VGroup` rồi gọi `self.fit_in_center_zone(group)` hoặc `self.fit_in_left_zone(left_col)` / `self.fit_in_right_zone(right_col)` để tự động phóng/thu cân đối lấp ~84% khung hình.\n"
            f"  + Chuyển động mượt & sống động: `GrowArrow(arr)` cho mũi tên, `self.morph_text_anim(old_txt, new_txt)` hoặc `FadeTransform(old_txt, new_txt, stretch=False)` khi đổi chữ/số (CẤM dùng `Transform` trên `Text`!), `self.pop_in(card)`, `self.stagger_in(group)`, `self.flow_to(src, dst)` (`TransformFromCopy`), `self.pulse_focus(mob)` (`FlashAround`), và `self.clear_stage()` khi sang cảnh mới."
        )

    timing_block = ""
    if scene_durations:
        per_scene_lines = "\n".join(
            f"  + Phân cảnh {idx}: tổng `run_time` + `self.wait(...)` phải đạt khoảng {dur:.1f} giây"
            for idx, dur in enumerate(scene_durations, start=1)
        )
        total_audio_target = round(sum(scene_durations), 1)
        duration_sec = max(duration_sec, int(round(total_audio_target)))
        timing_block = (
            f"\n- ĐỒNG BỘ GIỌNG THUYẾT MINH AI (AUDIO-FIRST SYNC — RẤT QUAN TRỌNG):\n"
            f"  Hệ thống VieNeu-TTS đã thu âm xong lời giảng thực tế cho từng phân cảnh (tổng ~{total_audio_target}s).\n"
            f"  Hãy canh nhịp `run_time` và `self.wait(...)` trong từng phân cảnh khớp sát thời lượng sau để hình và tiếng đi cùng nhau mượt mà:\n"
            f"{per_scene_lines}\n"
        )

    user_prompt = f"""Hãy viết mã nguồn ManimGL 1.7+ hoàn chỉnh, bố cục cân đối đầy đặn và hiệu ứng chuyển động mượt đẹp mắt cho kịch bản đã duyệt dưới đây:

- Tên class bắt buộc: `{scene_class_name}`
- Tổng thời lượng mục tiêu (`sum(run_time) + sum(self.wait)`): khoảng {duration_sec} giây{timing_block}
- Yêu cầu phong cách, bố cục & chuyển động:
{style_hint}

=== KỊCH BẢN ĐÃ DUYỆT ===
{approved_script_text}
=========================

6 QUY TẮC BẮT BUỘC ĐỂ ĐẠT CHẤT LƯỢNG ĐỒ HỌA CAO & VƯỢT QUA BỘ KIỂM ĐỊNH (`layout_auditor`):
1. LẤP ĐẦY CÂN ĐỐI & CHỐNG TRÀN VIỀN (`OFF_SCREEN`): Gom trọn toàn bộ thành phần của vùng trung tâm (hoặc từng cột Trái / Phải) vào `VGroup` rồi gọi `self.fit_in_center_zone(group)` / `self.fit_in_left_zone(left_col)` / `self.fit_in_right_zone(right_col)` TRƯỚC KHI diễn hoạt. Hai cột Trái – Phải phải có tỷ trọng hình ảnh cân xứng, không để 1 bên trống trải!
2. MŨI TÊN ĐẸP & ĐÚNG HƯỚNG (`make_arrow` + `GrowArrow`):
   - BẮT BUỘC diễn hoạt mũi tên bằng `GrowArrow(arrow)` (TUYỆT ĐỐI KHÔNG dùng `ShowCreation(arrow)` vì làm méo mũi tên đặc!).
   - Nếu A nằm TRÊN B (`.arrange(DOWN)`): nối `self.make_arrow(A.get_bottom(), B.get_top(), buff=0.10)` (CẤM nối `get_right()` sang `get_left()`!).
   - Nếu A nằm BÊN TRÁI B: nối `self.make_arrow(A.get_right(), B.get_left(), buff=0.10)`.
   - Với BẢNG DỌC (`arrange(DOWN)`): trỏ NGANG vào `slots[i].get_left()` / `get_right()`.
   - Với MẢNG NGANG (`arrange(RIGHT)` như `dp[0..n]`): trỏ từ TRÊN xuống `dp[i].get_top()`, từ DƯỚI lên `dp[i].get_bottom()`, hoặc dùng cung vòng `self.make_arrow(dp[i-2].get_top(), dp[i].get_top(), path_arc=-0.75, buff=0.08)` nhảy qua đầu các ô giữa (CẤM kéo ngang xuyên qua `dp[0..i-1]`!).
3. CHUYỂN ĐỘNG SỐNG ĐỘNG & CẤM RÁCH CHỮ (`Transform` trên `Text`):
   - TUYỆT ĐỐI CẤM dùng `Transform(old_txt, new_txt)` trên `Text` khác ký tự (gây rách nét chữ!). BẮT BUỘC đặt vị trí trước bằng `self.fit_text_in(new_txt, slot_box)` (hoặc `new_txt.move_to(old_txt)`), rồi dùng `self.morph_text_anim(old_txt, new_txt)` hoặc `FadeTransform(old_txt, new_txt, stretch=False)` (sau đó cập nhật biến tham chiếu sang `new_txt`).
   - Kết hợp nhịp nhàng `self.stagger_in(...)` cho dãy phần tử, `self.pop_in(...)` cho thẻ công thức/badge, `self.flow_to(src, dst, path_arc=-0.45)` cho luồng dữ liệu bay vào bảng nhớ (tránh `TransformFromCopy` giữa 2 `Text` khác ký tự!), `self.pulse_focus(...)` (`FlashAround`) để nhấn sáng, và hạt điểm `self.glow(Dot(...))` di chuyển minh họa trực quan.
4. CÂY ĐỆ QUY & Ô BẢNG CHUẨN XÁC:
   - Cây đệ quy xếp theo từng tầng `lv = VGroup(...).arrange(RIGHT, buff=0.55)` rồi `VGroup(lv0, lv1, lv2).arrange(DOWN, buff=0.80)`.
   - Mảng / bảng tạo gọn 4–6 ô; chữ trong ô `slot` bắt buộc gọi `self.fit_text_in(txt, slot)`; hộp có chữ/công thức bắt buộc tạo bằng `self.make_box(...)`.
5. CHỐNG ĐÈ CẢNH CŨ: Luôn gọi `self.clear_stage()` khi chuyển từ phân cảnh hiện tại sang phân cảnh tiếp theo (nhưng KHÔNG gọi `clear_stage()` ở cuối phân cảnh cuối cùng để giữ khung hình tổng kết đẹp mắt khi hết video).
6. ĐÚNG CÚ PHÁP MANIMGL 1.7+: Dùng `from manimlib import *`, `arrange_in_grid(n_rows=..., n_cols=..., buff=...)`, `Text(..., font="Segoe UI")` cho Tiếng Việt, và `Tex(r"...")` chỉ chứa ký hiệu toán học.
"""
    return system_instruction, user_prompt


def build_fixer_prompts(
    broken_code: str,
    error_traceback: str,
    scene_class_name: str,
) -> tuple[str, str]:
    """Ghép (system_instruction, user_prompt) cho Bước 3: Tự sửa lỗi Render & Bố cục."""
    fixer_rules = _extract_skill_section("PROMPT 3: FIXER")
    manim_api = _read_ref("manim-gl-api.md")
    project_sdk = _read_ref("project-sdk.md")

    system_instruction = f"""{fixer_rules}

---
{project_sdk}

---
{manim_api}

QUAN TRỌNG: Chỉ trả về DUY NHẤT toàn bộ mã nguồn Python đã sửa lỗi hoàn chỉnh cho class `{scene_class_name}`, không kèm giải thích bên ngoài.
"""

    tail_error = error_traceback[-4500:] if len(error_traceback) > 4500 else error_traceback

    user_prompt = f"""Đoạn mã ManimGL dưới đây không vượt qua được bước Kiểm định Bố cục / Render tự động.
Hãy đọc kỹ từng dòng cảnh báo lỗi (tọa độ tràn lề, dòng chữ bị đè, mũi tên cắt qua chữ/ô bảng, chữ tràn khỏi ô, khung lệch công thức hoặc Python Traceback), sửa triệt để tất cả các điểm lỗi đó mà vẫn giữ trọn nội dung bài giảng và tên class `{scene_class_name}`, rồi trả về toàn bộ file Python hoàn chỉnh:

=== BÁO CÁO LỖI / KIỂM ĐỊNH BỐ CỤC ===
{tail_error}

=== MÃ NGUỒN HIỆN TẠI ===
```python
{broken_code}
```
"""
    return system_instruction, user_prompt
