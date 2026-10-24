"""
Bộ kiểm định tự động Bố cục & Tràn viền (Layout & Bounds Auditor) cho ManimGL.

Chạy thử Scene ở chế độ headless siêu tốc (`skip_animations=True`, không mở cửa sổ,
không mã hóa MP4 — mất ~1–2 giây) để kiểm tra chính xác tọa độ khung bao (Bounding Box)
sau từng lệnh `self.play(...)`:
  1. `OFF_SCREEN`           : Hình vẽ / chữ bị tràn ra ngoài khung hình camera.
  2. `TEXT_OVERLAP`         : Hai chữ / công thức đè chồng lên nhau.
  3. `CARD_OCCLUDES_TEXT`   : Khung nền màu đặc vẽ đè lên trên làm mờ chữ/công thức.
  4. `TEXT_OVERFLOWS_BOX`   : Chữ đặt trong ô bảng / thẻ bị to hơn hoặc tràn chạm viền ô.
  5. `TEXT_CROSSED_BY_SHAPE`: Chữ / công thức bị mũi tên (`Arrow`), đường thẳng hoặc cạnh hình cắt ngang.
  6. `ARROW_PIERCES_BOX`    : Mũi tên (`Arrow`) đâm xuyên chéo qua khung hoặc xuyên dọc qua các ô bảng khác.
  7. `PAIRED_CARD_DETACHED` : Khung `make_formula_card` bị dịch chuyển mà bỏ rơi công thức ở vị trí cũ.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass
class AuditOutcome:
    ok: bool
    runtime_error: str = ""
    layout_issues: list[str] = field(default_factory=list)
    scene_cut_times: list[float] = field(default_factory=list)
    header_times: list[float] = field(default_factory=list)
    virtual_duration: float = 0.0

    def format_for_fixer(self) -> str:
        if self.runtime_error:
            return self.runtime_error
        if not self.layout_issues:
            return ""
        header = (
            "LỖI BỐ CỤC HÌNH ẢNH (LAYOUT / OVERLAP / ARROW / OUT-OF-BOUNDS):\n"
            "Code chạy không văng Exception nhưng bố cục hiển thị trên video bị lỗi nghiêm trọng:\n"
        )
        bullet_list = "\n".join(f"  {i + 1}. {msg}" for i, msg in enumerate(self.layout_issues))
        guide = (
            "\n\nHƯỚNG DẪN CÁCH SỬA BẮT BUỘC:\n"
            "- Với lỗi TRÀN LỀ MÀN HÌNH (`OFF_SCREEN`): Gom trọn cụm hình vào `VGroup` rồi gọi "
            "`self.fit_in_center_zone(group)` hoặc `self.fit_in_left_zone(group)` / `self.fit_in_right_zone(group)`.\n"
            "- Với lỗi ĐÈ CHỮ LÊN CHỮ TẠI (0, 0) KHI ĐỔI CHỮ: Trước khi gọi `self.morph_text_anim(old_txt, new_txt)` hoặc `FadeTransform(old_txt, new_txt, stretch=False)`, "
            "BẮT BUỘC đặt vị trí cho `new_txt` bằng `self.fit_text_in(new_txt, slot_box)` hoặc `new_txt.move_to(old_txt)` (CẤM dùng `Transform` trên `Text` vì gây rách chữ!). "
            "Với cây đệ quy (recursion tree), hãy xếp từng tầng thành `level = VGroup(...).arrange(RIGHT, buff=0.6)` rồi xếp các tầng `VGroup(lv0, lv1, lv2).arrange(DOWN, buff=0.8)` để các nhánh con không bao giờ trùng tọa độ!\n"
            "- Với lỗi MŨI TÊN CẮT QUA CHỮ HOẶC ĐÂM XUYÊN Ô MẢNG (`Arrow`):\n"
            "  + Luôn tạo mũi tên bằng `self.make_arrow(...)` và diễn hoạt bằng `GrowArrow(arr)`.\n"
            "  + Nếu 2 khối xếp DỌC: dùng `self.make_arrow(top.get_bottom(), bottom.get_top(), buff=0.10)`.\n"
            "  + Nếu trỏ vào ô `slots[i]` của BẢNG DỌC (`arrange(DOWN)`): trỏ NGANG vào `slots[i].get_left()` hoặc `get_right()`.\n"
            "  + Nếu trỏ vào ô `dp[i]` của MẢNG NGANG (`arrange(RIGHT)`): BẮT BUỘC trỏ từ TRÊN xuống `dp[i].get_top()` hoặc từ DƯỚI lên `dp[i].get_bottom()`, "
            "hoặc dùng mũi tên vòng cung `self.make_arrow(dp[i-2].get_top(), dp[i].get_top(), path_arc=-0.75, buff=0.08)` nhảy qua đầu các ô giữa — TUYỆT ĐỐI CẤM kéo mũi tên ngang xuyên qua `dp[0..i-1]`!\n"
            "- Với lỗi CHỮ TRÀN KHỎI Ô BẢNG: Gọi `self.fit_text_in(text_mob, slot)` để chữ tự co vừa khít lòng ô.\n"
            "- Với lỗi LỆCH KHUNG CÔNG THỨC / KHUNG CHE CHỮ: Dùng `box = self.make_box(formula_or_text)` để khung và chữ luôn đi liền nhau trong 1 `VGroup`.\n"
        )
        return header + bullet_list + guide


# ------------------------------------------------------------------
# CÁC HÀM HÌNH HỌC 2D PHỤC VỤ KIỂM ĐỊNH TRONG TIẾN TRÌNH CON
# ------------------------------------------------------------------
def _rect_intersection_area(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _rect_area(r: tuple[float, float, float, float]) -> float:
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def _point_strictly_inside_rect(pt: tuple[float, float], r: tuple[float, float, float, float], pad: float = 0.02) -> bool:
    return (r[0] + pad) < pt[0] < (r[2] - pad) and (r[1] + pad) < pt[1] < (r[3] - pad)


def _segment_intersects_rect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    rect: tuple[float, float, float, float],
) -> bool:
    """Thuật toán Liang-Barsky kiểm tra đoạn thẳng (p1, p2) có cắt qua hình chữ nhật `rect` không."""
    x1, y1 = p1
    x2, y2 = p2
    rx1, ry1, rx2, ry2 = rect
    if rx2 <= rx1 or ry2 <= ry1:
        return False

    dx = x2 - x1
    dy = y2 - y1
    p = [-dx, dx, -dy, dy]
    q = [x1 - rx1, rx2 - x1, y1 - ry1, ry2 - y1]

    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1e-9:
            if qi < 0:
                return False
        else:
            t = qi / pi
            if pi < 0:
                if t > u2:
                    return False
                if t > u1:
                    u1 = t
            else:
                if t < u1:
                    return False
                if t < u2:
                    u2 = t
    return u1 <= u2


def _run_audit_in_process(scene_file: str, scene_class_name: str) -> dict[str, Any]:
    """Hàm chạy trực tiếp bên trong subprocess kiểm định."""
    from manimlib.module_loader import ModuleLoader
    from manimlib.mobject.coordinate_systems import CoordinateSystem
    from manimlib.mobject.geometry import Arrow, Line, Rectangle, RoundedRectangle, Square, StrokeArrow
    from manimlib.mobject.mobject import Group, Mobject
    from manimlib.mobject.number_line import NumberLine
    from manimlib.mobject.shape_matchers import SurroundingRectangle
    from manimlib.mobject.svg.brace import Brace
    from manimlib.mobject.svg.string_mobject import StringMobject
    from manimlib.mobject.types.vectorized_mobject import VGroup, VMobject
    from manimlib.scene.scene import Scene

    scene_path_resolved = str(Path(scene_file).resolve())

    try:
        module = ModuleLoader.get_module(scene_path_resolved)
        scene_cls = getattr(module, scene_class_name, None)
        if scene_cls is None or not issubclass(scene_cls, Scene):
            return {
                "ok": False,
                "runtime_error": f"Không tìm thấy class Scene `{scene_class_name}` trong {scene_file}.",
                "layout_issues": [],
            }
    except Exception:
        return {
            "ok": False,
            "runtime_error": traceback.format_exc(),
            "layout_issues": [],
        }

    issues: list[str] = []
    seen_signatures: set[str] = set()
    play_counter = 0

    def record_issue(sig: str, msg: str):
        if sig not in seen_signatures and len(issues) < 12:
            seen_signatures.add(sig)
            issues.append(msg)

    def find_scene_line_number() -> int | None:
        for frame in reversed(traceback.extract_stack()):
            try:
                if str(Path(frame.filename).resolve()) == scene_path_resolved:
                    return frame.lineno
            except Exception:
                continue
        return None

    def get_bbox_2d(mob: Mobject) -> tuple[float, float, float, float] | None:
        try:
            left = float(mob.get_left()[0])
            right = float(mob.get_right()[0])
            bottom = float(mob.get_bottom()[1])
            top = float(mob.get_top()[1])
            if right - left < 1e-4 and top - bottom < 1e-4:
                return None
            return (left, bottom, right, top)
        except Exception:
            return None

    def get_own_points_bbox_2d(mob: VMobject) -> tuple[float, float, float, float] | None:
        try:
            pts = mob.get_points()
            if pts is None or len(pts) == 0:
                return None
            left = float(pts[:, 0].min())
            right = float(pts[:, 0].max())
            bottom = float(pts[:, 1].min())
            top = float(pts[:, 1].max())
            if right - left < 1e-4 and top - bottom < 1e-4:
                return None
            return (left, bottom, right, top)
        except Exception:
            return get_bbox_2d(mob)

    def short_text_desc(mob: StringMobject) -> str:
        raw = getattr(mob, "string", "") or ""
        if not raw and hasattr(mob, "get_string"):
            try:
                raw = mob.get_string()
            except Exception:
                raw = ""
        raw = " ".join(str(raw).split())
        if len(raw) > 32:
            raw = raw[:29] + "..."
        return f"{type(mob).__name__}({raw!r})"

    def collect_visual_items(scene_obj: Scene) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        order_counter = 0

        def walk(mob: Mobject):
            nonlocal order_counter
            if mob is scene_obj.camera.frame:
                return
            z_idx = float(getattr(mob, "z_index", 0) or 0)
            if z_idx <= -5:
                return

            # Nếu là hiệu ứng glow, chỉ xét phần tử gốc nằm trên cùng
            if getattr(mob, "_is_glow_group", False) and len(mob.submobjects) > 0:
                walk(mob.submobjects[-1])
                return

            # 1. Chữ / Công thức / Code (loại trừ Brace vì Brace kế thừa Tex nhưng là ký hiệu hình học)
            if isinstance(mob, StringMobject) and not isinstance(mob, Brace):
                try:
                    if mob.get_fill_opacity() < 0.05 and mob.get_stroke_opacity() < 0.05:
                        return
                except Exception:
                    pass
                bb = get_bbox_2d(mob)
                if bb:
                    order_counter += 1
                    items.append(
                        {
                            "mob_id": id(mob),
                            "kind": "text",
                            "name": short_text_desc(mob),
                            "bbox": bb,
                            "z": z_idx,
                            "order": order_counter,
                        }
                    )
                return

            # 2. Nhân vật StickmanTeacher
            if type(mob).__name__ == "StickmanTeacher":
                bb = get_bbox_2d(mob)
                if bb:
                    order_counter += 1
                    items.append(
                        {
                            "mob_id": id(mob),
                            "kind": "character",
                            "name": "StickmanTeacher",
                            "bbox": bb,
                            "z": z_idx,
                            "order": order_counter,
                        }
                    )
                return

            # 3. Hệ trục tọa độ (Axes, NumberLine): chỉ kiểm tra tràn khung hình tổng thể
            if isinstance(mob, (CoordinateSystem, NumberLine)):
                bb = get_bbox_2d(mob)
                if bb:
                    order_counter += 1
                    items.append(
                        {
                            "mob_id": id(mob),
                            "kind": "axes",
                            "name": type(mob).__name__,
                            "bbox": bb,
                            "z": z_idx,
                            "order": order_counter,
                        }
                    )
                return

            # 4. Các đường nối / Mũi tên (Line, Arrow, Vector, StrokeArrow, DashedLine)
            # Lưu ý: Trong ManimGL, Arrow có fill_opacity=1.0 và stroke_width=0.0; DashedLine chứa các nét đứt trong submobjects
            if isinstance(mob, Line):
                fill_op = float(mob.get_fill_opacity() or 0.0)
                stroke_op = float(mob.get_stroke_opacity() or 0.0)
                if not mob.has_points() and len(mob.submobjects) > 0:
                    sub0 = mob.submobjects[0]
                    if isinstance(sub0, VMobject):
                        fill_op = max(fill_op, float(sub0.get_fill_opacity() or 0.0))
                        stroke_op = max(stroke_op, float(sub0.get_stroke_opacity() or 0.0))
                if fill_op < 0.05 and stroke_op < 0.05:
                    return
                bb = get_bbox_2d(mob)
                if not bb:
                    return
                segs: list[tuple[tuple[float, float], tuple[float, float]]] = []
                try:
                    path_arc = float(getattr(mob, "path_arc", 0.0) or 0.0)
                    if abs(path_arc) > 1e-3 and mob.has_points():
                        samples = [mob.point_from_proportion(k / 8.0) for k in range(9)]
                        for a_pt, b_pt in zip(samples, samples[1:]):
                            p1 = (float(a_pt[0]), float(a_pt[1]))
                            p2 = (float(b_pt[0]), float(b_pt[1]))
                            if abs(p1[0] - p2[0]) > 1e-3 or abs(p1[1] - p2[1]) > 1e-3:
                                segs.append((p1, p2))
                    else:
                        s_pt = mob.get_start()
                        e_pt = mob.get_end()
                        p1 = (float(s_pt[0]), float(s_pt[1]))
                        p2 = (float(e_pt[0]), float(e_pt[1]))
                        if abs(p1[0] - p2[0]) > 1e-3 or abs(p1[1] - p2[1]) > 1e-3:
                            segs.append((p1, p2))
                except Exception:
                    pass
                order_counter += 1
                items.append(
                    {
                        "mob_id": id(mob),
                        "kind": "shape",
                        "name": type(mob).__name__,
                        "bbox": bb,
                        "z": z_idx,
                        "order": order_counter,
                        "fill_opacity": fill_op,
                        "stroke_opacity": stroke_op,
                        "is_connector": True,
                        "is_arrow": isinstance(mob, (Arrow, StrokeArrow)),
                        "is_box": False,
                        "is_surrounding": False,
                        "paired_content_id": None,
                        "segments": segs,
                    }
                )
                return

            # 5. Nhóm VGroup / Group thuần túy -> duyệt đệ quy từng phần tử con
            if type(mob) in (VGroup, Group) or (len(mob.submobjects) > 0 and not mob.has_points()):
                for sub in mob.submobjects:
                    walk(sub)
                return

            # 6. Các hình vẽ vector cơ bản (Polygon, Rectangle, RoundedRectangle, Circle...)
            if isinstance(mob, VMobject) and mob.has_points():
                fill_op = float(mob.get_fill_opacity() or 0.0)
                stroke_op = float(mob.get_stroke_opacity() or 0.0)
                stroke_w = float(mob.get_stroke_width() or 0.0)
                visible_stroke = stroke_op >= 0.15 and stroke_w > 0.05
                visible_fill = fill_op >= 0.15

                if visible_stroke or visible_fill:
                    bb = get_own_points_bbox_2d(mob) if len(mob.submobjects) > 0 else get_bbox_2d(mob)
                    if bb:
                        segs = []
                        try:
                            starts = mob.get_start_anchors()
                            ends = mob.get_end_anchors()
                            for s_pt, e_pt in zip(starts, ends):
                                p1 = (float(s_pt[0]), float(s_pt[1]))
                                p2 = (float(e_pt[0]), float(e_pt[1]))
                                if abs(p1[0] - p2[0]) > 1e-3 or abs(p1[1] - p2[1]) > 1e-3:
                                    segs.append((p1, p2))
                        except Exception:
                            pass
                        paired = getattr(mob, "_paired_content", None)
                        order_counter += 1
                        items.append(
                            {
                                "mob_id": id(mob),
                                "kind": "shape",
                                "name": type(mob).__name__,
                                "bbox": bb,
                                "z": z_idx,
                                "order": order_counter,
                                "fill_opacity": fill_op,
                                "stroke_opacity": stroke_op,
                                "is_connector": False,
                                "is_arrow": False,
                                "is_box": isinstance(mob, (Rectangle, RoundedRectangle, Square))
                                and not isinstance(mob, (Brace, SurroundingRectangle)),
                                "is_surrounding": isinstance(mob, SurroundingRectangle),
                                "paired_content_id": id(paired) if paired is not None else None,
                                "segments": segs,
                            }
                        )

                # RẤT QUAN TRỌNG: Nếu người dùng/LLM gọi `card.add(text)` trên một hình có điểm,
                # vẫn phải duyệt tiếp `mob.submobjects` để không bỏ sót dòng chữ bên trong!
                for sub in mob.submobjects:
                    walk(sub)
                return

            for sub in mob.submobjects:
                walk(sub)

        for top_mob in list(scene_obj.mobjects):
            walk(top_mob)
        return items

    def inspect_current_frame(scene_obj: Scene, step_idx: int, lineno: int | None):
        loc_prefix = f"[Dòng {lineno}, play #{step_idx}]" if lineno else f"[Play #{step_idx}]"
        frame = scene_obj.camera.frame
        f_left = float(frame.get_left()[0])
        f_right = float(frame.get_right()[0])
        f_bottom = float(frame.get_bottom()[1])
        f_top = float(frame.get_top()[1])

        margin_x = 0.14
        margin_y = 0.14
        min_x, max_x = f_left + margin_x, f_right - margin_x
        min_y, max_y = f_bottom + margin_y, f_top - margin_y

        items = collect_visual_items(scene_obj)
        items_by_id = {it["mob_id"]: it for it in items}

        # 1. KIỂM TRA TRÀN VIỀN MÀN HÌNH (OFF_SCREEN)
        for it in items:
            x1, y1, x2, y2 = it["bbox"]
            overflows: list[str] = []
            if x1 < min_x - 0.05:
                overflows.append(f"tràn lề trái (x={x1:.2f} < {min_x:.2f})")
            if x2 > max_x + 0.05:
                overflows.append(f"tràn lề phải (x={x2:.2f} > {max_x:.2f})")
            if y1 < min_y - 0.05:
                overflows.append(f"tràn lề dưới (y={y1:.2f} < {min_y:.2f})")
            if y2 > max_y + 0.05:
                overflows.append(f"tràn lề trên (y={y2:.2f} > {max_y:.2f})")
            if overflows:
                sig = f"OFF_SCREEN:{it['name']}:{','.join(o.split()[2] for o in overflows)}"
                record_issue(
                    sig,
                    f"{loc_prefix} TRÀN LỀ MÀN HÌNH: `{it['name']}` bị {', '.join(overflows)} "
                    f"(khung bao hiện tại: x=[{x1:.2f}, {x2:.2f}], y=[{y1:.2f}, {y2:.2f}]).",
                )

        text_items = [it for it in items if it["kind"] == "text"]
        shape_items = [it for it in items if it["kind"] == "shape"]

        # 2. KIỂM TRA ĐÈ CHỮ LÊN CHỮ (TEXT_OVERLAP)
        for i in range(len(text_items)):
            for j in range(i + 1, len(text_items)):
                t1, t2 = text_items[i], text_items[j]
                inter = _rect_intersection_area(t1["bbox"], t2["bbox"])
                if inter <= 0.0:
                    continue
                smaller = min(_rect_area(t1["bbox"]), _rect_area(t2["bbox"]))
                if smaller > 1e-4 and (inter / smaller) > 0.12:
                    pair = tuple(sorted([t1["name"], t2["name"]]))
                    sig = f"TEXT_OVERLAP:{pair[0]}:{pair[1]}"
                    b1, b2 = t1["bbox"], t2["bbox"]
                    record_issue(
                        sig,
                        f"{loc_prefix} ĐÈ CHỮ LÊN CHỮ: `{t1['name']}` (tâm {(b1[0]+b1[2])/2:.2f}, {(b1[1]+b1[3])/2:.2f}) "
                        f"và `{t2['name']}` (tâm {(b2[0]+b2[2])/2:.2f}, {(b2[1]+b2[3])/2:.2f}) chồng lên nhau!",
                    )

        # 3. KIỂM TRA CHỮ VỚI KHUNG HÌNH / Ô BẢNG / MŨI TÊN
        for t in text_items:
            tx1, ty1, tx2, ty2 = t["bbox"]
            tw, th = tx2 - tx1, ty2 - ty1
            tcx, tcy = (tx1 + tx2) * 0.5, (ty1 + ty2) * 0.5
            t_area = _rect_area(t["bbox"])

            conn_ix = min(0.04, tw * 0.10)
            conn_iy = min(0.04, th * 0.12)
            connector_core = (
                tx1 + conn_ix,
                ty1 + conn_iy,
                tx2 - conn_ix,
                ty2 - conn_iy,
            )
            shp_ix = min(0.05, tw * 0.12)
            shp_iy = min(0.04, th * 0.14)
            shape_core = (
                tx1 + shp_ix,
                ty1 + shp_iy,
                tx2 - shp_ix,
                ty2 - shp_iy,
            )

            for s in shape_items:
                bx1, by1, bx2, by2 = s["bbox"]
                bw, bh = bx2 - bx1, by2 - by1

                # 3a. Khung nền màu đặc vẽ đè lên trên làm che mờ chữ (trừ các mũi tên/đường nối)
                if not s["is_connector"]:
                    is_drawn_above_text = (s["z"] > t["z"]) or (s["z"] == t["z"] and s["order"] > t["order"])
                    if is_drawn_above_text and s["fill_opacity"] >= 0.35 and t_area > 1e-4:
                        inter = _rect_intersection_area(t["bbox"], s["bbox"])
                        if (inter / t_area) > 0.20:
                            sig = f"OCCLUDE:{s['name']}:{t['name']}"
                            record_issue(
                                sig,
                                f"{loc_prefix} KHUNG NỀN ĐÈ CHE MỜ CHỮ: `{s['name']}` (fill_opacity={s['fill_opacity']:.2f}) "
                                f"được vẽ đè lên trên `{t['name']}` làm che mờ chữ. "
                                f"Hãy dùng `self.make_box(...)` hoặc đặt `z_index=-1` cho khung nền.",
                            )

                # 3b. Chữ đặt bên trong một ô bảng / khung (`Rectangle` / `RoundedRectangle`) nhưng bị to tràn viền ô
                if s["is_box"] and bw >= 0.40 and bh >= 0.22:
                    if bx1 < tcx < bx2 and by1 < tcy < by2:
                        if (
                            tx1 < bx1 + 0.04
                            or tx2 > bx2 - 0.04
                            or ty1 < by1 + 0.025
                            or ty2 > by2 - 0.025
                        ):
                            sig = f"BOX_OVERFLOW:{s['name']}:{t['name']}"
                            record_issue(
                                sig,
                                f"{loc_prefix} CHỮ TRÀN KHỎI Ô KHUNG: `{t['name']}` (rộng {tw:.2f}, cao {th:.2f}) "
                                f"chạm hoặc tràn ra ngoài viền của `{s['name']}` (rộng {bw:.2f}, cao {bh:.2f})! "
                                f"Hãy gọi `self.fit_text_in(text_mob, slot)` để co chữ vừa khít lòng ô, hoặc dùng `self.make_box(...)`.",
                            )
                            continue

                # 3c. Mũi tên / Đường thẳng cắt xuyên qua chữ
                if s["is_connector"] and tw > 0.18 and th > 0.10 and s["segments"]:
                    crossed = any(_segment_intersects_rect(p1, p2, connector_core) for p1, p2 in s["segments"])
                    if crossed:
                        sig = f"ARROW_TEXT:{s['name']}:{t['name']}"
                        record_issue(
                            sig,
                            f"{loc_prefix} MŨI TÊN / ĐƯỜNG KẺ CẮT ĐÈ LÊN CHỮ: `{s['name']}` cắt ngang qua `{t['name']}` "
                            f"(x=[{tx1:.2f}, {tx2:.2f}], y=[{ty1:.2f}, {ty2:.2f}])! "
                            f"Nếu A nằm trên B hãy dùng `Arrow(A.get_bottom(), B.get_top())`; "
                            f"nếu trỏ vào ô của bảng dọc hãy trỏ NGANG từ cạnh trái/phải vào ô thay vì trỏ dọc từ trên xuống!",
                        )
                        continue

                # 3d. Cạnh đa giác / hình học cắt ngang qua chữ (bỏ qua SurroundingRectangle dùng để tô sáng 1 dòng Code/Tex)
                if not s["is_connector"] and not s.get("is_surrounding") and tw > 0.30 and th > 0.12 and s["segments"]:
                    crossed = any(_segment_intersects_rect(p1, p2, shape_core) for p1, p2 in s["segments"])
                    if crossed:
                        sig = f"CROSS:{s['name']}:{t['name']}"
                        record_issue(
                            sig,
                            f"{loc_prefix} CHỮ ĐÈ LÊN CẠNH HÌNH VẼ: `{t['name']}` (x=[{tx1:.2f}, {tx2:.2f}], y=[{ty1:.2f}, {ty2:.2f}]) "
                            f"bị nét vẽ của `{s['name']}` cắt ngang qua! "
                            f"Hãy gọi `self.clear_stage()` xóa hình cũ hoặc dịch tách rời sang 2 cột Trái – Phải.",
                        )

        # 4. KIỂM TRA MŨI TÊN ĐÂM XUYÊN QUA LÒNG KHUNG / Ô BẢNG KHÁC (ARROW_PIERCES_BOX)
        arrow_items = [s for s in shape_items if s["is_arrow"] and s["segments"]]
        box_items = [s for s in shape_items if s["is_box"]]
        for arr in arrow_items:
            for box in box_items:
                bx1, by1, bx2, by2 = box["bbox"]
                bw, bh = bx2 - bx1, by2 - by1
                if bw < 0.40 or bh < 0.22:
                    continue
                # Bỏ qua nếu toàn bộ mũi tên được vẽ nằm gọn bên trong một khung bao lớn
                all_inside = all(
                    _point_strictly_inside_rect(p1, box["bbox"], pad=0.05)
                    and _point_strictly_inside_rect(p2, box["bbox"], pad=0.05)
                    for p1, p2 in arr["segments"]
                )
                if all_inside:
                    continue

                box_core = (
                    bx1 + bw * 0.16,
                    by1 + bh * 0.16,
                    bx2 - bw * 0.16,
                    by2 - bh * 0.16,
                )
                if any(_segment_intersects_rect(p1, p2, box_core) for p1, p2 in arr["segments"]):
                    sig = f"ARROW_BOX:{arr['name']}:{box['name']}:{round((bx1+bx2)/2, 1)}"
                    record_issue(
                        sig,
                        f"{loc_prefix} MŨI TÊN ĐÂM XUYÊN QUA KHUNG / Ô BẢNG: `{arr['name']}` cắt xuyên qua lòng `{box['name']}` "
                        f"tại tâm ({(bx1+bx2)/2:.2f}, {(by1+by2)/2:.2f})! "
                        f"Nếu nối 2 khối xếp dọc hãy dùng `Arrow(top_mob.get_bottom(), bottom_mob.get_top(), buff=0.12)`; "
                        f"nếu trỏ vào 1 ô của bảng băm / mảng dọc hãy trỏ NGANG từ bên ngoài vào `slot.get_left()` hoặc `slot.get_right()`!",
                    )

        # 5. KIỂM TRA KHUNG `make_formula_card` BỊ DỊCH CHUYỂN MÀ BỎ RƠI CÔNG THỨC Ở CHỖ CŨ
        for s in shape_items:
            paired_id = s.get("paired_content_id")
            if paired_id and paired_id in items_by_id:
                content_it = items_by_id[paired_id]
                sb = s["bbox"]
                cb = content_it["bbox"]
                scx, scy = (sb[0] + sb[2]) * 0.5, (sb[1] + sb[3]) * 0.5
                ccx, ccy = (cb[0] + cb[2]) * 0.5, (cb[1] + cb[3]) * 0.5
                if math.hypot(scx - ccx, scy - ccy) > 0.35:
                    sig = f"DETACHED_CARD:{content_it['name']}"
                    record_issue(
                        sig,
                        f"{loc_prefix} LỆCH KHUNG CÔNG THỨC: Khung `{s['name']}` đã di chuyển tới ({scx:.2f}, {scy:.2f}) "
                        f"nhưng nội dung `{content_it['name']}` bị bỏ rơi tại ({ccx:.2f}, {ccy:.2f})! "
                        f"Hãy dùng `box = self.make_box(formula)` (hoặc gom `VGroup(card, formula)`) trước khi gọi `.arrange()` / `fit_in_*_zone()`.",
                    )

    orig_play = Scene.play
    fallback_fade_cuts: list[float] = []

    def audited_play(self: Scene, *args, **kwargs):
        nonlocal play_counter
        lineno = find_scene_line_number()
        t_before = round(float(getattr(self, "time", 0.0)), 3)
        fadeout_count = sum(1 for a in args if type(a).__name__ == "FadeOut")
        if fadeout_count >= 2 and t_before > 1.0:
            if not fallback_fade_cuts or (t_before - fallback_fade_cuts[-1] > 1.0):
                fallback_fade_cuts.append(t_before)
        result = orig_play(self, *args, **kwargs)
        play_counter += 1
        inspect_current_frame(self, play_counter, lineno)
        return result

    Scene.play = audited_play  # type: ignore[assignment]
    try:
        scene_instance = scene_cls(
            window=None,
            skip_animations=True,
            preview_while_skipping=False,
            file_writer_config={
                "write_to_movie": False,
                "save_last_frame": False,
                "open_file_upon_completion": False,
                "quiet": True,
            },
        )
        scene_instance.run()
    except Exception:
        return {
            "ok": False,
            "runtime_error": traceback.format_exc(),
            "layout_issues": issues,
            "scene_cut_times": [],
            "header_times": [],
            "virtual_duration": 0.0,
        }
    finally:
        Scene.play = orig_play  # type: ignore[assignment]

    cut_times = list(getattr(scene_instance, "_scene_cut_times", None) or fallback_fade_cuts)
    hdr_times = list(getattr(scene_instance, "_header_times", None) or [])
    virt_dur = round(float(getattr(scene_instance, "time", 0.0)), 3)

    return {
        "ok": len(issues) == 0,
        "runtime_error": "",
        "layout_issues": issues,
        "scene_cut_times": cut_times,
        "header_times": hdr_times,
        "virtual_duration": virt_dur,
    }


def audit_scene_file(
    scene_path: str | Path,
    scene_class_name: str,
    timeout_sec: int = 90,
) -> AuditOutcome:
    """
    Chạy kiểm định nhanh `scene_path` trong một subprocess độc lập (không mở cửa sổ).
    Trả về `AuditOutcome` chứa lỗi runtime (nếu có) hoặc danh sách lỗi tràn lề / đè chữ.
    """
    cmd = [
        sys.executable,
        "-m",
        "core.layout_auditor",
        str(scene_path),
        scene_class_name,
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            creationflags=creation_flags,
        )
    except subprocess.TimeoutExpired:
        return AuditOutcome(ok=False, runtime_error="Kiểm định Scene bị quá thời gian (vòng lặp vô hạn?).")

    stdout = proc.stdout or ""
    marker = "===AUDIT_JSON==="
    if marker in stdout:
        json_part = stdout.split(marker, 1)[1].strip()
        try:
            data = json.loads(json_part)
            return AuditOutcome(
                ok=bool(data.get("ok", False)),
                runtime_error=str(data.get("runtime_error", "")),
                layout_issues=list(data.get("layout_issues") or []),
                scene_cut_times=[float(x) for x in (data.get("scene_cut_times") or [])],
                header_times=[float(x) for x in (data.get("header_times") or [])],
                virtual_duration=float(data.get("virtual_duration") or 0.0),
            )
        except Exception:
            pass

    if proc.returncode != 0:
        combined = (stdout + "\n" + (proc.stderr or "")).strip()
        return AuditOutcome(ok=False, runtime_error=combined[-4000:])

    return AuditOutcome(ok=True)


def _cli_main():
    if len(sys.argv) < 3:
        print("Usage: python -m core.layout_auditor <scene_path> <SceneClassName>")
        sys.exit(2)
    res = _run_audit_in_process(sys.argv[1], sys.argv[2])
    print("===AUDIT_JSON===")
    print(json.dumps(res, ensure_ascii=True))


if __name__ == "__main__":
    _cli_main()
