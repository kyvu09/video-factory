
from manimlib import *


class FirstAnimation(Scene):
    def construct(self):
        title = TexText("Algorithm Visualization")
        title.scale(0.8)
        title.to_edge(UP)

        circle = Circle(radius=1.2, color=BLUE)
        square = Square(side_length=2, color=YELLOW)

        self.play(Write(title), run_time=1.5)
        self.play(ShowCreation(circle), run_time=1.5)
        self.wait(1)
        self.play(Transform(circle, square), run_time=2)
        self.wait(2)
