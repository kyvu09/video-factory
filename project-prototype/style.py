from manimlib import *

# ============================================================
# BẢNG MÀU & STYLE CHUNG CHO KÊNH
#
# Nền tối xanh-navy gần đen làm phông, kết hợp 3 màu thương hiệu
# cyan -> tím -> hồng (liền một dải gradient, lấy cảm hứng từ các
# hệ màu thiết kế hiện đại kiểu Tailwind) để tạo cảm giác công
# nghệ, hiện đại. Vàng/xanh lá/đỏ dùng riêng cho ý nghĩa ngữ nghĩa
# (nhấn mạnh / đúng / sai) nên không bị lẫn với màu thương hiệu.
# ============================================================
STYLE = {
    # ---- Nền & bề mặt ----
    "background": "#0A0F1E",   # nền chính: navy gần đen, tương phản mạnh hơn bản cũ
    "surface": "#141D33",      # nền thẻ/khung (card quanh công thức, bảng số liệu)
    "border": "#2A3B5C",       # viền / đường kẻ mờ, lưới nền

    # ---- Bộ 3 màu thương hiệu (phối gradient) ----
    "primary": "#38BDF8",      # cyan - màu chủ đạo (tiêu đề, đường cong chính)
    "secondary": "#A78BFA",    # tím - màu phụ (vùng diện tích, nhãn phụ)
    "accent": "#F472B6",       # hồng - màu nhấn đặc biệt (cao trào, CTA)

    # ---- Màu ngữ nghĩa (giữ tách biệt với màu thương hiệu) ----
    "highlight": "#FBBF24",    # vàng hổ phách - nhấn mạnh ý quan trọng
    "success": "#34D399",      # xanh lá - đúng / kết quả
    "error": "#FB7185",        # đỏ hồng - sai / cảnh báo

    # ---- Chữ ----
    "text": "#F8FAFC",
    "muted": "#94A3B8",

    # ---- Cỡ chữ ----
    "title_size": 42,
    "subtitle_size": 32,
    "body_size": 28,
    "caption_size": 22,        # mới: nhãn phụ/chú thích nhỏ (trước đây hay dùng body_size-3/-4)
    "code_size": 25,

    # ---- Tốc độ animation ----
    "fast": 0.3,
    "normal": 0.7,
    "slow": 1.2,
    "stagger": 0.12,           # mới: lag_ratio cho hiệu ứng xuất hiện nối tiếp (LaggedStart)

    # ---- Thời gian chờ ----
    "short_pause": 0.5,
    "normal_pause": 1.5,
    "long_pause": 2.5,
}


class ChannelScene(Scene):
    def setup(self):
        super().setup()
        self.camera.background_color = STYLE["background"]

    # ------------------------------------------------------------------
    # CHỮ
    # ------------------------------------------------------------------
    def make_title(self, text):
        return Text(
            text,
            font_size=STYLE["title_size"],
            color=STYLE["primary"],
            weight=BOLD,
        )

    def make_subtitle(self, text):
        return Text(
            text,
            font_size=STYLE["subtitle_size"],
            color=STYLE["secondary"],
        )

    def make_body(self, text):
        return Text(
            text,
            font_size=STYLE["body_size"],
            color=STYLE["text"],
        )

    def make_caption(self, text, color=None):
        return Text(
            text,
            font_size=STYLE["caption_size"],
            color=color or STYLE["muted"],
        )

    def gradient_text(self, text, colors=None, font_size=None, weight=BOLD):
        """Chữ phối gradient 3 màu thương hiệu - dùng cho tiêu đề mở đầu/kết
        hoặc những khoảnh khắc muốn thật nổi bật, không nên lạm dụng ở mọi dòng chữ."""
        colors = colors or (STYLE["primary"], STYLE["secondary"], STYLE["accent"])
        mob = Text(text, font_size=font_size or STYLE["title_size"], weight=weight)
        mob.set_color_by_gradient(*colors)
        return mob

    # ------------------------------------------------------------------
    # KHUNG / THẺ - nền cho công thức, số liệu... dùng chung một kiểu
    # ------------------------------------------------------------------
    def make_card(self, width, height, color=None, corner_radius=0.25, fill_opacity=0.85):
        color = color or STYLE["accent"]
        return RoundedRectangle(
            width=width,
            height=height,
            corner_radius=corner_radius,
            color=color,
            fill_color=STYLE["surface"],
            fill_opacity=fill_opacity,
            stroke_width=2,
        )

    # ------------------------------------------------------------------
    # HIỆU ỨNG PHÁT SÁNG (glow) - hợp với nền tối + màu kiểu neon
    # ------------------------------------------------------------------
    def glow(self, mobject, color=None, layers=3, spread=0.08, opacity=0.16):
        """Trả về VGroup gồm các bản sao to dần, mờ dần phía sau mobject để
        tạo cảm giác phát sáng. mobject gốc nằm trên cùng (phần tử cuối)."""
        color = color or mobject.get_color()
        halo = VGroup()
        for i in range(layers, 0, -1):
            layer = mobject.copy()
            layer.set_color(color)
            layer.set_opacity(opacity * i / layers)
            layer.scale(1 + spread * i)
            halo.add(layer)
        halo.add(mobject.copy().set_color(color))
        return halo

    # ------------------------------------------------------------------
    # NỀN DẠNG LƯỚI MỜ (tùy chọn) - thêm chiều sâu "công nghệ" cho cảnh
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # CHUYỂN ĐỘNG DÙNG CHUNG
    # ------------------------------------------------------------------
    def show_title(self, mob):
        self.play(Write(mob), run_time=STYLE["normal"])

    def fade_in(self, mob):
        self.play(
            FadeIn(mob, shift=UP * 0.15),
            run_time=STYLE["normal"],
        )

    def emphasize(self, mob):
        """Nhấn mạnh: đổi màu sang highlight + phồng nhẹ rồi trả lại kích
        thước gốc (trước đây chỉ đổi màu, nay thêm hiệu ứng "pulse")."""
        self.play(
            mob.animate.set_color(STYLE["highlight"]).scale(1.08),
            run_time=STYLE["fast"],
        )
        self.play(
            mob.animate.scale(1 / 1.08),
            run_time=STYLE["fast"],
        )