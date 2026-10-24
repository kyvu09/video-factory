# Video Factory SDK Reference (`style.py` & `components/`)

Tài liệu đặc tả hệ thống **Motion Design System** và các module dùng chung trong dự án **Video Factory**. Khi sinh code ManimGL, **luôn ưu tiên sử dụng** các lớp, hằng số, hàm bố cục lấp đầy không gian và hiệu ứng chuyển động mượt dưới đây.

---

## 1. Hệ thống Phong cách, Bố cục & Chuyển động (`style.py`)

```python
from manimlib import *
from style import STYLE, ChannelScene
```

### Bảng hằng số `STYLE` (chỉ sử dụng đúng các key dưới đây)

```python
# Nền & bề mặt có chiều sâu (ChannelScene tự động dựng lưới kiến trúc mờ + quầng sáng ambient + thanh ngăn Header)
STYLE["background"]     # "#070B16" - nền tối Midnight Slate sâu làm nổi bật ánh sáng neon
STYLE["surface"]        # "#131F38" - bề mặt thẻ/khung sáng rõ tách khỏi nền
STYLE["surface_alt"]    # "#1A2B4C" - bề mặt nhấn cho nhãn pill / badge
STYLE["border"]         # "#334B73" - viền khung trung tính sắc nét

# Bộ 3 màu thương hiệu
STYLE["primary"]        # "#38BDF8" (Sky Cyan)    - chủ đạo, luồng chính, khung chính
STYLE["secondary"]      # "#A78BFA" (Soft Violet) - khái niệm phụ, nhánh con, dữ liệu đầu vào
STYLE["accent"]         # "#F472B6" (Rose Pink)   - công thức chốt, cấu trúc bảng / mảng

# Màu ngữ nghĩa
STYLE["highlight"]      # "#FBBF24" (Amber Gold)  - trạng thái đang xét, con trỏ, điểm nhấn
STYLE["success"]        # "#34D399" (Emerald)     - kết quả tối ưu, hoàn thành, cache hit
STYLE["error"]          # "#FB7185" (Coral Red)   - chi phí cao, trùng lặp, cảnh báo

# Màu chữ
STYLE["text"]           # "#F8FAFC" - chữ nội dung chính
STYLE["muted"]          # "#94A3B8" - chỉ số phụ, trạng thái chờ

# Cỡ chữ chuẩn cân đối 16:9
STYLE["title_size"]     # 38
STYLE["subtitle_size"]  # 24
STYLE["body_size"]      # 26
STYLE["caption_size"]   # 21
STYLE["code_size"]      # 23

# Nhịp điệu animation (run_time) & nghỉ (self.wait)
STYLE["fast"]           # 0.4
STYLE["normal"]         # 0.75
STYLE["slow"]           # 1.25
STYLE["stagger"]        # 0.12 (dùng cho lag_ratio trong LaggedStart)
STYLE["short_pause"]    # 0.45
STYLE["normal_pause"]   # 1.3
STYLE["long_pause"]     # 2.2
```

### Lớp cơ sở `ChannelScene(Scene)` — Bố cục Đầy Đặn & Motion Graphics Sống Động

Khung hình 16:9 chuẩn của ManimGL rộng `14.22` (`x ∈ [-7.11, 7.11]`), cao `8.0` (`y ∈ [-4.0, 4.0]`). `ChannelScene` tự động trang bị phông nền Studio có chiều sâu (`z_index <= -8`) và chia màn hình thành **3 dải tối ưu diện tích**:
- **Dải Header (`y ∈ [2.62, 3.76]`):** Tiêu đề phối màu gradient + phụ đề thanh thoát (`self.place_header(...)`).
- **Dải Stage (`y ∈ [-2.65, 2.32]`):** Vùng diễn hoạt rộng rãi (`12.2 × 4.75`), tự động **thu nhỏ nếu quá khổ VÀ phóng lớn vừa vặn (`auto_upscale=True`, lấp ~84% khung)** để hình vẽ luôn đầy đặn, cân đối, không bị lọt thỏm giữa khoảng đen! Khi dùng 2 cột (`x = -3.35` và `x = +3.35`), hệ thống tự động kẻ đường phân cách dọc nét đứt tinh tế ở giữa màn hình.
- **Dải Footer (`y ∈ [-3.78, -2.95]`):** Thanh chú thích dạng pill hiện đại ở đáy (`self.place_footer(...)`).

#### A. Nhóm hàm Tạo Chữ, Khối Thẻ, Nhãn Pill & Mũi Tên
| Phương thức trên `self` | Công dụng |
|---|---|
| `self.make_title(text, color=None)` | Tạo `Text` font `Segoe UI`, `BOLD`, mặc định phủ gradient `primary -> secondary`. |
| `self.make_subtitle(text, color=None)` | Tạo phụ đề sắc nét font `Segoe UI`. |
| `self.make_body(text, color=None)` | Tạo chữ nội dung chính font `Segoe UI`, cỡ `body_size`. |
| `self.make_caption(text, color=None)` | Tạo chữ chú thích/nhãn phụ font `Segoe UI`, cỡ `caption_size`. |
| `self.make_box(content, width=None, height=None, color=None)` | **BẮT BUỘC DÙNG CHO HỘP/THẺ:** Tạo trọn gói `VGroup(card, content_mob)` (nhận `str` hoặc `Tex`/`Text`/`Code`/`VGroup`). Khung và nội dung luôn đi liền nhau! |
| `self.make_badge(text, color=None, font_size=20)` | **RẤT ĐẸP:** Tạo nhãn pill nhỏ gọn có viền sáng (dùng gắn nhãn độ phức tạp `O(1)`, `O(N)`, `+1 bậc`, `Cache Hit!`, bước 1, 2...). |
| `self.make_arrow(start, end, color=None, buff=0.10, path_arc=0.0)` | Tạo mũi tên thanh thoát, tỷ lệ đầu nhọn cân đối, nổi bật trên nền tối (luôn diễn hoạt bằng `GrowArrow(arr)`!). |
| `self.fit_text_in(text_mob, container_mob)` | **BẮT BUỘC DÙNG CHO Ô BẢNG:** Tự co chữ/số vừa khít và căn chính giữa lòng ô `container_mob`. |

#### B. Nhóm hàm Quy Hoạch Bố Cục Lấp Đầy Khung Hình
| Phương thức trên `self` | Công dụng |
|---|---|
| `self.place_header(title, subtitle=None)` | Đặt tiêu đề & phụ đề vào dải Header, tự động thay thế tiêu đề cảnh trước. |
| `self.place_footer(caption, color=None)` | Đặt thanh chú thích dạng pill vào dải Footer dưới đáy. |
| `self.fit_in_center_zone(mob, auto_upscale=True)` | Căn chỉnh `mob` lấp đầy cân đối vùng trung tâm (`12.2 × 4.75` tại `(0, -0.18)`). |
| `self.fit_in_left_zone(mob, auto_upscale=True)` | Căn chỉnh `mob` lấp đầy cân đối **Cột Trái** (`5.95 × 4.75` tại `(-3.35, -0.18)`) + bật vạch chia cột. |
| `self.fit_in_right_zone(mob, auto_upscale=True)` | Căn chỉnh `mob` lấp đầy cân đối **Cột Phải** (`5.95 × 4.75` tại `(+3.35, -0.18)`) + bật vạch chia cột. |
| `self.clear_stage(*keep, run_time=0.5)` | Chuyển cảnh mượt (`FadeOut(..., shift=DOWN*0.12)`), dọn sạch vật thể cũ nhưng giữ nguyên phông nền Studio. |

#### C. Nhóm hàm Hiệu Ứng Chuyển Động Cao Cấp (3Blue1Brown Choreography)
| Phương thức trên `self` | Công dụng |
|---|---|
| `self.pop_in(mob, run_time=0.6)` | Xuất hiện nảy đàn hồi (`GrowFromCenter` + `rate_func=overshoot`) cực kỳ bắt mắt cho thẻ công thức / nút chính / badge. |
| `self.stagger_in(group, shift=UP*0.22, lag_ratio=0.12)` | Xuất hiện đuổi nhau theo làn sóng mượt mà cho bậc thang, mảng, lưới ô, danh sách. |
| `self.flow_to(source_mob, target_mob, path_arc=-0.45)` | Cho bản sao bay theo đường cong mượt từ `source_mob` sang `target_mob` (`TransformFromCopy`) — tuyệt vời để diễn tả dữ liệu / giá trị truyền vào bảng nhớ! |
| `self.morph_text_anim(old_mob, new_mob)` / `self.morph_text(old_mob, new_mob)` | Chuyển đổi chữ/số mượt kiểu cuộn số (`FadeOut` + `FadeIn` trượt nhẹ), **không bao giờ bị rách/méo ký tự** như `Transform`! (Lưu ý sau khi gọi, `new_mob` là đối tượng hiển thị trên màn hình). |
| `self.pulse_focus(mob, color=None, run_time=0.9)` | Tia sáng neon chạy viền `FlashAround` kết hợp nhịp nhấn `Indicate` thu hút ánh mắt khán giả. |
| `self.glow(mobject, color=None)` | Tạo quầng hào quang phát sáng neon xung quanh hạt điểm (`Dot`), đường đi hoặc ký hiệu quan trọng. |

---

## 2. Thư viện Linh kiện Hoạt họa (`components/`)

```python
from components import StickmanTeacher, RightAngle
```

### `StickmanTeacher(VGroup)` — Nhân vật thầy giáo chỉ bảng
- Nét vẽ màu `BLACK`, vị trí mặc định bên trái (`x ≈ -4.8`). Khi dùng cần đặt nền sáng (`default_camera_config = {"background_color": "#F8FAFC"}`).
- Phương thức:
  - `teacher.create_pointing_arm_to(target_pos)` (`Transform(teacher.right_arm_group, ...)`)
  - `teacher.create_wave_left_arm(phase=0)` / `teacher.create_rest_left_arm()` / `teacher.create_thumbs_up_left_arm()` (`Transform(teacher.left_arm_group, ...)`)
  - `teacher.create_surprised_head()` / `teacher.create_smiling_head()` (`Transform(teacher.head_group, ...)`)
  - `teacher.get_pointer_tip_pos()`

### `RightAngle(line1, line2, length=0.35, color=YELLOW, **kwargs)`
- Vẽ ký hiệu góc vuông tại `line1.get_start()` (theo hướng `+UP` và `+RIGHT`).
