from manimlib import *
from style import STYLE, ChannelScene
import numpy as np


def riemann_sum(dx, a=0, b=2, f=lambda x: x):
    """Tính tổng Riemann (điểm bên phải) để hiển thị giá trị xấp xỉ S."""
    n = int(round((b - a) / dx))
    xs = a + dx * np.arange(1, n + 1)
    return float(np.sum(f(xs) * dx)), n


class IntegralTutorial(ChannelScene):
    def construct(self):
        accent = STYLE["accent"]

        # =========================
        # 1. TIÊU ĐỀ
        # =========================
        title = self.make_title("Tích phân là gì?")
        title.to_edge(UP, buff=0.35)

        # Gạch chân nhỏ dưới tiêu đề -> cảm giác có thiết kế, không bị "trống"
        title_underline = Line(LEFT, RIGHT, color=accent, stroke_width=3)
        title_underline.set_width(title.get_width() * 0.55)
        title_underline.next_to(title, DOWN, buff=0.12)

        self.show_title(title)
        self.play(GrowFromCenter(title_underline), run_time=0.5)
        self.wait(STYLE["short_pause"])

        # =========================
        # 2. GIỚI THIỆU ĐỒ THỊ
        # =========================
        subtitle = Text(
            "Hãy tìm diện tích bên dưới đường cong!",
            font_size=STYLE["body_size"],
            color=STYLE["text"],
        )
        subtitle.next_to(title_underline, DOWN, buff=0.35)

        self.fade_in(subtitle)

        axes = Axes(
            x_range=(0, 3, 1),
            y_range=(0, 3, 1),
            width=8,
            height=5,
            axis_config={
                "stroke_color": STYLE["muted"],
                "stroke_width": 2,
                "include_tip": True,
            },
            x_axis_config={"include_numbers": True},
            y_axis_config={"include_numbers": True},
        )
        axes.shift(DOWN * 0.6)

        # Nhãn trục x, y -> trông giống sách giáo khoa / video chuyên nghiệp hơn
        axis_labels = axes.get_axis_labels(x_label_tex="x", y_label_tex="y")
        axis_labels.set_color(STYLE["muted"])

        graph = axes.get_graph(
            lambda x: x,
            x_range=(0, 2.5),
            color=STYLE["primary"],
            stroke_width=4,
        )

        graph_label = Text(
            "y = x",
            font_size=STYLE["body_size"],
            color=STYLE["primary"],
        )
        graph_label.move_to(axes.c2p(2.3, 2.6))

        self.play(
            ShowCreation(axes),
            FadeIn(axis_labels),
            run_time=STYLE["slow"],
        )
        self.play(
            ShowCreation(graph),
            FadeIn(graph_label, shift=UP * 0.1),
            run_time=STYLE["slow"],
        )
        self.wait(STYLE["normal_pause"])

        # =========================
        # 3. TÔ VÙNG DIỆN TÍCH
        # =========================
        self.play(FadeOut(subtitle))

        area = axes.get_riemann_rectangles(
            graph,
            x_range=(0, 2),
            dx=0.05,
            colors=(STYLE["secondary"],),
            fill_opacity=0.65,
            stroke_width=0,
        )
        area.set_color(STYLE["secondary"])

        question = Text(
            "Diện tích vùng màu bằng bao nhiêu?",
            font_size=STYLE["body_size"],
            color=STYLE["text"],
        )
        question.to_edge(UP, buff=0.35)

        self.play(
            FadeIn(area),
            Transform(title, question),
            FadeOut(title_underline),
            run_time=STYLE["normal"],
        )
        self.wait(STYLE["normal_pause"])

        # =========================
        # 4. CHIA THÀNH HÌNH CHỮ NHẬT - hội tụ dần qua 3 bước
        #    (thêm nhãn n & S ≈ ... để người xem THẤY phép xấp xỉ tiến gần 2)
        # =========================
        explanation = Text(
            "Cộng diện tích nhiều hình chữ nhật nhỏ",
            font_size=STYLE["body_size"] - 3,
            color=STYLE["highlight"],
        )
        explanation.to_edge(DOWN, buff=0.35)

        self.play(Write(explanation))
        self.wait(STYLE["short_pause"])

        def make_stats_label(dx):
            value, n = riemann_sum(dx)
            label = VGroup(
                Text(f"n = {n}", font_size=STYLE["body_size"] - 4, color=STYLE["text"]),
                Text(f"S ≈ {value:.3f}", font_size=STYLE["body_size"] - 4, color=accent),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            label.next_to(axes, RIGHT, buff=0.45)
            return label

        # Bước 1: thô (4 hình chữ nhật)
        coarse_area = axes.get_riemann_rectangles(
            graph,
            x_range=(0, 2),
            dx=0.5,
            colors=(STYLE["highlight"],),
            fill_opacity=0.75,
            stroke_width=1,
        )
        coarse_area.set_color(STYLE["highlight"])
        stats = make_stats_label(0.5)

        self.play(
            ReplacementTransform(area, coarse_area),
            FadeIn(stats),
            run_time=STYLE["normal"],
        )
        self.wait(STYLE["short_pause"])

        # Bước 2: vừa (10 hình chữ nhật) - bước đệm giúp mắt theo kịp sự hội tụ
        medium_area = axes.get_riemann_rectangles(
            graph,
            x_range=(0, 2),
            dx=0.2,
            colors=(STYLE["highlight"],),
            fill_opacity=0.7,
            stroke_width=0.5,
        )
        medium_area.set_color(STYLE["highlight"])
        medium_stats = make_stats_label(0.2)

        self.play(
            ReplacementTransform(coarse_area, medium_area),
            ReplacementTransform(stats, medium_stats),
            run_time=STYLE["normal"],
        )
        self.wait(STYLE["short_pause"])

        # Bước 3: mịn (80 hình chữ nhật) - gần như khớp hình tam giác
        fine_area = axes.get_riemann_rectangles(
            graph,
            x_range=(0, 2),
            dx=0.025,
            colors=(STYLE["secondary"],),
            fill_opacity=0.65,
            stroke_width=0,
        )
        fine_area.set_color(STYLE["secondary"])
        fine_stats = make_stats_label(0.025)

        self.play(
            ReplacementTransform(medium_area, fine_area),
            ReplacementTransform(medium_stats, fine_stats),
            run_time=STYLE["slow"],
        )
        self.wait(STYLE["normal_pause"])

        # =========================
        # 5. CHUYỂN SANG TAM GIÁC
        # =========================
        self.play(
            FadeOut(fine_area),
            FadeOut(explanation),
            FadeOut(graph_label),
            FadeOut(fine_stats),
            run_time=STYLE["normal"],
        )

        triangle = Polygon(
            axes.c2p(0, 0),
            axes.c2p(2, 0),
            axes.c2p(2, 2),
            color=STYLE["success"],
            fill_color=STYLE["success"],
            fill_opacity=0.45,
            stroke_width=3,
        )

        self.play(
            ShowCreation(triangle),
            run_time=STYLE["normal"],
        )

        base_label = Text(
            "Đáy = 2",
            font_size=STYLE["body_size"] - 3,
            color=STYLE["highlight"],
        )
        base_label.next_to(axes.c2p(1, 0), DOWN, buff=0.15)

        height_label = Text(
            "Cao = 2",
            font_size=STYLE["body_size"] - 3,
            color=STYLE["highlight"],
        )
        height_label.next_to(axes.c2p(2, 1), RIGHT, buff=0.15)

        self.play(
            FadeIn(base_label),
            FadeIn(height_label),
        )

        formula = Tex(
            r"S = \frac{1}{2} \times 2 \times 2 = 2"
        )
        formula.set_color(STYLE["text"])
        formula.scale(0.9)
        formula.to_edge(DOWN, buff=0.35)

        # Khung nhấn quanh công thức -> mắt người xem dừng lại ở đây
        formula_box = SurroundingRectangle(formula, color=accent, buff=0.18, stroke_width=2)

        self.play(
            Write(formula),
            run_time=STYLE["slow"],
        )
        self.play(ShowCreation(formula_box), run_time=0.5)
        self.wait(STYLE["normal_pause"])

        # =========================
        # 6. CÔNG THỨC TÍCH PHÂN
        # =========================
        self.play(
            FadeOut(title),
            FadeOut(axes),
            FadeOut(axis_labels),
            FadeOut(graph),
            FadeOut(triangle),
            FadeOut(base_label),
            FadeOut(height_label),
            FadeOut(formula),
            FadeOut(formula_box),
            run_time=STYLE["normal"],
        )

        final_title = self.make_title("Kết quả")
        final_title.move_to(UP * 1.5)

        integral_formula = Tex(
            r"\int_0^2 x\,dx = 2"
        )
        integral_formula.set_color(STYLE["highlight"])
        integral_formula.scale(1.4)

        # "Thẻ" nền mềm phía sau công thức -> giống thumbnail/ slide chuyên nghiệp
        card = RoundedRectangle(
            width=integral_formula.get_width() + 1.4,
            height=integral_formula.get_height() + 0.9,
            corner_radius=0.25,
            color=accent,
            fill_color=STYLE["surface"],
            fill_opacity=0.18,
            stroke_width=2,
        )
        card.move_to(integral_formula)

        final_message = Text(
            "Tích phân giúp ta tính diện tích dưới đường cong.",
            font_size=STYLE["body_size"] - 3,
            color=STYLE["text"],
        )
        final_message.move_to(DOWN * 1.8)

        self.play(
            Write(final_title),
            run_time=STYLE["normal"],
        )
        self.play(
            GrowFromCenter(card),
            Write(integral_formula),
            run_time=STYLE["slow"],
        )
        self.play(Indicate(integral_formula, color=accent, scale_factor=1.08))
        self.play(
            FadeIn(final_message, shift=UP * 0.15),
            run_time=STYLE["normal"],
        )

        self.wait(STYLE["long_pause"])