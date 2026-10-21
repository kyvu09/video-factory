# Math Visual Recipes (Các mẫu trực quan hóa toán học)

> Tài liệu này đúc kết các ý tưởng hoạt ảnh toán học hay nhất từ bộ tutorial (Calculus, Updaters, 3D),
> đã được chuẩn hóa để tham khảo cho **ManimGL**.

---

## 1. Tiếp tuyến & Đạo hàm (Secant Slope to Tangent)

**Ý tưởng sư phạm:**
- Cho một đường cong $f(x)$.
- Đặt 2 điểm trên đồ thị cách nhau khoảng cách $\Delta x$.
- Vẽ đường cát tuyến (secant line) nối 2 điểm đó.
- Cho $\Delta x \to 0$, cát tuyến dần chuyển thành tiếp tuyến tại điểm $x_0$.

**Cơ chế trong ManimGL:**
```python
from manimlib import *

# Dùng ValueTracker để điều khiển vị trí hoặc khoảng cách dx
x_tracker = ValueTracker(1.0)
dx_tracker = ValueTracker(1.0)

# Cập nhật đường cát tuyến / tiếp tuyến qua updater
# Trong ManimGL, dùng add_updater thay vì always_redraw của ManimCE
dot = Dot(color=YELLOW)
dot.add_updater(lambda m: m.move_to(axes.c2p(x_tracker.get_value(), f(x_tracker.get_value()))))
```

---

## 2. Tổng Riemann xấp xỉ diện tích (Riemann Sum Convergence)

**Ý tưởng sư phạm:**
- Chia diện tích dưới đường cong thành $n$ hình chữ nhật với độ rộng $dx$.
- Cho $dx$ nhỏ dần: $0.5 \to 0.2 \to 0.05 \to 0.01$.
- Các hình chữ nhật phủ khít dần vùng diện tích thật.

**Cơ chế trong ManimGL:**
- Sử dụng trực tiếp `axes.get_riemann_rectangles(graph, x_range=[a, b], dx=...)`.
- Chuyển tiếp mượt giữa các mức độ thô/mịn bằng `ReplacementTransform`.
- Xem ví dụ hoàn chỉnh đã chạy được trong [`integral_tutorial.py`](../integral_tutorial.py).

---

## 3. Khối tròn xoay 3D (Surface of Revolution)

**Ý tưởng sư phạm:**
- Bắt đầu từ đồ thị 2D $y = f(x)$ trên mặt phẳng $XY$.
- Xoay đồ thị quanh trục hoành $X$ qua một góc $\theta$ từ $0 \to 2\pi$.
- Khối 3D hoặc mặt cong dần xuất hiện trong không gian 3 chiều.

**Cơ chế trong ManimGL:**
```python
from manimlib import *

class SurfaceOfRevolutionDemo(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES)
        
        # Dùng ParametricSurface để mô tả mặt tròn xoay:
        # x(u, v) = u
        # y(u, v) = f(u) * cos(v)
        # z(u, v) = f(u) * sin(v)
        surface = ParametricSurface(
            lambda u, v: np.array([
                u,
                np.sqrt(u) * np.cos(v),
                np.sqrt(u) * np.sin(v)
            ]),
            u_range=[0, 4],
            v_range=[0, TAU],
            color=BLUE,
            opacity=0.7
        )
        self.play(ShowCreation(surface), run_time=3)
        self.wait()
```

---

## 4. Các điểm lưu ý khi chuyển code ManimCE sang ManimGL

| Khái niệm | ManimCE (Tutorials cũ) | ManimGL (Chuẩn của dự án) |
|---|---|---|
| Import | `from manim import *` | `from manimlib import *` |
| Text công thức | `MathTex(r"...")` | `Tex(r"...")` |
| Text thường | `Text("...")` | `Text("...")` hoặc `TexText("...")` |
| Vẽ hình | `Create(obj)` | `ShowCreation(obj)` |
| Tự động cập nhật | `always_redraw(lambda: ...)` | `mob.add_updater(lambda m: ...)` |
| Tọa độ trục | `axes.coords_to_point(x, y)` | `axes.c2p(x, y)` |
| Điểm sang tọa độ | `axes.point_to_coords(p)` | `axes.p2c(p)` |
