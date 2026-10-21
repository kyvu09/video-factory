from manimlib import *
from style import STYLE, ChannelScene


class DynamicProgrammingTutorial(ChannelScene):
    def construct(self):
        title = self.make_title(
            "Quy hoach dong"
        )
        title.to_edge(UP)

        # Hien thi tieu de (dung show_title thay cho reveal khong ton tai)
        self.show_title(title)

        intro = self.make_body(
            "Hay bat dau tu mot bai toan don gian."
        )

        self.play(
            FadeIn(intro, shift=UP * 0.15),
            run_time=STYLE["normal"],
        )

        self.wait(STYLE["normal_pause"])

        formula = Tex(
            r"dp[n] = dp[n-1] + dp[n-2]"
        )
        formula.set_color(STYLE["highlight"])

        self.play(
            ReplacementTransform(intro, formula),
            run_time=STYLE["slow"],
        )

        self.wait(2)
