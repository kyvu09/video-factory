from manimlib import *
import numpy as np

# ============================================================
# BẢNG MÀU & MOTION DESIGN SYSTEM CHO VIDEO FACTORY
#
# Tông nền Midnight Slate sâu có chiều sâu thị giác (kèm lưới kiến trúc mờ
# & quầng sáng ambient góc màn hình), kết hợp dải màu Neon Cyan -> Violet -> Pink
# và đường cong chuyển động mượt (smooth / overshoot / FlashAround / TransformFromCopy).
# ============================================================
STYLE = {
    # ---- Nền & bề mặt có chiều sâu ----
    "background": "#070B16",   # Midnight navy sâu làm nổi bật ánh sáng neon
    "surface": "#131F38",      # Bề mặt thẻ/khung sáng rõ tách khỏi nền
    "surface_alt": "#1A2B4C",  # Bề mặt nhấn / tiêu đề phụ
    "border": "#334B73",       # Viền khung trung tính rõ nét (không bị chìm vào nền)

    # ---- Bộ 3 màu thương hiệu ----
    "primary": "#38BDF8",      # Sky Cyan - chủ đạo
    "secondary": "#A78BFA",    # Soft Violet - khái niệm phụ / nhánh con
    "accent": "#F472B6",       # Rose Pink - công thức / cấu trúc dữ liệu

    # ---- Màu ngữ nghĩa ----
    "highlight": "#FBBF24",    # Amber Gold - điểm nhấn / trạng thái đang xét
    "success": "#34D399",      # Emerald - kết quả đúng / hoàn tất tối ưu
    "error": "#FB7185",        # Coral Red - chi phí cao / trùng lặp / sai

    # ---- Chữ ----
    "text": "#F8FAFC",
    "muted": "#94A3B8",

    # ---- Cỡ chữ cân đối tỷ lệ 16:9 ----
    "title_size": 38,
    "subtitle_size": 24,
    "body_size": 26,
    "caption_size": 21,
    "code_size": 23,

    # ---- Nhịp điệu Animation (Timing & Easing) ----
    "fast": 0.4,
    "normal": 0.75,
    "slow": 1.25,
    "stagger": 0.12,

    # ---- Thời gian dừng đọc hiểu ----
    "short_pause": 0.45,
    "normal_pause": 1.3,
    "long_pause": 2.2,
}


class ChannelScene(Scene):
    # Thiết lập màu nền chuẩn ngay từ lúc khởi tạo Camera của ManimGL 1.7+
    default_camera_config = {"background_color": STYLE["background"]}

    def setup(self):
        super().setup()
        self.camera.background_color = STYLE["background"]
        self._active_header = None
        self._active_footer = None
        self._active_column_divider = None
        self._scene_cut_times: list[float] = []
        self._header_times: list[float] = []
        self._install_studio_backdrop()

    def _install_studio_backdrop(self):
        """Tạo phông nền Studio có chiều sâu (lưới kiến trúc siêu mảnh + quầng sáng góc + thanh ngăn Header).
        Mọi phần tử nền đặt `z_index <= -8` nên giữ xuyên suốt video và không ảnh hưởng vùng diễn hoạt."""
        grid = NumberPlane(
            x_range=[-8, 8, 1],
            y_range=[-5, 5, 1],
            background_line_style={
                "stroke_color": "#1B2A4A",
                "stroke_width": 1.0,
                "stroke_opacity": 0.28,
            },
            axis_config={
                "stroke_color": "#1B2A4A",
                "stroke_width": 1.0,
                "stroke_opacity": 0.28,
            },
            faded_line_ratio=0,
        )
        grid.set_z_index(-10)

        orb_tl = Circle(radius=4.2, stroke_width=0).set_fill(STYLE["primary"], opacity=0.04)
        orb_tl.move_to([-5.6, 3.2, 0]).set_z_index(-9)

        orb_br = Circle(radius=4.5, stroke_width=0).set_fill(STYLE["secondary"], opacity=0.04)
        orb_br.move_to([5.6, -3.0, 0]).set_z_index(-9)

        header_rule = Line([-6.5, 2.52, 0], [6.5, 2.52, 0], stroke_width=1.4)
        header_rule.set_color_by_gradient(STYLE["primary"], STYLE["secondary"], STYLE["accent"])
        header_rule.set_stroke(opacity=0.38)
        header_rule.set_z_index(-8)

        self.add(grid, orb_tl, orb_br, header_rule)

    # ------------------------------------------------------------------
    # CHỮ (chuẩn hóa font Segoe UI hỗ trợ đầy đủ dấu Tiếng Việt;
    # nhận linh hoạt thêm color, font_size, weight...)
    # ------------------------------------------------------------------
    def make_title(self, text, color=None, font_size=None, weight=BOLD, **kwargs):
        if isinstance(text, Mobject):
            mob = text
            if color is not None:
                mob.set_color(color)
        else:
            mob = Text(
                str(text),
                font="Segoe UI",
                font_size=font_size or STYLE["title_size"],
                weight=weight,
                **kwargs,
            )
            if color is not None:
                mob.set_color(color)
            else:
                mob.set_color_by_gradient(STYLE["primary"], "#7DD3FC", STYLE["secondary"])
        if mob.get_width() > 12.6:
            mob.set_width(12.6)
        return mob

    def make_subtitle(self, text, color=None, font_size=None, **kwargs):
        if isinstance(text, Mobject):
            mob = text
            if color is not None:
                mob.set_color(color)
        else:
            mob = Text(
                str(text),
                font="Segoe UI",
                font_size=font_size or STYLE["subtitle_size"],
                **kwargs,
            ).set_color(color or "#CBD5E1")
        if mob.get_width() > 12.4:
            mob.set_width(12.4)
        return mob

    def make_body(self, text, color=None, font_size=None, **kwargs):
        if isinstance(text, Mobject):
            mob = text
            if color is not None:
                mob.set_color(color)
        else:
            mob = Text(
                str(text),
                font="Segoe UI",
                font_size=font_size or STYLE["body_size"],
                **kwargs,
            ).set_color(color or STYLE["text"])
        if mob.get_width() > 12.4:
            mob.set_width(12.4)
        return mob

    def make_caption(self, text, color=None, font_size=None, **kwargs):
        if isinstance(text, Mobject):
            mob = text
            if color is not None:
                mob.set_color(color)
        else:
            mob = Text(
                str(text),
                font="Segoe UI",
                font_size=font_size or STYLE["caption_size"],
                **kwargs,
            ).set_color(color or STYLE["muted"])
        if mob.get_width() > 12.6:
            mob.set_width(12.6)
        return mob

    def gradient_text(self, text, colors=None, font_size=None, weight=BOLD):
        colors = colors or (STYLE["primary"], STYLE["secondary"], STYLE["accent"])
        mob = Text(text, font="Segoe UI", font_size=font_size or STYLE["title_size"], weight=weight)
        if mob.get_width() > 12.6:
            mob.set_width(12.6)
        mob.set_color_by_gradient(*colors)
        return mob

    # ------------------------------------------------------------------
    # KHUNG / THẺ / MŨI TÊN THẨM MỸ CAO
    # ------------------------------------------------------------------
    def make_card(self, width, height, color=None, corner_radius=0.20, fill_opacity=0.94, fill_color=None):
        color = color or STYLE["primary"]
        card = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=corner_radius,
            color=color,
            fill_color=fill_color or STYLE["surface"],
            fill_opacity=fill_opacity,
            stroke_width=2.5,
        )
        card.set_z_index(-1)
        return card

    def make_box(
        self,
        content,
        width=None,
        height=None,
        color=None,
        text_color=None,
        buff_x=0.75,
        buff_y=0.46,
        font_size=None,
        **card_kwargs,
    ):
        """Tạo khối thẻ `VGroup(card, content_mob)` sắc nét, luôn đi liền nhau khi dịch chuyển/thu phóng."""
        if isinstance(content, str):
            mob = Text(
                content,
                font="Segoe UI",
                font_size=font_size or STYLE["body_size"],
            ).set_color(text_color or STYLE["text"])
        else:
            mob = content
            if text_color is not None:
                mob.set_color(text_color)

        w = float(width) if width is not None else float(mob.get_width() + buff_x)
        h = float(height) if height is not None else float(mob.get_height() + buff_y)
        self.fit_to_box(mob, max_width=max(0.2, w - 0.28), max_height=max(0.15, h - 0.18), auto_upscale=False)

        card = self.make_card(w, h, color=color or STYLE["primary"], **card_kwargs)
        mob.move_to(card.get_center())
        return VGroup(card, mob)

    def make_badge(self, text, color=None, font_size=20):
        """Tạo nhãn pill nhỏ gọn (dùng cho độ phức tạp O(1), O(N), bước 1, 2...)."""
        c = color or STYLE["highlight"]
        lbl = Text(str(text), font="Segoe UI", font_size=font_size, weight=BOLD).set_color(c)
        pill = RoundedRectangle(
            width=lbl.get_width() + 0.46,
            height=lbl.get_height() + 0.24,
            corner_radius=0.16,
            color=c,
            fill_color=STYLE["surface_alt"],
            fill_opacity=0.92,
            stroke_width=1.8,
        )
        pill.set_z_index(-1)
        pill.move_to(lbl)
        return VGroup(pill, lbl)

    def make_arrow(self, start, end, color=None, buff=0.10, path_arc=0.0, thickness=2.4):
        """Tạo mũi tên thanh thoát, màu sắc rực rỡ rõ nét trên nền tối."""
        arr = Arrow(
            start,
            end,
            buff=buff,
            path_arc=path_arc,
            thickness=thickness,
            tip_width_ratio=4.4,
        )
        arr.set_color(color or STYLE["primary"])
        return arr

    def make_formula_card(self, content_mob, color=None, buff_x=1.0, buff_y=0.68):
        """Tạo khung thẻ tự động khớp kích thước và nằm dưới `content_mob`."""
        card = self.make_card(
            width=content_mob.get_width() + buff_x,
            height=content_mob.get_height() + buff_y,
            color=color or STYLE["accent"],
        )
        card.move_to(content_mob)
        card.set_z_index(min(-1, getattr(content_mob, "z_index", 0) - 1))
        card._paired_content = content_mob
        return card

    def fit_text_in(self, text_mob, container_mob, pad_x=0.22, pad_y=0.12):
        """Tự động co chữ/công thức vừa khít và căn chính giữa lòng ô `container_mob`."""
        max_w = max(0.15, float(container_mob.get_width()) - pad_x)
        max_h = max(0.10, float(container_mob.get_height()) - pad_y)
        return self.fit_to_box(
            text_mob,
            max_width=max_w,
            max_height=max_h,
            center=container_mob.get_center(),
            auto_upscale=False,
        )

    # ------------------------------------------------------------------
    # HỆ THỐNG BỐ CỤC TỐI ƯU KHÔNG GIAN 16:9 (KHÔNG LÃNG PHÍ DIỆN TÍCH)
    # Khung hình chuẩn: rộng 14.22 ([-7.11, 7.11]), cao 8.0 ([-4.0, 4.0])
    #   - HEADER : y in [2.62, 3.76] (gọn gàng, tinh tế)
    #   - STAGE  : y in [-2.65, 2.32] (rộng 12.6 x cao 4.9 -> tận dụng tối đa màn hình!)
    #   - FOOTER : y in [-3.78, -2.95] (thanh pill chú thích hiện đại)
    # ------------------------------------------------------------------
    def place_header(self, title=None, subtitle=None, *, title_mob=None, subtitle_mob=None):
        """Đặt tiêu đề & phụ đề thanh thoát ở dải trên cùng, tự động hiển thị và thay thế tiêu đề cũ."""
        raw_title = title if title is not None else title_mob
        raw_sub = subtitle if subtitle is not None else subtitle_mob
        if raw_title is None:
            return VGroup()

        if getattr(self, "_active_header", None) is not None:
            self.remove(self._active_header)

        t_mob = raw_title if isinstance(raw_title, Mobject) else self.make_title(str(raw_title))
        if t_mob.get_width() > 12.6:
            t_mob.set_width(12.6)

        if raw_sub is not None:
            t_mob.to_edge(UP, buff=0.24)
            s_mob = raw_sub if isinstance(raw_sub, Mobject) else self.make_subtitle(str(raw_sub))
            if s_mob.get_width() > 12.4:
                s_mob.set_width(12.4)
            s_mob.next_to(t_mob, DOWN, buff=0.10)
            hdr = VGroup(t_mob, s_mob)
        else:
            t_mob.to_edge(UP, buff=0.36)
            hdr = t_mob

        self._active_header = hdr
        t_now = round(float(getattr(self, "time", 0.0)), 3)
        hdr_times = getattr(self, "_header_times", None)
        if isinstance(hdr_times, list) and t_now > 1.0 and (not hdr_times or t_now - hdr_times[-1] > 1.0):
            hdr_times.append(t_now)
        self.add(hdr)
        return hdr

    def place_footer(self, caption=None, *, caption_mob=None, color=None):
        """Đặt thanh chú thích dạng pill hiện đại ở dải dưới cùng màn hình."""
        raw_cap = caption if caption is not None else caption_mob
        if raw_cap is None:
            return VGroup()

        if getattr(self, "_active_footer", None) is not None:
            self.remove(self._active_footer)

        c_mob = raw_cap if isinstance(raw_cap, Mobject) else self.make_caption(str(raw_cap), color=color or "#CBD5E1")
        if color is not None and isinstance(raw_cap, Mobject):
            c_mob.set_color(color)
        if c_mob.get_width() > 12.2:
            c_mob.set_width(12.2)
        c_mob.to_edge(DOWN, buff=0.28)

        pill = RoundedRectangle(
            width=c_mob.get_width() + 0.70,
            height=c_mob.get_height() + 0.24,
            corner_radius=0.18,
            color=STYLE["border"],
            fill_color="#0F182C",
            fill_opacity=0.88,
            stroke_width=1.3,
        )
        pill.move_to(c_mob)
        pill.set_z_index(-6)  # Coi là lớp nền trang trí của footer

        ftr = VGroup(pill, c_mob)
        self._active_footer = ftr
        self.add(ftr)
        return ftr

    def fit_to_box(
        self,
        mob,
        max_width,
        max_height,
        center=None,
        auto_upscale=False,
        target_fill=0.84,
        max_upscale=1.32,
    ):
        """Thu nhỏ nếu vượt hộp cho phép, VÀ tự động phóng lớn vừa vặn (`auto_upscale=True`)
        nếu cụm hình quá nhỏ để bố cục luôn đầy đặn, cân đối, không lãng phí khoảng trống."""
        w = mob.get_width()
        h = mob.get_height()
        if w > 1e-6 and h > 1e-6:
            fit_scale = min(max_width / w, max_height / h)
            if fit_scale < 1.0:
                mob.scale(fit_scale)
            elif auto_upscale:
                desired = min((max_width * target_fill) / w, (max_height * target_fill) / h)
                if desired > 1.05:
                    mob.scale(min(desired, max_upscale))
        if center is not None:
            mob.move_to(np.array(center, dtype=float))
        return mob

    def fit_in_center_zone(self, mob, auto_upscale=True):
        """Đặt cụm hình/sơ đồ lấp đầy cân đối vùng trung tâm rộng rãi (12.2 x 4.7)."""
        if getattr(self, "_active_column_divider", None) is not None:
            self.remove(self._active_column_divider)
            self._active_column_divider = None
        return self.fit_to_box(
            mob,
            max_width=12.2,
            max_height=4.75,
            center=[0.0, -0.18, 0.0],
            auto_upscale=auto_upscale,
            target_fill=0.82,
            max_upscale=1.30,
        )

    def fit_in_left_zone(self, mob, auto_upscale=True):
        """Đặt cụm hình minh họa lấp đầy cân đối Cột Trái (5.95 x 4.75 tại x = -3.35)."""
        self._ensure_column_divider()
        return self.fit_to_box(
            mob,
            max_width=5.95,
            max_height=4.75,
            center=[-3.35, -0.18, 0.0],
            auto_upscale=auto_upscale,
            target_fill=0.84,
            max_upscale=1.28,
        )

    def fit_in_right_zone(self, mob, auto_upscale=True):
        """Đặt bảng/công thức lấp đầy cân đối Cột Phải (5.95 x 4.75 tại x = +3.35)."""
        self._ensure_column_divider()
        return self.fit_to_box(
            mob,
            max_width=5.95,
            max_height=4.75,
            center=[3.35, -0.18, 0.0],
            auto_upscale=auto_upscale,
            target_fill=0.84,
            max_upscale=1.28,
        )

    def _ensure_column_divider(self):
        """Đường phân cách dọc tinh tế ở giữa màn hình khi dùng bố cục 2 cột."""
        if getattr(self, "_active_column_divider", None) is None:
            div = DashedLine(
                start=[0.0, 2.15, 0.0],
                end=[0.0, -2.50, 0.0],
                dash_length=0.14,
                stroke_width=1.4,
                stroke_color=STYLE["border"],
                stroke_opacity=0.40,
            )
            div.set_z_index(-7)
            self._active_column_divider = div
            self.add(div)

    def clear_stage(self, *keep, run_time=0.5):
        """Chuyển cảnh mượt mà: xóa các vật thể nội dung nhưng giữ nguyên phông nền Studio (`z_index <= -5`)."""
        keep_ids = {id(k) for k in keep}
        if getattr(self, "_active_header", None) is not None and id(self._active_header) not in keep_ids:
            self._active_header = None
        if getattr(self, "_active_footer", None) is not None and id(self._active_footer) not in keep_ids:
            if self._active_footer in self.mobjects:
                self.remove(self._active_footer)
            self._active_footer = None
        if getattr(self, "_active_column_divider", None) is not None:
            self.remove(self._active_column_divider)
            self._active_column_divider = None

        to_fade = [
            m for m in list(self.mobjects)
            if m is not self.camera.frame
            and getattr(m, "z_index", 0) > -5
            and id(m) not in keep_ids
        ]
        if to_fade:
            t_now = round(float(getattr(self, "time", 0.0)), 3)
            cut_times = getattr(self, "_scene_cut_times", None)
            if isinstance(cut_times, list) and t_now > 0.5 and (not cut_times or t_now - cut_times[-1] > 0.8):
                cut_times.append(t_now)
            self.play(*[FadeOut(m, shift= DOWN * 0.12) for m in to_fade], run_time=run_time)

    # ------------------------------------------------------------------
    # BỘ HIỆU ỨNG MOTION GRAPHICS MƯỢT & SỐNG ĐỘNG (3BLUE1BROWN STYLE)
    # ------------------------------------------------------------------
    def glow(self, mobject, color=None, layers=3, spread=0.07, opacity=0.18):
        color = color or mobject.get_color()
        halo = VGroup()
        halo._is_glow_group = True
        for i in range(layers, 0, -1):
            layer = mobject.copy()
            layer.set_color(color)
            layer.set_opacity(opacity * i / layers)
            layer.scale(1 + spread * i)
            layer.set_z_index(getattr(mobject, "z_index", 0) - 1)
            halo.add(layer)
        halo.add(mobject.copy().set_color(color))
        return halo

    def background_grid(self, color=None, opacity=0.25):
        color = color or STYLE["border"]
        grid = NumberPlane(
            background_line_style={
                "stroke_color": color,
                "stroke_width": 1,
                "stroke_opacity": opacity,
            },
            faded_line_ratio=0,
        )
        grid.set_z_index(-10)
        return grid

    def pop_in(self, mob, run_time=0.6):
        """Hiệu ứng nảy nhẹ đàn hồi (spring overshoot) hiện đại khi xuất hiện thẻ/nút."""
        self.play(GrowFromCenter(mob, rate_func=overshoot), run_time=run_time)

    def stagger_in(self, group, shift=UP * 0.22, lag_ratio=0.12, run_time=0.95):
        """Hiệu ứng xuất hiện đuổi nhau theo làn sóng mượt mà cho danh sách / mảng / lưới."""
        self.play(
            LaggedStart(
                *[FadeIn(m, shift=shift, scale=0.92) for m in group],
                lag_ratio=lag_ratio,
            ),
            run_time=run_time,
        )

    def flow_to(self, source_mob, target_mob, path_arc=-0.45, color=None, run_time=0.80):
        """Bắn hạt ánh sáng bay vòng cung từ `source_mob` sang `target_mob` đồng thời hiện `target_mob` sắc nét (không bao giờ gây rách chữ!)."""
        p1 = source_mob.get_center()
        p2 = target_mob.get_center()
        c = color or STYLE["highlight"]
        orb = Dot(point=p1, radius=0.08, color=c)
        path = ArcBetweenPoints(p1, p2, angle=path_arc) if np.linalg.norm(p2 - p1) > 1e-3 else Line(p1, p2 + RIGHT * 0.01)
        self.play(
            MoveAlongPath(orb, path, rate_func=smooth, remover=True),
            FadeIn(target_mob, shift=UP * 0.10, scale=0.94),
            run_time=run_time,
        )

    def morph_text_anim(self, old_mob, new_mob, shift=UP * 0.10):
        """Trả về Animation chuyển chữ mượt kiểu cuộn số (không bao giờ bị rách nét chữ như `Transform`)."""
        return AnimationGroup(
            FadeOut(old_mob, shift=shift),
            FadeIn(new_mob, shift=shift),
        )

    def morph_text(self, old_mob, new_mob, run_time=0.65):
        """Chuyển đổi mượt từ `old_mob` sang `new_mob` tại chỗ (tránh lỗi vỡ/méo ký tự của `Transform`)."""
        self.play(self.morph_text_anim(old_mob, new_mob), run_time=run_time)

    def pulse_focus(self, mob, color=None, run_time=0.9):
        """Tia sáng neon chạy viền `FlashAround` kết hợp nhịp phồng nhẹ thu hút ánh nhìn (giữ nguyên nền thẻ tối không bị chói chữ!)."""
        c = color or STYLE["highlight"]
        self.play(
            FlashAround(mob, color=c, stroke_width=4.0, time_width=1.25, buff=0.08),
            ScaleInPlace(mob, 1.06, rate_func=there_and_back),
            run_time=run_time,
        )

    def show_title(self, mob):
        self.play(Write(mob), run_time=STYLE["normal"])

    def fade_in(self, mob):
        self.play(
            FadeIn(mob, shift=UP * 0.16, scale=0.96),
            run_time=STYLE["normal"],
        )

    def emphasize(self, mob, color=None):
        c = color or STYLE["highlight"]
        self.pulse_focus(mob, color=c, run_time=0.85)
