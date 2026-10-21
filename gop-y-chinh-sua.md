# Góp ý & Câu hỏi cần làm rõ cho dự án video-factory

> Đây là danh sách nhận xét sau khi đọc toàn bộ project gồm:
> `ke-hoach.md`, `manim_coding_skill_mvp_plan.md`, `style.py`, `integral_tutorial.py`,
> `dp_tutorial.py`, `pyproject.toml` và thư mục `manim-coding-skill`.

---

## 1. Xung đột giữa hai bản kế hoạch

**Vấn đề:** Có hai tài liệu kế hoạch song song tồn tại — `ke-hoach.md` và `manim_coding_skill_mvp_plan.md` — nhưng chúng có phạm vi và cấu trúc thư mục khác nhau.

| Điểm so sánh | `ke-hoach.md` | `manim_coding_skill_mvp_plan.md` |
|---|---|---|
| Tên thư mục gốc | `project-prototype/` | `coding-video-factory/` |
| Đã tồn tại thực tế | ✅ Có (`project-prototype/`) | ❌ Không |
| Manim phiên bản ưu tiên | ManimGL 1.7.2 | Để ngỏ (A = ManimCE / B = ManimGL) |
| Giai đoạn AI | Giai đoạn 5 | Sau MVP |

**Câu hỏi:** Tài liệu nào là nguồn sự thật chính thức? Có nên gộp lại thành một file duy nhất không?

---

## 2. Phiên bản Manim chưa được chốt nhất quán

**Vấn đề:** Code thực tế trong `project-prototype/` dùng `from manimlib import *` (ManimGL), nhưng `manim_coding_skill_mvp_plan.md` lại minh họa bằng `from manim import *` (ManimCE) cho ví dụ Binary Search. Hai API này **không tương thích**.

- `integral_tutorial.py` → `from manimlib import *` (ManimGL) ✅
- `dp_tutorial.py` → `from manimlib import *` (ManimGL) ✅
- Ví dụ `scene.py` trong bản kế hoạch MVP → `from manim import *` (ManimCE) ❌ không nhất quán

**Câu hỏi:** Project đã chốt dùng ManimGL chưa? Nếu có, nên xóa hoặc đánh dấu rõ ràng đoạn ví dụ ManimCE trong `manim_coding_skill_mvp_plan.md` là "chỉ minh họa, không dùng thực tế".

---

## 3. File `dp_tutorial.py` bị hỏng — import sai

**Vấn đề:** `dp_tutorial.py` import từ `video_style` và dùng class `StyledScene`, nhưng file thực tế trong project là `style.py` với class `ChannelScene`. File này sẽ báo lỗi `ModuleNotFoundError` ngay khi chạy.

```python
# dp_tutorial.py — HIỆN TẠI (lỗi)
from video_style import STYLE, StyledScene

# style.py — THỰC TẾ
from style import STYLE, ChannelScene
```

Ngoài ra, `dp_tutorial.py` còn dùng `STYLE["transition_time"]`, `STYLE["pause_time"]`, `STYLE["write_time"]` — không tồn tại trong `style.py` hiện tại.

**Đề xuất:** Cập nhật `dp_tutorial.py` hoặc xóa nó nếu chỉ là file thử nghiệm cũ chưa dùng.

---

## 4. `pyproject.toml` thiếu dependencies

**Vấn đề:** `pyproject.toml` có `dependencies = []` rỗng, trong khi project đang dùng `manimgl` và `numpy`.

```toml
# Hiện tại
dependencies = []
```

Bất kỳ ai clone project sẽ không biết cần cài gì. `uv.lock` có thể đã chứa thông tin này nhưng `pyproject.toml` là file người đọc đầu tiên.

**Đề xuất:** Thêm ít nhất:
```toml
dependencies = [
    "manimgl>=1.7.2",
    "numpy",
]
```

---

## 5. Cấu trúc thư mục trong kế hoạch chưa khớp thực tế

**Vấn đề:** `ke-hoach.md` đề xuất cấu trúc có các thư mục `core/`, `components/`, `animations/`, `templates/`, `projects/`, `output/`, `tests/` — nhưng thực tế `project-prototype/` chỉ có:
- `style.py`, `integral_tutorial.py`, `dp_tutorial.py` (flat structure)
- Không có bất kỳ thư mục module nào từ kế hoạch

Điều này bình thường nếu dự án đang ở Giai đoạn 1, nhưng kế hoạch không ghi rõ trạng thái hiện tại là giai đoạn mấy.

**Đề xuất:** Thêm vào đầu `ke-hoach.md` dòng **"Trạng thái hiện tại: Giai đoạn 1 — đang hoàn thiện"** để dễ theo dõi tiến độ.

---

## 6. Tên project khác nhau giữa các tài liệu

- Thư mục thực tế: `video-factory/`
- Trong `manim_coding_skill_mvp_plan.md`: đề xuất tạo `coding-video-factory/`
- Trong `ke-hoach.md`: làm việc trong `project-prototype/`

**Câu hỏi:** `project-prototype/` là thư mục "thực hành thử", hay đây sẽ là thư mục gốc của sản phẩm thật? Nếu là thật thì nên đổi tên thành tên có ý nghĩa hơn (ví dụ `src/` hoặc `video_factory/`).

---

## 7. `manim-coding-skill` — vai trò chưa rõ trong project

**Vấn đề:** Thư mục `project-prototype/manim-coding-skill/` là một repo GitHub clone (`shihabshahrier/manim-coding-skill`) dùng ManimGL. Nhưng không rõ:
- Đây là dependency hay chỉ là tài liệu tham khảo?
- Project có đang dùng `SKILL.md` của nó như một skill cho AI agent không?
- `.gitignore` ở root có loại trừ thư mục này không?

**Câu hỏi:** Nên dùng repo này như một **git submodule** hay chỉ là tham khảo cục bộ? Nếu chỉ tham khảo, nên thêm vào `.gitignore` hoặc ít nhất có README giải thích.

---

## 8. File `trien-khai.md` rỗng

**Vấn đề:** File `trien-khai.md` hiện đang rỗng (0 bytes). Nếu đây là file ghi chép triển khai thực tế, cần bắt đầu điền nội dung.

**Đề xuất:** Ghi lại ít nhất:
- Ngày bắt đầu
- Môi trường đang dùng (Python version, ManimGL version)
- Lệnh render đã chạy được
- Kết quả render hiện tại

---

## 9. `style.py` — thiếu một số tiện ích thực dụng

**Nhận xét nhỏ (không quan trọng bằng các vấn đề trên):**

- `emphasize()` sau khi scale lên 1.08 thì scale xuống 1/1.08, nhưng không khôi phục màu về màu gốc — sau khi gọi hàm này, màu của object vẫn là `STYLE["highlight"]`.
- `glow()` tạo ra một `VGroup` mới tách khỏi mobject gốc — nếu người dùng thêm `glow()` vào scene mà quên rằng mobject gốc vẫn còn riêng biệt, có thể gây chồng nhau.
- Chưa có hàm utility để **xóa màn hình** (`clear_scene`) hay **chuyển cảnh** tiêu chuẩn — đây có vẻ là thứ cần thêm ở Giai đoạn 2 theo kế hoạch.

---

## 10. Chưa có file `.gitignore` nội dung

**Vấn đề:** File `.gitignore` ở root hiện rỗng (0 bytes). Cần có ít nhất:

```gitignore
project-prototype/.venv/
project-prototype/__pycache__/
project-prototype/latex_cache/
project-prototype/videos/
*.mp4
*.log
```

Nếu không, git sẽ track cả thư mục `.venv` và các file render nặng.

---

## 11. Câu hỏi về hướng phát triển AI (Giai đoạn 5)

Kế hoạch đề cập tích hợp AI nhưng chưa cụ thể:

- **Model nào** sẽ được dùng? Gemini API (đã nhắc trong `manim_coding_skill_mvp_plan.md`) hay local LLM?
- AI sẽ sinh ra **JSON script** (theo ke-hoach.md) hay **code ManimGL trực tiếp** (theo manim_coding_skill_mvp_plan.md Phần 10)?
- Có kế hoạch dùng `manim-coding-skill` như một **skill cho AI agent** (Antigravity/Cursor) để sinh code tự động không? Nếu có, cần cài đặt đúng theo hướng dẫn trong `GEMINI.md` của repo đó.

---

## Tóm tắt mức độ ưu tiên

| # | Vấn đề | Mức độ | Cần làm ngay? |
|---|---|---|---|
| 3 | `dp_tutorial.py` import sai — sẽ crash | 🔴 Cao | ✅ Có |
| 2 | Chưa chốt ManimGL vs ManimCE | 🔴 Cao | ✅ Có |
| 10 | `.gitignore` rỗng | 🔴 Cao | ✅ Có |
| 4 | `pyproject.toml` thiếu dependencies | 🟡 Trung bình | Nên làm |
| 1 | Hai bản kế hoạch xung đột | 🟡 Trung bình | Nên làm |
| 5 | Kế hoạch không ghi rõ giai đoạn hiện tại | 🟡 Trung bình | Nên làm |
| 8 | `trien-khai.md` rỗng | 🟡 Trung bình | Nên làm |
| 6 | Tên project/thư mục không nhất quán | 🟢 Thấp | Tùy bạn |
| 7 | Vai trò của `manim-coding-skill` chưa rõ | 🟢 Thấp | Tùy bạn |
| 9 | Một số quirk nhỏ trong `style.py` | 🟢 Thấp | Sau này |
| 11 | Hướng tích hợp AI chưa cụ thể | 🟢 Thấp | Giai đoạn 5 |
