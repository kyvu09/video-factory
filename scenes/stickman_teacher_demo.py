from manim import *
import numpy as np

# Thiết lập font mặc định hỗ trợ tiếng Việt trên Windows
Text.set_default(font="Segoe UI")


class StickmanTeacherScene(Scene):
    def construct(self):
        # 1. Nền trắng tối giản
        self.camera.background_color = "#FFFFFF"

        C_BLACK = "#1A1A1A"
        C_BLUE = "#2563EB"       # Xanh dương cạnh đáy
        C_ORANGE = "#EA580C"     # Cam cạnh đứng
        C_NAVY = "#0F172A"       # Xanh đậm cạnh huyền
        C_GREEN = "#16A34A"      # Xanh lá kết quả
        C_SUB_BG = "#F1F5F9"     # Nền thanh phụ đề

        # ==========================================================
        # XÂY DỰNG NHÂN VẬT THẦY GIÁO STICKMAN
        # ==========================================================
        pos_x = -4.8
        head_center = np.array([pos_x, 0.7, 0])

        # Đầu hình tròn
        dau = Circle(radius=0.48, color=C_BLACK, stroke_width=3.5, fill_color=WHITE, fill_opacity=1)
        dau.move_to(head_center)

        # Cặp kính tròn
        kinh_trai = Circle(radius=0.12, color=C_BLACK, stroke_width=2.5, fill_color=WHITE, fill_opacity=0.6)
        kinh_trai.move_to(head_center + np.array([-0.14, 0.05, 0]))
        kinh_phai = Circle(radius=0.12, color=C_BLACK, stroke_width=2.5, fill_color=WHITE, fill_opacity=0.6)
        kinh_phai.move_to(head_center + np.array([0.14, 0.05, 0]))
        gong_kinh = Line(kinh_trai.get_right(), kinh_phai.get_left(), color=C_BLACK, stroke_width=2.5)
        gong_trai = Line(kinh_trai.get_left(), head_center + np.array([-0.45, 0.08, 0]), color=C_BLACK, stroke_width=2)
        gong_phai = Line(kinh_phai.get_right(), head_center + np.array([0.45, 0.08, 0]), color=C_BLACK, stroke_width=2)
        nhom_kinh = VGroup(kinh_trai, kinh_phai, gong_kinh, gong_trai, gong_phai)

        # Mắt & Lông mày
        mat_trai = Dot(kinh_trai.get_center(), radius=0.038, color=C_BLACK)
        mat_phai = Dot(kinh_phai.get_center(), radius=0.038, color=C_BLACK)
        nhom_mat = VGroup(mat_trai, mat_phai)

        long_may_trai = Line(head_center + np.array([-0.24, 0.22, 0]), head_center + np.array([-0.05, 0.24, 0]), color=C_BLACK, stroke_width=2.5)
        long_may_phai = Line(head_center + np.array([0.05, 0.24, 0]), head_center + np.array([0.24, 0.22, 0]), color=C_BLACK, stroke_width=2.5)
        nhom_long_may = VGroup(long_may_trai, long_may_phai)

        # Miệng cười
        mieng_cuoi = Arc(radius=0.18, start_angle=-5*PI/6, angle=2*PI/3, color=C_BLACK, stroke_width=3)
        mieng_cuoi.move_to(head_center + np.array([0, -0.22, 0]))
        nhom_khuon_mat = VGroup(dau, nhom_kinh, nhom_mat, nhom_long_may, mieng_cuoi)

        # Thân, vai và chân
        co = head_center + np.array([0, -0.48, 0])
        hong = head_center + np.array([0, -1.8, 0])
        than = Line(co, hong, color=C_BLACK, stroke_width=4)
        chan_trai = Line(hong, hong + np.array([-0.3, -1.2, 0]), color=C_BLACK, stroke_width=3.5)
        chan_phai = Line(hong, hong + np.array([0.3, -1.2, 0]), color=C_BLACK, stroke_width=3.5)
        nhom_chan = VGroup(chan_trai, chan_phai)
        vai = co + np.array([0, -0.2, 0])

        # Cánh tay trái mặc định
        khuyu_trai_default = vai + np.array([-0.4, -0.4, 0])
        tay_trai_default = khuyu_trai_default + np.array([-0.3, -0.4, 0])
        canh_tay_trai = VGroup(
            Line(vai, khuyu_trai_default, color=C_BLACK, stroke_width=3.5),
            Line(khuyu_trai_default, tay_trai_default, color=C_BLACK, stroke_width=3.5)
        )
        canh_tay_trai_default = canh_tay_trai.copy()

        # Hàm dựng cánh tay cầm que chỉ trỏ đến mục tiêu
        def tao_tay_chi(muc_tieu, do_dai_que=1.1):
            huong = muc_tieu - vai
            kc = np.linalg.norm(huong)
            u = huong / (kc + 1e-6)
            phap_tuyen = np.array([-u[1], u[0], 0])

            ban_tay = vai + u * min(kc * 0.45, 0.85) - phap_tuyen * 0.1
            khuyu_tay = (vai + ban_tay) / 2 - phap_tuyen * 0.22
            dau_que = ban_tay + u * do_dai_que

            return VGroup(
                Line(vai, khuyu_tay, color=C_BLACK, stroke_width=3.5),
                Line(khuyu_tay, ban_tay, color=C_BLACK, stroke_width=3.5),
                Line(ban_tay, dau_que, color="#854D0E", stroke_width=3.5),
                Dot(dau_que, radius=0.06, color=RED)
            )

        tay_phai_hien_tai = tao_tay_chi(head_center + np.array([1.2, -1.0, 0]), do_dai_que=0.8)
        thay_giao = VGroup(nhom_chan, than, canh_tay_trai, tay_phai_hien_tai, nhom_khuon_mat)

        # Thanh phụ đề
        khung_phu_de = RoundedRectangle(corner_radius=0.15, height=0.9, width=12.5, color="#CBD5E1", fill_color=C_SUB_BG, fill_opacity=0.95)
        khung_phu_de.to_edge(DOWN, buff=0.25)

        loi_giang_hien_tai = Text("Xin chào các em! Thầy là giáo viên Toán đây 👋", font_size=20, color=C_BLACK)
        loi_giang_hien_tai.move_to(khung_phu_de.get_center())

        def doi_loi_giang(cau_moi, run_time=0.4):
            nonlocal loi_giang_hien_tai
            cau_text = Text(cau_moi, font_size=20, color=C_BLACK)
            cau_text.move_to(khung_phu_de.get_center())
            self.play(Transform(loi_giang_hien_tai, cau_text), run_time=run_time)

        # ==========================================================
        # DIỄN HOẠT
        # ==========================================================
        self.add(khung_phu_de, loi_giang_hien_tai)
        self.play(FadeIn(thay_giao, shift=UP * 0.3), run_time=1)

        # Vẫy tay chào
        khuyu_vay = vai + np.array([-0.3, 0.3, 0])
        tay_vay_1 = khuyu_vay + np.array([-0.2, 0.45, 0])
        tay_vay_2 = khuyu_vay + np.array([-0.4, 0.35, 0])
        canh_tay_vay_1 = VGroup(Line(vai, khuyu_vay, color=C_BLACK, stroke_width=3.5), Line(khuyu_vay, tay_vay_1, color=C_BLACK, stroke_width=3.5))
        canh_tay_vay_2 = VGroup(Line(vai, khuyu_vay, color=C_BLACK, stroke_width=3.5), Line(khuyu_vay, tay_vay_2, color=C_BLACK, stroke_width=3.5))

        self.play(Transform(canh_tay_trai, canh_tay_vay_1), run_time=0.4)
        self.play(Transform(canh_tay_trai, canh_tay_vay_2), run_time=0.3)
        self.play(Transform(canh_tay_trai, canh_tay_vay_1), run_time=0.3)
        self.play(Transform(canh_tay_trai, canh_tay_trai_default), run_time=0.4)
        self.wait(0.5)

        doi_loi_giang("Hôm nay chúng ta sẽ cùng tìm hiểu về Định lý Pytago kỳ diệu nhé!")
        self.wait(1.5)

        # Vẽ tam giác vuông
        c_pt = np.array([-1.5, -1.6, 0])
        b_pt = np.array([1.2, -1.6, 0])
        a_pt = np.array([-1.5, 2.0, 0])

        tam_giac = Polygon(c_pt, b_pt, a_pt, color=C_NAVY, stroke_width=4.5)
        tam_giac.set_fill("#EFF6FF", opacity=0.7)
        goc_vuong = VGroup(
            Line(c_pt + UP * 0.35, c_pt + UP * 0.35 + RIGHT * 0.35, color=C_BLACK, stroke_width=2.5),
            Line(c_pt + UP * 0.35 + RIGHT * 0.35, c_pt + RIGHT * 0.35, color=C_BLACK, stroke_width=2.5)
        )
        canh_day = Line(c_pt, b_pt, color=C_BLUE, stroke_width=5)
        canh_dung = Line(c_pt, a_pt, color=C_ORANGE, stroke_width=5)
        canh_huyen = Line(b_pt, a_pt, color=C_NAVY, stroke_width=5.5)

        nhan_a = Text("a (cạnh ngắn)", font_size=18, color=C_BLUE, weight=BOLD).next_to(canh_day, DOWN, buff=0.18)
        nhan_b = Text("b (cạnh ngắn)", font_size=18, color=C_ORANGE, weight=BOLD).next_to(canh_dung, LEFT, buff=0.18)
        nhan_c = Text("c (cạnh huyền)", font_size=19, color=C_NAVY, weight=BOLD).next_to(canh_huyen.get_center(), UP + RIGHT, buff=0.18)

        doi_loi_giang("Định lý này chuyên dùng cho các tam giác có một góc vuông (tam giác vuông).")
        self.play(Create(tam_giac), Create(goc_vuong), Create(canh_day), Create(canh_dung), Create(canh_huyen))

        # Chỉ góc vuông & các cạnh
        self.play(Transform(tay_phai_hien_tai, tao_tay_chi(c_pt + np.array([0.2, 0.2, 0]))), run_time=0.8)
        self.wait(1.2)

        doi_loi_giang("Hai cạnh ngắn kẹp lấy góc vuông (gọi là hai cạnh góc vuông)...")
        self.play(Transform(tay_phai_hien_tai, tao_tay_chi(canh_day.get_center() + DOWN * 0.1)), Write(nhan_a), run_time=0.7)
        self.wait(0.8)
        self.play(Transform(tay_phai_hien_tai, tao_tay_chi(canh_dung.get_center() + LEFT * 0.1)), Write(nhan_b), run_time=0.7)
        self.wait(1)

        doi_loi_giang("...và một cạnh dài nhất nằm đối diện, gọi là cạnh huyền!")
        self.play(Transform(tay_phai_hien_tai, tao_tay_chi(canh_huyen.get_center() + UP * 0.1)), Write(nhan_c), run_time=0.8)
        self.wait(1.5)

        # Công thức định lý
        doi_loi_giang("Định lý: Tổng bình phương hai cạnh ngắn bằng bình phương cạnh huyền.")
        hop_ct = RoundedRectangle(corner_radius=0.15, height=1.35, width=4.6, color=C_NAVY, fill_color="#F8FAFC", fill_opacity=1)
        hop_ct.to_edge(RIGHT, buff=0.8).shift(UP * 1.8)
        ct_text = Text("a² + b² = c²", font_size=38, color=C_NAVY, weight=BOLD).move_to(hop_ct.get_center()).shift(UP * 0.18)
        ct_note = Text("Bình phương: nhân với chính nó", font_size=15, color="#64748B").next_to(ct_text, DOWN, buff=0.15)
        nhom_ct = VGroup(hop_ct, ct_text, ct_note)

        self.play(FadeIn(nhom_ct, shift=LEFT * 0.3), Transform(tay_phai_hien_tai, tao_tay_chi(hop_ct.get_left() + UP * 0.1)), run_time=0.8)
        self.wait(2)

        # Ví dụ 3 - 4 - 5
        doi_loi_giang("Ví dụ: nếu hai cạnh ngắn có độ dài lần lượt là 3 cm và 4 cm...")
        nhan_a_3 = Text("a = 3 cm", font_size=19, color=C_BLUE, weight=BOLD).next_to(canh_day, DOWN, buff=0.18)
        nhan_b_4 = Text("b = 4 cm", font_size=19, color=C_ORANGE, weight=BOLD).next_to(canh_dung, LEFT, buff=0.18)
        nhan_c_hoi = Text("c = ? cm", font_size=20, color=RED, weight=BOLD).next_to(canh_huyen.get_center(), UP + RIGHT, buff=0.18)

        self.play(Transform(nhan_a, nhan_a_3), Transform(nhan_b, nhan_b_4), Transform(nhan_c, nhan_c_hoi), run_time=0.8)
        self.wait(1)

        vd_header = Text("Tính toán từng bước:", font_size=20, color="#334155", weight=BOLD).next_to(hop_ct, DOWN, buff=0.35).align_to(hop_ct, LEFT)
        dong_1 = Text("• 3 × 3 = 9", font_size=21, color=C_BLUE, weight=BOLD).next_to(vd_header, DOWN, buff=0.22).align_to(vd_header, LEFT)
        dong_2 = Text("• 4 × 4 = 16", font_size=21, color=C_ORANGE, weight=BOLD).next_to(dong_1, DOWN, buff=0.2).align_to(vd_header, LEFT)
        dong_3 = Text("• Tổng: 9 + 16 = 25", font_size=22, color=C_BLACK, weight=BOLD).next_to(dong_2, DOWN, buff=0.2).align_to(vd_header, LEFT)
        dong_4 = Text("• 5 × 5 = 25  ➜  c = 5 cm!", font_size=22, color=C_GREEN, weight=BOLD).next_to(dong_3, DOWN, buff=0.25).align_to(vd_header, LEFT)

        doi_loi_giang("Đầu tiên: lấy 3 bình phương lên, tức là 3 × 3 = 9.")
        self.play(FadeIn(vd_header), Write(dong_1), Transform(tay_phai_hien_tai, tao_tay_chi(dong_1.get_left() + LEFT * 0.1)), run_time=0.8)
        self.wait(1.5)

        doi_loi_giang("Tiếp theo: 4 bình phương lên, tức là 4 × 4 = 16.")
        self.play(Write(dong_2), Transform(tay_phai_hien_tai, tao_tay_chi(dong_2.get_left() + LEFT * 0.1)), run_time=0.8)
        self.wait(1.5)

        doi_loi_giang("Sau đó cộng hai số lại với nhau: 9 + 16 = 25!")
        self.play(Write(dong_3), Transform(tay_phai_hien_tai, tao_tay_chi(dong_3.get_left() + LEFT * 0.1)), run_time=0.8)

        # Biểu cảm mở to mắt, nhướng mày, miệng chữ O ngạc nhiên
        mat_trai_to = Dot(kinh_trai.get_center(), radius=0.06, color=C_BLACK)
        mat_phai_to = Dot(kinh_phai.get_center(), radius=0.06, color=C_BLACK)
        long_may_nhuong_trai = Line(head_center + np.array([-0.24, 0.28, 0]), head_center + np.array([-0.05, 0.32, 0]), color=C_BLACK, stroke_width=3)
        long_may_nhuong_phai = Line(head_center + np.array([0.05, 0.32, 0]), head_center + np.array([0.24, 0.28, 0]), color=C_BLACK, stroke_width=3)
        mieng_chu_o = Circle(radius=0.1, color=C_BLACK, stroke_width=3, fill_color=WHITE, fill_opacity=1).move_to(head_center + np.array([0, -0.22, 0]))

        self.play(
            Transform(nhom_mat, VGroup(mat_trai_to, mat_phai_to)),
            Transform(nhom_long_may, VGroup(long_may_nhuong_trai, long_may_nhuong_phai)),
            Transform(mieng_cuoi, mieng_chu_o),
            run_time=0.4
        )
        self.wait(1.2)

        # Giải thích 5 x 5 = 25, gật đầu
        doi_loi_giang("Và vì 5 × 5 = 25, nên cạnh huyền dài đúng bằng 5 cm!")
        self.play(
            Transform(nhom_mat, VGroup(Dot(kinh_trai.get_center(), radius=0.038, color=C_BLACK), Dot(kinh_phai.get_center(), radius=0.038, color=C_BLACK))),
            Transform(nhom_long_may, VGroup(Line(head_center + np.array([-0.24, 0.22, 0]), head_center + np.array([-0.05, 0.24, 0]), color=C_BLACK, stroke_width=2.5), Line(head_center + np.array([0.05, 0.24, 0]), head_center + np.array([0.24, 0.22, 0]), color=C_BLACK, stroke_width=2.5))),
            Transform(mieng_cuoi, Arc(radius=0.18, start_angle=-5*PI/6, angle=2*PI/3, color=C_BLACK, stroke_width=3).move_to(head_center + np.array([0, -0.22, 0]))),
            Write(dong_4),
            Transform(tay_phai_hien_tai, tao_tay_chi(dong_4.get_left() + LEFT * 0.1)),
            run_time=0.6
        )
        self.play(nhom_khuon_mat.animate.shift(DOWN * 0.08), run_time=0.2)
        self.play(nhom_khuon_mat.animate.shift(UP * 0.08), run_time=0.2)

        # Cạnh huyền phát sáng xanh và đổi thành 5 cm
        nhan_c_5 = Text("c = 5 cm", font_size=21, color=C_GREEN, weight=BOLD).next_to(canh_huyen.get_center(), UP + RIGHT, buff=0.18)
        canh_huyen_sang = Line(b_pt, a_pt, color=C_GREEN, stroke_width=7)
        self.play(Transform(nhan_c, nhan_c_5), Create(canh_huyen_sang), Transform(tay_phai_hien_tai, tao_tay_chi(canh_huyen.get_center() + UP * 0.2)), run_time=0.8)
        self.play(FadeOut(canh_huyen_sang), run_time=0.5)
        self.wait(1.5)

        # Kết luận & Giơ ngón tay cái (Thumbs Up)
        doi_loi_giang("Chỉ cần biết 2 cạnh bất kỳ, em sẽ tính ngay được cạnh còn lại mà không cần đo!")
        tay_cai = Line(vai + np.array([-0.3, 0, 0]), vai + np.array([-0.3, 0.25, 0]), color=C_BLACK, stroke_width=4.5)
        nam_tay = Circle(radius=0.1, color=C_BLACK, fill_color=C_BLACK, fill_opacity=1).move_to(vai + np.array([-0.3, 0, 0]))
        ngon_cai = VGroup(Line(vai, vai + np.array([-0.3, 0, 0]), color=C_BLACK, stroke_width=3.5), tay_cai, nam_tay)

        self.play(Transform(canh_tay_trai, ngon_cai), Transform(tay_phai_hien_tai, tao_tay_chi(hop_ct.get_left())), run_time=0.8)
        self.wait(3)