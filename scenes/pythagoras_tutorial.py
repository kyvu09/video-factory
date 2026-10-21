from manimlib import *
import numpy as np

class StickmanTeacher(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.center_pos = np.array([-4.8, -0.6, 0.0])

        # 1. Head & Face
        head_center = self.center_pos + UP * 1.85
        self.head_center = head_center
        self.head = Circle(radius=0.58).set_stroke(color=BLACK, width=4.0).set_fill(color=WHITE, opacity=1.0).move_to(head_center)

        # Glasses
        glass_r = 0.13
        self.glass_l = Circle(radius=glass_r).set_stroke(color=BLACK, width=2.8).set_fill(opacity=0).move_to(head_center + LEFT * 0.16 + UP * 0.06)
        self.glass_r = Circle(radius=glass_r).set_stroke(color=BLACK, width=2.8).set_fill(opacity=0).move_to(head_center + RIGHT * 0.16 + UP * 0.06)
        self.bridge = Line(self.glass_l.get_right(), self.glass_r.get_left(), stroke_width=2.8).set_color(BLACK)
        self.temple_l = Line(self.glass_l.get_left(), head_center + LEFT * 0.58 + UP * 0.06, stroke_width=2.2).set_color(BLACK)
        self.temple_r = Line(self.glass_r.get_right(), head_center + RIGHT * 0.58 + UP * 0.06, stroke_width=2.2).set_color(BLACK)
        self.glasses_group = VGroup(self.glass_l, self.glass_r, self.bridge, self.temple_l, self.temple_r)

        # Eyes (small round dots)
        self.eye_l = Dot(self.glass_l.get_center(), radius=0.045).set_color(BLACK)
        self.eye_r = Dot(self.glass_r.get_center(), radius=0.045).set_color(BLACK)
        self.eyes_group = VGroup(self.eye_l, self.eye_r)

        # Eyebrows
        self.brow_l = Arc(radius=0.14, start_angle=PI*0.15, angle=PI*0.7, stroke_width=2.8).set_color(BLACK)
        self.brow_l.next_to(self.glass_l, UP, buff=0.05)
        self.brow_r = Arc(radius=0.14, start_angle=PI*0.15, angle=PI*0.7, stroke_width=2.8).set_color(BLACK)
        self.brow_r.next_to(self.glass_r, UP, buff=0.05)
        self.eyebrows_group = VGroup(self.brow_l, self.brow_r)

        # Mouth (Smile)
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

        # 2. Torso & Neck
        self.neck = head_center + DOWN * 0.58
        self.pelvis = self.neck + DOWN * 1.35
        self.torso = Line(self.neck, self.pelvis, stroke_width=4.5).set_color(BLACK)

        # 3. Legs & Feet
        foot_l_pos = self.pelvis + DOWN * 1.3 + LEFT * 0.45
        foot_r_pos = self.pelvis + DOWN * 1.3 + RIGHT * 0.45
        self.leg_l = Line(self.pelvis, foot_l_pos, stroke_width=4.5).set_color(BLACK)
        self.leg_r = Line(self.pelvis, foot_r_pos, stroke_width=4.5).set_color(BLACK)
        self.foot_l = Line(foot_l_pos, foot_l_pos + LEFT * 0.22, stroke_width=4.0).set_color(BLACK)
        self.foot_r = Line(foot_r_pos, foot_r_pos + RIGHT * 0.22, stroke_width=4.0).set_color(BLACK)
        self.legs_group = VGroup(self.leg_l, self.leg_r, self.foot_l, self.foot_r)

        # 4. Arms
        self.shoulder_pos = self.neck + DOWN * 0.25

        # Left Arm (Resting)
        hand_l_rest = self.shoulder_pos + DOWN * 0.85 + LEFT * 0.45
        self.arm_l = Line(self.shoulder_pos, hand_l_rest, stroke_width=3.8).set_color(BLACK)
        self.hand_l = Dot(hand_l_rest, radius=0.065).set_color(BLACK)
        self.left_arm_group = VGroup(self.arm_l, self.hand_l)

        # Right Arm & Pointer stick
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

        # Pointer stick
        stick_len = 1.35
        stick_end = hand + unit_dir * stick_len
        pointer = Line(hand, stick_end, stroke_width=4.0).set_color("#854d0e")
        pointer_tip = Dot(stick_end, radius=0.08).set_color("#dc2626")

        return VGroup(upper_arm, forearm, hand_dot, pointer, pointer_tip)

    def get_pointer_tip_pos(self):
        return self.right_arm_group[-1].get_center()

    def create_pointing_arm_to(self, target_pos):
        return self._build_pointing_arm(target_pos)

    def create_wave_left_arm(self, phase=0):
        s = self.shoulder_pos
        elbow = s + UP * 0.4 + LEFT * 0.35
        hand = elbow + (UP * 0.45 + LEFT * 0.15 if phase == 0 else UP * 0.45 + RIGHT * 0.2)
        upper = Line(s, elbow, stroke_width=3.8).set_color(BLACK)
        fore = Line(elbow, hand, stroke_width=3.8).set_color(BLACK)
        palm = Dot(hand, radius=0.075).set_color(BLACK)
        return VGroup(upper, fore, palm)

    def create_rest_left_arm(self):
        hand_l_rest = self.shoulder_pos + DOWN * 0.85 + LEFT * 0.45
        arm = Line(self.shoulder_pos, hand_l_rest, stroke_width=3.8).set_color(BLACK)
        hand = Dot(hand_l_rest, radius=0.065).set_color(BLACK)
        return VGroup(arm, hand)

    def create_thumbs_up_left_arm(self):
        s = self.shoulder_pos
        elbow = s + LEFT * 0.45 + DOWN * 0.1
        hand = elbow + LEFT * 0.35 + UP * 0.4
        upper = Line(s, elbow, stroke_width=3.8).set_color(BLACK)
        fore = Line(elbow, hand, stroke_width=3.8).set_color(BLACK)
        fist = Dot(hand, radius=0.09).set_color(BLACK)
        thumb = Line(hand, hand + UP * 0.3, stroke_width=4.5).set_color(BLACK)
        return VGroup(upper, fore, fist, thumb)

    def create_surprised_head(self):
        head_c = self.head_center
        head = Circle(radius=0.58).set_stroke(color=BLACK, width=4.0).set_fill(color=WHITE, opacity=1.0).move_to(head_c)
        glasses = self.glasses_group.copy()
        eye_l = Dot(self.glass_l.get_center(), radius=0.065).set_color(BLACK)
        eye_r = Dot(self.glass_r.get_center(), radius=0.065).set_color(BLACK)
        brow_l = Arc(radius=0.15, start_angle=PI*0.1, angle=PI*0.8, stroke_width=3.2).set_color(BLACK)
        brow_l.next_to(self.glass_l, UP, buff=0.14)
        brow_r = Arc(radius=0.15, start_angle=PI*0.1, angle=PI*0.8, stroke_width=3.2).set_color(BLACK)
        brow_r.next_to(self.glass_r, UP, buff=0.14)
        mouth = Ellipse(width=0.22, height=0.32, stroke_width=3.2).set_stroke(color=BLACK).set_fill(color="#334155", opacity=0.9).move_to(head_c + DOWN * 0.24)
        return VGroup(head, glasses, VGroup(eye_l, eye_r), VGroup(brow_l, brow_r), mouth)

    def create_smiling_head(self):
        head_c = self.head_center
        head = Circle(radius=0.58).set_stroke(color=BLACK, width=4.0).set_fill(color=WHITE, opacity=1.0).move_to(head_c)
        glasses = self.glasses_group.copy()
        eyes = VGroup(
            Dot(self.glass_l.get_center(), radius=0.045).set_color(BLACK),
            Dot(self.glass_r.get_center(), radius=0.045).set_color(BLACK)
        )
        brows = VGroup(
            Arc(radius=0.14, start_angle=PI*0.15, angle=PI*0.7, stroke_width=2.8).set_color(BLACK).next_to(self.glass_l, UP, buff=0.05),
            Arc(radius=0.14, start_angle=PI*0.15, angle=PI*0.7, stroke_width=2.8).set_color(BLACK).next_to(self.glass_r, UP, buff=0.05)
        )
        mouth = Arc(
            radius=0.22,
            start_angle=-PI * 0.88,
            angle=PI * 0.76,
            stroke_width=3.5
        ).set_color(BLACK).move_to(head_c + DOWN * 0.20)
        return VGroup(head, glasses, eyes, brows, mouth)


class PythagorasTeacherScene(Scene):
    default_camera_config = {"background_color": "#F8FAFC"}

    def construct(self):
        # 0. Minimalist Teacher Blackboard Canvas
        board_bg = RoundedRectangle(
            width=9.2,
            height=6.4,
            corner_radius=0.22,
            stroke_width=2.0
        ).set_stroke(color="#cbd5e1").set_fill(color="#ffffff", opacity=0.98).move_to(np.array([1.8, -0.3, 0.0]))

        title_box = VGroup(
            Text("ĐỊNH LÝ PYTAGO", font_size=28, weight="BOLD").set_color("#0f172a"),
            Text("Trong tam giác vuông: a² + b² = c²", font_size=16).set_color("#475569")
        ).arrange(DOWN, buff=0.10).move_to(np.array([1.8, 2.35, 0.0]))

        self.add(board_bg)
        self.play(FadeIn(title_box, UP), run_time=0.8)

        # 1. Spawn Stickman Teacher
        teacher = StickmanTeacher()
        self.play(FadeIn(teacher, RIGHT), run_time=1.0)
        self.wait(0.5)

        speech_bubble = None

        def show_dialogue(text):
            nonlocal speech_bubble
            if speech_bubble:
                self.play(FadeOut(speech_bubble), run_time=0.25)
            
            txt = Text(text, font_size=16, alignment="CENTER").set_color("#0f172a")
            bg = RoundedRectangle(
                width=txt.get_width() + 0.55,
                height=txt.get_height() + 0.4,
                corner_radius=0.15,
                stroke_width=1.8
            ).set_stroke(color="#94a3b8").set_fill(color="#f1f5f9", opacity=1.0)
            bubble = VGroup(bg, txt).move_to(np.array([-4.5, 2.7, 0.0]))
            self.play(FadeIn(bubble, UP * 0.25), run_time=0.4)
            speech_bubble = bubble

        # Greeting & Waving
        show_dialogue("Xin chào các em!\nThầy là giáo viên Toán.")
        wave1 = teacher.create_wave_left_arm(phase=0)
        wave2 = teacher.create_wave_left_arm(phase=1)
        self.play(Transform(teacher.left_arm_group, wave1), run_time=0.35)
        self.play(Transform(teacher.left_arm_group, wave2), run_time=0.3)
        self.play(Transform(teacher.left_arm_group, wave1), run_time=0.3)
        self.play(Transform(teacher.left_arm_group, teacher.create_rest_left_arm()), run_time=0.35)
        self.wait(0.5)

        show_dialogue("Hôm nay chúng ta cùng học\nĐịnh lý Pytago nhé!")
        self.wait(1.0)

        # 2. Draw Right Triangle
        # C is right-angle vertex, B is base right vertex, A is top vertex
        C = np.array([-1.8, -1.8, 0.0])
        B = np.array([0.9, -1.8, 0.0])    # Base length = 2.7 (representing b = 4 cm)
        A = np.array([-1.8, 0.25, 0.0])   # Height = 2.05 (representing a = 3 cm)

        side_a = Line(C, A, stroke_width=6.0).set_color("#ea580c") # Cam nhạt (3 cm)
        side_b = Line(C, B, stroke_width=6.0).set_color("#0284c7") # Xanh nhạt (4 cm)
        side_c = Line(A, B, stroke_width=7.0).set_color("#1e3a8a") # Xanh đậm (5 cm)

        # Right angle indicator
        right_square = Square(side_length=0.30, stroke_width=2.5).set_stroke(color="#64748b").set_fill(opacity=0)
        right_square.move_to(C + UR * 0.15)

        # Labels
        label_a = Text("a = 3 cm", font_size=19, weight="BOLD").set_color("#ea580c").next_to(side_a, LEFT, buff=0.15)
        label_b = Text("b = 4 cm", font_size=19, weight="BOLD").set_color("#0284c7").next_to(side_b, DOWN, buff=0.15)
        
        # Hypotenuse label
        label_c_main = Text("c = 5 cm", font_size=19, weight="BOLD").set_color("#1e3a8a")
        label_c_sub = Text("(Cạnh huyền)", font_size=14, weight="BOLD").set_color("#1e3a8a")
        label_c = VGroup(label_c_main, label_c_sub).arrange(DOWN, buff=0.06).move_to(np.array([-0.1, -0.4, 0.0]))

        show_dialogue("Quan sát hình tam giác vuông\nbên cạnh này nhé!")
        self.play(
            ShowCreation(side_a),
            ShowCreation(side_b),
            ShowCreation(side_c),
            ShowCreation(right_square),
            run_time=1.5
        )
        self.play(Write(label_a), Write(label_b), Write(label_c), run_time=1.0)
        self.wait(0.5)

        # 3. Teacher points at Right Angle
        show_dialogue("Trước hết, đây là góc vuông 90°.")
        arm_point_angle = teacher.create_pointing_arm_to(C)
        self.play(Transform(teacher.right_arm_group, arm_point_angle), run_time=0.6)
        highlight_box = Square(side_length=0.45, stroke_width=3).set_stroke(color="#ef4444").set_fill(opacity=0).move_to(C + UR * 0.15)
        self.play(ShowCreationThenFadeOut(highlight_box), run_time=0.8)
        self.wait(0.5)

        # Teacher points at Leg 1 (3 cm)
        show_dialogue("Cạnh góc vuông thứ nhất\ndài a = 3 cm.")
        arm_point_a = teacher.create_pointing_arm_to(side_a.get_center())
        self.play(Transform(teacher.right_arm_group, arm_point_a), run_time=0.6)
        self.play(side_a.animate.set_stroke(width=9), run_time=0.3)
        self.play(side_a.animate.set_stroke(width=6), run_time=0.3)
        self.wait(0.5)

        # Teacher points at Leg 2 (4 cm)
        show_dialogue("Cạnh góc vuông thứ hai\ndài b = 4 cm.")
        arm_point_b = teacher.create_pointing_arm_to(side_b.get_center())
        self.play(Transform(teacher.right_arm_group, arm_point_b), run_time=0.6)
        self.play(side_b.animate.set_stroke(width=9), run_time=0.3)
        self.play(side_b.animate.set_stroke(width=6), run_time=0.3)
        self.wait(0.5)

        # Teacher points at Hypotenuse (5 cm)
        show_dialogue("Và cạnh đối diện góc vuông\nlà cạnh huyền: c = 5 cm!")
        arm_point_c = teacher.create_pointing_arm_to(side_c.get_center())
        self.play(Transform(teacher.right_arm_group, arm_point_c), run_time=0.6)
        self.play(side_c.animate.set_stroke(width=10), run_time=0.3)
        self.play(side_c.animate.set_stroke(width=7), run_time=0.3)
        self.wait(0.8)

        # 4. Squaring concept & Calculations on Right Board Column
        calc_x = 3.9
        show_dialogue("Bình phương một cạnh là gì?\nLà lấy cạnh đó nhân với chính nó!")
        self.wait(1.2)

        # 3 x 3 = 9
        eq1 = Text("3 × 3 = 9", font_size=23, weight="BOLD").set_color("#ea580c")
        eq1.move_to(np.array([calc_x, 1.2, 0.0]))
        show_dialogue("Với cạnh 3 cm:\nTa có 3 × 3 = 9.")
        self.play(Write(eq1), run_time=0.8)

        # Point to 3 then to 9
        arm_point_num3 = teacher.create_pointing_arm_to(eq1.get_left() + RIGHT * 0.3)
        self.play(Transform(teacher.right_arm_group, arm_point_num3), run_time=0.5)
        self.wait(0.3)
        arm_point_res9 = teacher.create_pointing_arm_to(eq1.get_right())
        self.play(Transform(teacher.right_arm_group, arm_point_res9), run_time=0.5)
        self.wait(0.8)

        # 4 x 4 = 16
        eq2 = Text("4 × 4 = 16", font_size=23, weight="BOLD").set_color("#0284c7")
        eq2.move_to(np.array([calc_x, 0.5, 0.0]))
        show_dialogue("Tương tự với cạnh 4 cm:\nTa có 4 × 4 = 16.")
        self.play(Write(eq2), run_time=0.8)

        # Point to 4 then to 16
        arm_point_num4 = teacher.create_pointing_arm_to(eq2.get_left() + RIGHT * 0.3)
        self.play(Transform(teacher.right_arm_group, arm_point_num4), run_time=0.5)
        self.wait(0.3)
        arm_point_res16 = teacher.create_pointing_arm_to(eq2.get_right())
        self.play(Transform(teacher.right_arm_group, arm_point_res16), run_time=0.5)
        self.wait(0.8)

        # Sum: 9 + 16 = 25
        eq3 = Text("9 + 16 = 25", font_size=25, weight="BOLD").set_color("#7c3aed")
        eq3.move_to(np.array([calc_x, -0.2, 0.0]))
        show_dialogue("Giờ ta cộng hai kết quả:\n9 + 16 = 25!")
        self.play(Write(eq3), run_time=0.8)

        # Point to sum
        arm_point_sum = teacher.create_pointing_arm_to(eq3.get_center())
        self.play(Transform(teacher.right_arm_group, arm_point_sum), run_time=0.5)
        self.wait(0.4)

        # 5. Teacher Surprise Reaction!
        show_dialogue("Ồ! Nhìn kết quả 25 kìa!\nCác em có nhận ra điều gì không?")
        surprised_head = teacher.create_surprised_head()
        self.play(
            Transform(teacher.head_group, surprised_head),
            teacher.head_group.animate.shift(UP * 0.08),
            run_time=0.4
        )
        self.wait(1.0)

        # 5 x 5 = 25 and Hypotenuse
        eq4 = Text("5 × 5 = 25", font_size=23, weight="BOLD").set_color("#1e3a8a")
        eq4.move_to(np.array([calc_x, -0.9, 0.0]))
        show_dialogue("Chính xác! 5 × 5 = 25!\nĐúng bằng bình phương cạnh huyền!")
        self.play(Write(eq4), run_time=0.8)

        # Point to 5, nod head
        arm_point_5 = teacher.create_pointing_arm_to(eq4.get_center())
        self.play(Transform(teacher.right_arm_group, arm_point_5), run_time=0.5)
        # Nod head
        self.play(teacher.head_group.animate.shift(DOWN * 0.12), run_time=0.25)
        self.play(teacher.head_group.animate.shift(UP * 0.12), run_time=0.25)
        self.wait(0.5)

        # Point pointer back to hypotenuse
        show_dialogue("Bình phương 2 cạnh góc vuông\nđúng bằng bình phương cạnh huyền!")
        arm_point_c_final = teacher.create_pointing_arm_to(side_c.get_center())
        self.play(Transform(teacher.right_arm_group, arm_point_c_final), run_time=0.6)
        self.play(Indicate(side_c, color="#2563eb", scale_factor=1.1), run_time=0.8)
        self.wait(1.0)

        # 6. General Formula Card at bottom
        formula_text = Text("a² + b² = c²", font_size=32, weight="BOLD").set_color("#0f172a")
        formula_box = RoundedRectangle(
            width=4.2,
            height=1.05,
            corner_radius=0.18,
            stroke_width=2.5
        ).set_stroke(color="#2563eb").set_fill(color="#eff6ff", opacity=0.98)
        formula_label = Text("Định lý Pytago tổng quát", font_size=14, weight="BOLD").set_color("#1d4ed8")
        formula_label.next_to(formula_box, UP, buff=0.08)

        formula_group = VGroup(formula_box, formula_text, formula_label).move_to(np.array([calc_x, -2.1, 0.0]))

        show_dialogue("Và đây chính là\nĐịnh lý Pytago tổng quát:")
        self.play(FadeIn(formula_group, UP * 0.35), run_time=1.0)

        # Teacher points at general formula
        arm_point_formula = teacher.create_pointing_arm_to(formula_group.get_center())
        self.play(Transform(teacher.right_arm_group, arm_point_formula), run_time=0.6)
        self.wait(1.0)

        # 7. Conclusion: Smile & Thumbs Up!
        show_dialogue("Rất dễ hiểu đúng không nào?\nHãy luôn ghi nhớ nhé! 👍")
        smiling_head = teacher.create_smiling_head()
        thumbs_up_arm = teacher.create_thumbs_up_left_arm()
        self.play(
            Transform(teacher.head_group, smiling_head),
            Transform(teacher.left_arm_group, thumbs_up_arm),
            run_time=0.6
        )
        self.wait(2.5)

        if speech_bubble:
            self.play(FadeOut(speech_bubble), run_time=0.8)
        self.wait(1.5)
