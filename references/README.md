# Thư mục Tài liệu & Chỉ dẫn AI (`references/`)

Thư mục này chứa trọn bộ tri thức chuẩn hóa (**System Instructions**) để nạp vào **Gemini API** (hoặc AI Agent) khi tự động lập kịch bản, sinh mã nguồn hoạt ảnh ManimGL và tự sửa lỗi trên Windows:

1. **[`ai-animation-skill.md`](./ai-animation-skill.md)** — **Bộ Prompt điều phối chính (3 bước):**
   - Chia sẵn thành 3 khối rõ ràng: `[PROMPT 1: PLANNER]` (lập kịch bản), `[PROMPT 2: CODER]` (sinh code ManimGL hỗ trợ tiếng Việt, chống tràn khung hình) và `[PROMPT 3: FIXER]` (tự vá lỗi từ traceback). Đã loại bỏ hoàn toàn phần Bash script Linux không cần thiết.

2. **[`project-sdk.md`](./project-sdk.md)** — **Đặc tả SDK nội bộ của dự án:**
   - Liệt kê chính xác toàn bộ key của `STYLE`, các phương thức của `ChannelScene` trong [`style.py`](../style.py), cũng như cách dùng `StickmanTeacher` và `RightAngle` trong [`components/`](../components/__init__.py) để AI tái sử dụng đúng chuẩn thương hiệu.

3. **[`manim-gl-api.md`](./manim-gl-api.md)** — **Bảng tra cứu API ManimGL 1.7+:**
   - Cú pháp chuẩn `from manimlib import *`, quy tắc dùng `Text(..., font="Segoe UI")` cho tiếng Việt tách biệt với `Tex(r"...")` cho công thức toán, và bảng **Error → Fix Table** phục vụ bước tự sửa lỗi.

4. **[`storytelling.md`](./storytelling.md)** — **Nguyên tắc sư phạm trực quan:**
   - Cấu trúc kể chuyện 3 hồi (*Hook ➔ Build ➔ Resolution*), nhịp độ trình chiếu, quy tắc màu ngữ nghĩa và các lỗi trình bày cần tránh.

5. **[`math-visual-recipes.md`](./math-visual-recipes.md)** — **Mẫu trực quan hóa Toán học:**
   - Các mẫu code ManimGL thông dụng cho Giải tích & Hình học 3D (tiếp tuyến đạo hàm với `ValueTracker`, hội tụ tổng Riemann, mặt tròn xoay 3D).

---

### Sơ đồ ghép file vào `system_instruction` khi gọi Gemini API

- **Lượt 1 (Planner — Lập kịch bản):** `ai-animation-skill.md` *(Phần 1)* + `storytelling.md` + `project-sdk.md`
- **Lượt 2 (Coder — Viết code `.py`):** `ai-animation-skill.md` *(Phần 2)* + `project-sdk.md` + `manim-gl-api.md` *(+ `math-visual-recipes.md` nếu là chủ đề Toán)*
- **Lượt 3 (Fixer — Khi render báo lỗi):** `ai-animation-skill.md` *(Phần 3)* + `manim-gl-api.md` *(Error → Fix Table)* + `project-sdk.md`
