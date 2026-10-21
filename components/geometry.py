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
