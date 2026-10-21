from manimlib import *
import numpy as np

# 1. Tương thích giữa ManimGL và Manim Community
GRAY = GREY
Create = ShowCreation

# Ký hiệu góc vuông cho ManimGL
def RightAngle(line1, line2, length=0.35, color=YELLOW, **kwargs):
    p = line1.get_start()
    return VGroup(
        Line(p + UP * length, p + UP * length + RIGHT * length, color=color),
        Line(p + UP * length + RIGHT * length, p + RIGHT * length, color=color),
    )

# Mặc định dùng font Segoe UI để không bị lỗi tiếng Việt
_OrigText = Text
class Text(_OrigText):
    def __init__(self, text, font="Segoe UI", **kwargs):
        super().__init__(text, font=font, **kwargs)


class HelloScene(Scene):
    def construct(self):
        # ==========================================
        # 1. TIÊU ĐỀ
        # ==========================================
        tieu_de = Text("ĐỊNH LÝ PYTAGO", font_size=40, color=YELLOW, weight=BOLD)
        phu_de_td = Text("Công thức kỳ diệu trong tam giác vuông", font_size=22, color=GREY)
        phu_de_td.next_to(tieu_de, DOWN, buff=0.2)
        nhom_td = VGroup(tieu_de, phu_de_td)

        self.play(Write(tieu_de), FadeIn(phu_de_td, shift=UP * 0.3))
        self.wait(1)

        # Thu nhỏ tiêu đề và đưa lên góc trên
        self.play(
            nhom_td.animate.scale(0.7).to_corner(UP + LEFT, buff=0.4),
            run_time=1
        )

        # ==========================================
        # 2. VẼ TAM GIÁC VUÔNG (BÊN TRÁI MÀN HÌNH)
        # ==========================================
        c_pt = np.array([-4.5, -1.8, 0])      # Đỉnh góc vuông C
        b_pt = np.array([-1.5, -1.8, 0])      # Đáy B (cạnh ngắn a)
        a_pt = np.array([-4.5, 2.2, 0])       # Đỉnh đứng A (cạnh ngắn b)

        tam_giac = Polygon(c_pt, b_pt, a_pt, color=WHITE, stroke_width=4)
        tam_giac.set_fill(BLUE_E, opacity=0.3)

        # Ký hiệu góc vuông & các cạnh
        canh_day = Line(c_pt, b_pt)
        canh_dung = Line(c_pt, a_pt)
        canh_huyen = Line(b_pt, a_pt)
        goc_vuong = RightAngle(canh_day, canh_dung, length=0.35, color=YELLOW)

        nhan_a = Text("a (cạnh ngắn)", font_size=20, color=TEAL).next_to(canh_day, DOWN, buff=0.2)
        nhan_b = Text("b (cạnh ngắn)", font_size=20, color=BLUE_B).next_to(canh_dung, LEFT, buff=0.2)
        nhan_c = Text("c (cạnh huyền)", font_size=22, color=YELLOW).next_to(canh_huyen.get_center(), UP + RIGHT, buff=0.2)

        self.play(Create(tam_giac), Create(goc_vuong))
        self.play(Write(nhan_a), Write(nhan_b), Write(nhan_c))
        self.wait(1.5)

        # ==========================================
        # 3. ĐỊNH LÝ TỔNG QUÁT: a² + b² = c²
        # ==========================================
        hop_ct = RoundedRectangle(corner_radius=0.2, height=1.5, width=5.5, color=YELLOW, fill_color=BLACK, fill_opacity=0.8)
        hop_ct.to_edge(RIGHT, buff=0.8).shift(UP * 1.5)

        ct_text = Text("a² + b² = c²", font_size=42, color=YELLOW, weight=BOLD)
        ct_text.move_to(hop_ct.get_center()).shift(UP * 0.2)

        ct_giai_thich = Text("Tổng bình phương 2 cạnh ngắn = Bình phương cạnh huyền", font_size=15, color=WHITE)
        ct_giai_thich.next_to(ct_text, DOWN, buff=0.2)

        nhom_cong_thuc = VGroup(hop_ct, ct_text, ct_giai_thich)
        self.play(FadeIn(nhom_cong_thuc, shift=LEFT * 0.5))
        self.wait(2)

        # ==========================================
        # 4. VÍ DỤ CỤ THỂ: a = 3cm, b = 4cm, c = ?
        # ==========================================
        nhan_a_so = Text("a = 3 cm", font_size=22, color=TEAL).next_to(canh_day, DOWN, buff=0.2)
        nhan_b_so = Text("b = 4 cm", font_size=22, color=BLUE_B).next_to(canh_dung, LEFT, buff=0.2)
        nhan_c_hoi = Text("c = ? cm", font_size=24, color=RED, weight=BOLD).next_to(canh_huyen.get_center(), UP + RIGHT, buff=0.2)

        self.play(
            Transform(nhan_a, nhan_a_so),
            Transform(nhan_b, nhan_b_so),
            Transform(nhan_c, nhan_c_hoi)
        )
        self.wait(1)

        # Bảng tính toán các bước
        vd_tieude = Text("Ví dụ minh họa:", font_size=24, color=GOLD, weight=BOLD)
        vd_tieude.next_to(hop_ct, DOWN, buff=0.4).align_to(hop_ct, LEFT)

        dong_1 = Text("• Bình phương cạnh 1:  3 × 3 = 9", font_size=20, color=TEAL)
        dong_1.next_to(vd_tieude, DOWN, buff=0.25).align_to(vd_tieude, LEFT)

        dong_2 = Text("• Bình phương cạnh 2:  4 × 4 = 16", font_size=20, color=BLUE_B)
        dong_2.next_to(dong_1, DOWN, buff=0.2).align_to(vd_tieude, LEFT)

        dong_3 = Text("• Cộng lại:  9 + 16 = 25", font_size=20, color=WHITE, weight=BOLD)
        dong_3.next_to(dong_2, DOWN, buff=0.2).align_to(vd_tieude, LEFT)

        dong_4 = Text("• Vì 5 × 5 = 25  ➜  c = 5 cm!", font_size=22, color=GREEN_B, weight=BOLD)
        dong_4.next_to(dong_3, DOWN, buff=0.25).align_to(vd_tieude, LEFT)

        self.play(FadeIn(vd_tieude, shift=UP * 0.2))
        self.play(Write(dong_1))
        self.wait(0.8)
        self.play(Write(dong_2))
        self.wait(0.8)
        self.play(Write(dong_3))
        self.wait(1)
        self.play(Write(dong_4))

        # Hiệu ứng sáng cạnh huyền và đổi thành 5 cm
        nhan_c_dap_an = Text("c = 5 cm", font_size=26, color=GREEN_A, weight=BOLD).next_to(canh_huyen.get_center(), UP + RIGHT, buff=0.2)
        canh_huyen_sang = Line(b_pt, a_pt, color=GREEN, stroke_width=6)

        self.play(
            Transform(nhan_c, nhan_c_dap_an),
            Create(canh_huyen_sang),
            run_time=1
        )
        self.play(FadeOut(canh_huyen_sang), run_time=0.5)
        self.wait(1.5)

        # ==========================================
        # 5. KẾT LUẬN & Ý NGHĨA
        # ==========================================
        nhom_vd = VGroup(vd_tieude, dong_1, dong_2, dong_3, dong_4)

        hop_ketluan = RoundedRectangle(corner_radius=0.2, height=1.4, width=6.2, color=GREEN, fill_color=BLACK, fill_opacity=0.9)
        hop_ketluan.next_to(hop_ct, DOWN, buff=0.5).align_to(hop_ct, LEFT)

        txt_kl1 = Text("💡 Ý NGHĨA ỨNG DỤNG:", font_size=20, color=GREEN, weight=BOLD)
        txt_kl2 = Text("Chỉ cần biết 2 cạnh bất kỳ trong tam giác vuông,", font_size=17, color=WHITE)
        txt_kl3 = Text("bạn sẽ tính ngay được cạnh còn lại mà không cần đo!", font_size=17, color=YELLOW)

        nhom_chu_kl = VGroup(txt_kl1, txt_kl2, txt_kl3).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        nhom_chu_kl.move_to(hop_ketluan.get_center())

        self.play(
            FadeOut(nhom_vd),
            FadeIn(hop_ketluan, shift=UP * 0.3),
            FadeIn(nhom_chu_kl, shift=UP * 0.3)
        )
        self.wait(2)