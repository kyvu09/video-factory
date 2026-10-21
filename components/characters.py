"""
Thư viện nhân vật giáo viên và minh họa cho Video Factory.
"""
from manimlib import *
import numpy as np


class StickmanTeacher(VGroup):
    """
    Nhân vật thầy giáo hoạt hình dạng stickman (có kính, que chỉ bảng, vẫy tay).
    Phù hợp cho các video bài giảng giáo dục, giải thích toán và lập trình.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.center_pos = np.array([-4.8, -0.6, 0.0])

        # 1. Đầu & Khuôn mặt
        head_center = self.center_pos + UP * 1.85
        self.head_center = head_center
        self.head = Circle(radius=0.58).set_stroke(color=BLACK, width=4.0).set_fill(color=WHITE, opacity=1.0).move_to(head_center)

        # Kính mắt
        glass_r = 0.13
        self.glass_l = Circle(radius=glass_r).set_stroke(color=BLACK, width=2.8).set_fill(opacity=0).move_to(head_center + LEFT * 0.16 + UP * 0.06)
        self.glass_r = Circle(radius=glass_r).set_stroke(color=BLACK, width=2.8).set_fill(opacity=0).move_to(head_center + RIGHT * 0.16 + UP * 0.06)
        self.bridge = Line(self.glass_l.get_right(), self.glass_r.get_left(), stroke_width=2.8).set_color(BLACK)
        self.temple_l = Line(self.glass_l.get_left(), head_center + LEFT * 0.58 + UP * 0.06, stroke_width=2.2).set_color(BLACK)
        self.temple_r = Line(self.glass_r.get_right(), head_center + RIGHT * 0.58 + UP * 0.06, stroke_width=2.2).set_color(BLACK)
        self.glasses_group = VGroup(self.glass_l, self.glass_r, self.bridge, self.temple_l, self.temple_r)

        # Mắt
        self.eye_l = Dot(self.glass_l.get_center(), radius=0.045).set_color(BLACK)
        self.eye_r = Dot(self.glass_r.get_center(), radius=0.045).set_color(BLACK)
        self.eyes_group = VGroup(self.eye_l, self.eye_r)

        # Lông mày
        self.brow_l = Arc(radius=0.14, start_angle=PI*0.15, angle=PI*0.7, stroke_width=2.8).set_color(BLACK)
        self.brow_l.next_to(self.glass_l, UP, buff=0.05)
        self.brow_r = Arc(radius=0.14, start_angle=PI*0.15, angle=PI*0.7, stroke_width=2.8).set_color(BLACK)
        self.brow_r.next_to(self.glass_r, UP, buff=0.05)
        self.eyebrows_group = VGroup(self.brow_l, self.brow_r)

        # Miệng cười
        self.mouth = Arc(
            radius=0.18,
            start_angle=-PI * 0.85,
            angle=PI * 0.7,
            stroke_width=3.2
        ).set_color(BLACK).move_to(head_center + DOWN * 0.22)

        self.head_group = VGroup(
            self.head,
            self.glasses_group,
            self.eyes_group,
            self.eyebrows_group,
            self.mouth
        )

        # 2. Thân & Cổ
        self.neck = head_center + DOWN * 0.58
        self.pelvis = self.neck + DOWN * 1.35
        self.torso = Line(self.neck, self.pelvis, stroke_width=4.5).set_color(BLACK)

        # 3. Chân & Bàn chân
        foot_l_pos = self.pelvis + DOWN * 1.3 + LEFT * 0.45
        foot_r_pos = self.pelvis + DOWN * 1.3 + RIGHT * 0.45
        self.leg_l = Line(self.pelvis, foot_l_pos, stroke_width=4.5).set_color(BLACK)
        self.leg_r = Line(self.pelvis, foot_r_pos, stroke_width=4.5).set_color(BLACK)
        self.foot_l = Line(foot_l_pos, foot_l_pos + LEFT * 0.22, stroke_width=4.0).set_color(BLACK)
        self.foot_r = Line(foot_r_pos, foot_r_pos + RIGHT * 0.22, stroke_width=4.0).set_color(BLACK)
        self.legs_group = VGroup(self.leg_l, self.leg_r, self.foot_l, self.foot_r)

        # 4. Tay
        self.shoulder_pos = self.neck + DOWN * 0.25

        # Tay trái (thả lỏng)
        hand_l_rest = self.shoulder_pos + DOWN * 0.85 + LEFT * 0.45
        self.arm_l = Line(self.shoulder_pos, hand_l_rest, stroke_width=3.8).set_color(BLACK)
        self.hand_l = Dot(hand_l_rest, radius=0.065).set_color(BLACK)
        self.left_arm_group = VGroup(self.arm_l, self.hand_l)

        # Tay phải (cầm que chỉ bảng)
        self.right_arm_group = self._build_pointing_arm(self.shoulder_pos + RIGHT * 2.0 + UP * 0.5)

        self.add(
            self.legs_group,
            self.torso,
            self.left_arm_group,
            self.right_arm_group,
            self.head_group
        )

    def _build_pointing_arm(self, target_pos):
        s = self.shoulder_pos
        to_target = target_pos - s
        dist = np.linalg.norm(to_target)
        unit_dir = RIGHT if dist < 1e-4 else to_target / dist

        elbow = s + unit_dir * 0.45 + DOWN * 0.12
        hand = elbow + unit_dir * 0.45 + UP * 0.08

        upper_arm = Line(s, elbow, stroke_width=3.8).set_color(BLACK)
        forearm = Line(elbow, hand, stroke_width=3.8).set_color(BLACK)
        hand_dot = Dot(hand, radius=0.065).set_color(BLACK)

        # Que chỉ bảng
        stick_len = 1.35
        stick_end = hand + unit_dir * stick_len
        pointer = Line(hand, stick_end, stroke_width=4.0).set_color("#854d0e")
        pointer_tip = Dot(stick_end, radius=0.08).set_color("#dc2626")

        return VGroup(upper_arm, forearm, hand_dot, pointer, pointer_tip)

    def get_pointer_tip_pos(self):
        """Lấy vị trí đầu que chỉ bảng để trỏ vào đối tượng."""
        return self.right_arm_group[-1].get_center()

    def create_pointing_arm_to(self, target_pos):
        """Tạo tư thế tay phải chỉ vào vị trí target_pos."""
        return self._build_pointing_arm(target_pos)

    def create_wave_left_arm(self, phase=0):
        """Tạo chuyển động vẫy tay trái chào người xem."""
        s = self.shoulder_pos
        elbow = s + UP * 0.4 + LEFT * 0.35
        hand = elbow + (UP * 0.45 + LEFT * 0.15 if phase == 0 else UP * 0.45 + RIGHT * 0.2)
        upper = Line(s, elbow, stroke_width=3.8).set_color(BLACK)
        fore = Line(elbow, hand, stroke_width=3.8).set_color(BLACK)
        palm = Dot(hand, radius=0.075).set_color(BLACK)
        return VGroup(upper, fore, palm)
