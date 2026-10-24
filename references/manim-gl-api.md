# ManimGL API Quick Reference

Always `from manimlib import *`. Never `from manim import *`.

---

## Core Objects

### Shapes
```python
Circle(radius=1, color=BLUE)
Square(side_length=2, color=WHITE)
Rectangle(width=4, height=2, color=GREEN)
RoundedRectangle(width=4, height=1.5, corner_radius=0.25, color=BLUE)
Line(start=LEFT * 2, end=RIGHT * 2, color=WHITE)
Arrow(start=LEFT, end=RIGHT, buff=0.12).set_color(YELLOW)
Dot(point=ORIGIN, color=RED, radius=0.1)
Arc(radius=1, start_angle=0, angle=PI / 2)
Polygon(np.array([-2, -1, 0]), np.array([2, -1, 0]), np.array([0, 2, 0]))
```

### Text & Code (Chuẩn hỗ trợ Tiếng Việt)
```python
# 1. Chữ thông thường & Tiếng Việt có dấu -> BẮT BUỘC dùng Text (render qua Pango)
Text("Định lý Pytago", font="Segoe UI", font_size=42, color=WHITE, weight=BOLD)
Text("Giải thích trực quan\ncăn giữa nhiều dòng", font="Segoe UI", font_size=28, alignment="CENTER")

# 2. Công thức Toán học (LaTeX) -> Dùng Tex với raw string r"..."
# LƯU Ý: TUYỆT ĐỐI KHÔNG đặt chữ tiếng Việt có dấu vào trong Tex() hoặc TexText()
Tex(r"\frac{d}{dx} x^2 = 2x", font_size=48, color=YELLOW)
Tex(r"\int_0^2 x\,dx = 2", color=YELLOW)

# 3. Hiển thị mã nguồn lập trình -> Dùng Code (truy cập từng dòng qua code_mob.lines[i] hoặc code_mob.code[i])
code_mob = Code("def binary_search(arr, x):\n    return -1", language="python", font="Consolas", font_size=24)
```

### Math objects
```python
NumberLine(x_range=[-3, 3, 1], include_numbers=True)
NumberPlane()  # full grid
Axes(
    x_range=[-3, 3, 1],
    y_range=[-2, 2, 1],
    width=8,
    height=5,
    axis_config={"include_tip": True},
    x_axis_config={"include_numbers": True},
    y_axis_config={"include_numbers": True},
)
FunctionGraph(lambda x: x**2, x_range=[-2, 2], color=BLUE)
Vector([2, 1, 0], color=YELLOW)  # [x, y, z]
```

### Grouping & Grid Layout
```python
group = VGroup(obj1, obj2, obj3)
group.arrange(DOWN, aligned_edge=LEFT, buff=0.3)          # stack vertically
group.arrange(RIGHT, buff=0.5)                            # stack horizontally

# Xếp dạng lưới trong ManimGL 1.7+: BẮT BUỘC dùng n_rows / n_cols (KHÔNG có rows, cols, grid_dims!)
grid = VGroup(*items)
grid.arrange_in_grid(n_rows=2, n_cols=3, buff=0.6)        # hoặc h_buff=0.8, v_buff=0.5
group.move_to(ORIGIN)
```

---

## Positioning & Arrow Routing

```python
obj.to_edge(UP, buff=0.35)          # snap to top edge
obj.to_edge(DOWN, buff=0.35)        # snap to bottom
obj.to_edge(LEFT)
obj.to_edge(RIGHT)
obj.to_corner(UP + LEFT, buff=0.4)  # snap to corner
obj.move_to(ORIGIN)                 # center
obj.move_to(UP * 2)
obj.next_to(other, DOWN, buff=0.3)  # below other with gap
obj.align_to(other, LEFT)           # align left edges
obj.shift(RIGHT * 2)                # move relative to current pos
obj.scale(0.8)
obj.set_color(RED)

# Nối mũi tên ĐÚNG HƯỚNG vị trí tương đối (tránh cắt chéo qua chữ/khung):
Arrow(top_box.get_bottom(), bottom_box.get_top(), buff=0.12)     # Khi top_box nằm TRÊN bottom_box
Arrow(left_box.get_right(), right_box.get_left(), buff=0.12)     # Khi left_box nằm TRÁI right_box
Arrow(slot.get_left() + LEFT * 0.9, slot.get_left(), buff=0.08)  # Khi chỉ ngang vào 1 ô bảng dọc
```

**Direction constants**: `UP DOWN LEFT RIGHT UL UR DL DR ORIGIN`  
**Scalar multiply**: `UP * 2`, `RIGHT * 3.5`

---

## Animations (Ưu tiên chuyển động mượt & sống động)

### Appear & Spring Pop
```python
self.play(ShowCreation(shape_or_curve), run_time=1.2)        # Vẽ nét cho Line, Polygon, Circle, FunctionGraph
self.play(GrowArrow(arrow), run_time=0.65)                   # BẮT BUỘC dùng GrowArrow cho Arrow (KHÔNG dùng ShowCreation trên Arrow!)
self.play(Write(tex_obj), run_time=1.1)                      # Viết công thức Toán
self.play(FadeIn(obj, shift=UP * 0.2, scale=0.95), run_time=0.75)
self.pop_in(card, run_time=0.6)                              # Gọi trực tiếp method nảy đàn hồi (KHÔNG bọc trong self.play!)
self.play(DrawBorderThenFill(shape), run_time=1.2)
self.add(obj)                                                # Thêm tức thì không qua animation
```

### Data Flow, Path Motion & Smooth Text Morph
```python
# 1. Luồng dữ liệu bay từ nguồn tới đích (giữ nguyên nguồn, tạo đích tại chỗ):
self.flow_to(src_mob, dst_mob, path_arc=-0.45)              # Bắn hạt sáng sang ô mới (gọi trực tiếp, KHÔNG bọc trong self.play!)

# 2. Đổi chữ / cập nhật giá trị trong ô MƯỢT MÀ (TUYỆT ĐỐI KHÔNG dùng Transform trên Text vì gây rách nét chữ!):
new_val.move_to(old_val)  # hoặc self.fit_text_in(new_val, slot_box)
self.play(FadeTransform(old_val, new_val, stretch=False), run_time=0.6)
# Hoặc dùng self.morph_text_anim(old_val, new_val) của ChannelScene! (Lưu ý: sau lệnh này new_val thay thế old_val trên Scene)

# 3. Cho hạt điểm / con trỏ chạy dọc theo đường cong / bậc thang:
arc_path = ArcBetweenPoints(p_start, p_end, angle=-PI / 2)
self.play(MoveAlongPath(glowing_dot, arc_path, rate_func=smooth), run_time=0.65)

# 4. Biến đổi hình học & Công thức LaTeX:
self.play(ReplacementTransform(shape1, shape2), run_time=1.1)
self.play(TransformMatchingTex(eq1, eq2), run_time=1.3)
self.play(obj.animate.shift(RIGHT * 2), run_time=0.9)
self.play(obj.animate.set_stroke(YELLOW, width=3.5), run_time=0.5)
```

### Disappear
```python
self.play(FadeOut(obj, shift=DOWN * 0.12), run_time=0.6)
```

### Neon Focus / Indicate / Highlight
```python
# Tia neon chạy viền cực đẹp (hoặc gọi gọn self.pulse_focus(obj, color=YELLOW)):
self.play(
    FlashAround(obj, color=YELLOW, stroke_width=3.8, time_width=1.2, buff=0.08),
    Indicate(obj, color=YELLOW, scale_factor=1.06),
    run_time=0.9,
)
self.play(Flash(point_or_mob, color=YELLOW, flash_radius=0.35), run_time=0.6)
rect = SurroundingRectangle(obj, color=YELLOW, buff=0.15)
self.play(ShowCreation(rect), run_time=0.6)
```

### Multiple simultaneous & Staggered
```python
self.play(
    FadeIn(obj1),
    FadeIn(obj2),
    run_time=1.0,
)
self.play(
    LaggedStart(*[FadeIn(m, shift=UP * 0.15) for m in group], lag_ratio=0.12),
    run_time=1.2,
)
```

### Wait
```python
self.wait(0.5)   # short pause
self.wait(1.5)   # normal pause after major step
self.wait(2.5)   # hold for key insight / conclusion
```

---

## Camera

```python
# Zoom in
self.play(self.camera.frame.animate.scale(0.7), run_time=1.5)
# Zoom out
self.play(self.camera.frame.animate.scale(1.5), run_time=1.5)
# Pan to object
self.play(self.camera.frame.animate.move_to(obj), run_time=1.5)
# Reset to default frame
self.play(self.camera.frame.animate.move_to(ORIGIN).set_height(8), run_time=1.0)
```

---

## Colors

```python
# Built-in ManimGL constants
BLUE YELLOW GREEN RED TEAL PURPLE ORANGE GOLD WHITE GREY BLACK
BLUE_A BLUE_B BLUE_C BLUE_D BLUE_E  # A=lightest, E=darkest (same for RED, GREEN, YELLOW, GREY)

# Hex strings are also directly supported (recommended via STYLE dict in style.py)
obj.set_color("#38BDF8")
```

---

## ValueTracker & Updaters (for dynamic values)

```python
t = ValueTracker(0)

dot = Dot(color=BLUE)
dot.add_updater(lambda d: d.move_to(
    axes.c2p(t.get_value(), np.sin(t.get_value()))
))
self.add(dot)
self.play(t.animate.set_value(2 * PI), run_time=4)
dot.clear_updaters()
```

---

## Axes + Graphs

```python
axes = Axes(
    x_range=[0, 3, 1],
    y_range=[0, 3, 1],
    width=8,
    height=5,
    axis_config={"include_tip": True},
    x_axis_config={"include_numbers": True},
    y_axis_config={"include_numbers": True},
)
axis_labels = axes.get_axis_labels(x_label_tex="x", y_label_tex="y")
graph = axes.get_graph(lambda x: x**2 / 3, x_range=[0, 2.8], color=BLUE)
area = axes.get_riemann_rectangles(graph, x_range=[0, 2], dx=0.2, fill_opacity=0.65)
self.play(ShowCreation(axes), FadeIn(axis_labels), run_time=1.2)
self.play(ShowCreation(graph), run_time=1.2)
```

---

## Error → Fix Table

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'manim'` | Used ManimCE import `from manim import *` | Replace with `from manimlib import *` |
| `TypeError: Mobject.arrange_in_grid() got an unexpected keyword argument 'rows'` (or `'cols'`, `'grid_dims'`) | ManimCE / old ManimGL keyword | Use `group.arrange_in_grid(n_rows=2, n_cols=3, buff=0.6)` |
| `TypeError: ... got an unexpected keyword argument 'corner_radius'` on `SurroundingRectangle` | `SurroundingRectangle` inherits `Rectangle`, not `RoundedRectangle` | Remove `corner_radius=` or use `self.make_box(...)` / `RoundedRectangle` |
| `ImportError` / `NameError`: `'Create'` | ManimCE syntax | Use `ShowCreation(obj)` |
| `ImportError` / `NameError`: `'MathTex'` | ManimCE syntax | Use `Tex(r"...")` |
| `NameError: name 'always_redraw' is not defined` | ManimCE syntax | Use `mob.add_updater(lambda m: ...)` |
| `AttributeError: 'Axes' object has no attribute 'plot'` | ManimCE syntax | Use `axes.get_graph(lambda x: ...)` |
| `AttributeError: 'Axes' object has no attribute 'coords_to_point'` | ManimCE syntax | Use `axes.c2p(x, y)` |
| `LaTeX Error` / failed compilation on `Tex` or `TexText` | Vietnamese diacritics inside `Tex`/`TexText`, or unescaped `\` | Move Vietnamese text to `Text("...", font="Segoe UI")`; keep `Tex(r"...")` strictly for math using raw string `r"..."` |
| `TypeError` / `AttributeError` on `Text.set_default()` | ManimCE method not in ManimGL | Pass `font="Segoe UI"` directly or use `ChannelScene` helpers |
| `AttributeError: 'NoneType' object` | Invalid method chain or uninitialized mobject | Ensure object is created before `self.play()` and methods return `self` |
| Black frame in output | Empty `construct()` or no `self.play()` | Add at least one `self.play(...)` or `self.wait(...)` after `self.add(...)` |
