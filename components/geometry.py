"""
Thư viện hình học & công cụ hỗ trợ vẽ hình cho Video Factory.
"""
from manimlib import *
import numpy as np


def RightAngle(line1, line2, length=0.35, color=YELLOW, **kwargs):
    """
    Vẽ ký hiệu góc vuông giữa hai đường thẳng vuông góc trong ManimGL.
    line1: cạnh thứ nhất (thường là cạnh đáy)
    line2: cạnh thứ hai (thường là cạnh đứng)
    """
    p = line1.get_start()
    return VGroup(
        Line(p + UP * length, p + UP * length + RIGHT * length, color=color, **kwargs),
        Line(p + UP * length + RIGHT * length, p + RIGHT * length, color=color, **kwargs),
    )

class PythagorasFigure(VGroup):
    """
    Component hình học chuẩn mực: Tam giác vuông + 3 hình vuông dựng trên 3 cạnh.
    Tự động tính toán vector chính xác 100%, tích hợp nhãn cạnh & nhãn diện tích.
    Tất cả được đóng gói sẵn trong 1 VGroup chuẩn, chỉ cần gọi fit_in_left_zone(fig)!
    """
    def __init__(
        self,
        a: float = 2.4,
        b: float = 3.2,
        color_a: str = "#A78BFA",
        color_b: str = "#A78BFA",
        color_c: str = "#38BDF8",
        fill_opacity: float = 0.38,
        stroke_width: float = 2.6,
        **kwargs,
    ):
        super().__init__(**kwargs)
        c_pt = ORIGIN
        b_pt = RIGHT * a
        a_pt = UP * b

        # 1. Các cạnh tam giác
        self.side_a = Line(c_pt, b_pt, color=color_a, stroke_width=stroke_width)
        self.side_b = Line(c_pt, a_pt, color=color_b, stroke_width=stroke_width)
        self.side_c = Line(b_pt, a_pt, color=color_c, stroke_width=stroke_width + 0.8)
        self.triangle_lines = VGroup(self.side_a, self.side_b, self.side_c)

        # Ký hiệu góc vuông
        self.right_angle = RightAngle(self.side_a, self.side_b, length=min(0.35, a * 0.15))

        # 2. Ba hình vuông mở rộng ra ngoài
        self.square_a = Polygon(
            c_pt, b_pt, b_pt + DOWN * a, c_pt + DOWN * a,
            color=color_a, fill_color=color_a, fill_opacity=fill_opacity, stroke_width=stroke_width
        ).set_z_index(-1)

        self.square_b = Polygon(
            c_pt, a_pt, a_pt + LEFT * b, c_pt + LEFT * b,
            color=color_b, fill_color=color_b, fill_opacity=fill_opacity, stroke_width=stroke_width
        ).set_z_index(-1)

        v_hyp = a_pt - b_pt
        n_hyp = np.array([-v_hyp[1], v_hyp[0], 0])
        if n_hyp[0] < 0:
            n_hyp = -n_hyp
        n_hyp = normalize(n_hyp) * np.linalg.norm(v_hyp)

        self.square_c = Polygon(
            b_pt, a_pt, a_pt + n_hyp, b_pt + n_hyp,
            color=color_c, fill_color=color_c, fill_opacity=fill_opacity + 0.1, stroke_width=stroke_width + 0.6
        ).set_z_index(-1)

        # 3. Nhãn cạnh và nhãn diện tích
        self.label_a = Tex("a", font_size=24, color=color_a).next_to(self.side_a, DOWN, buff=0.12)
        self.label_b = Tex("b", font_size=24, color=color_b).next_to(self.side_b, LEFT, buff=0.12)
        self.label_c = Tex("c", font_size=24, color=color_c).next_to(self.side_c.get_center(), UR, buff=0.12)

        self.text_sq_a = Tex("a^2", font_size=26, color="#F8FAFC").move_to(self.square_a.get_center())
        self.text_sq_b = Tex("b^2", font_size=26, color="#F8FAFC").move_to(self.square_b.get_center())
        self.text_sq_c = Tex("c^2", font_size=32, color=color_c).move_to(self.square_c.get_center())

        self.add(
            self.square_a, self.square_b, self.square_c,
            self.side_a, self.side_b, self.side_c,
            self.right_angle,
            self.label_a, self.label_b, self.label_c,
            self.text_sq_a, self.text_sq_b, self.text_sq_c
        )

