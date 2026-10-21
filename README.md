# 🎬 Video Factory

Hệ thống sản xuất video hoạt ảnh giáo dục tự động (Toán học, Thuật toán, Khoa học máy tính) chất lượng cao sử dụng **ManimGL 1.7+**.

---

## 🌟 Điểm nổi bật của dự án

1. **Giao diện Studio trực quan (`gui.py` / `run_gui.bat`)**:
   - Tự động nhận diện các Scene trong mã nguồn Python.
   - Hỗ trợ xem trước nhanh (Preview) hoặc render xuất file video chất lượng cao (480p, 720p, 1080p, 4K, GIF).
   - Theo dõi tiến trình render và log lỗi theo thời gian thực ngay trên giao diện.

2. **Thư viện thành phần hoạt họa (`components/`)**:
   - `StickmanTeacher`: Nhân vật giáo viên hoạt hình đầy đủ biểu cảm, kính mắt, que chỉ bảng tương tác và cử chỉ vẫy tay chào người xem.
   - `RightAngle`: Ký hiệu góc vuông chuẩn xác cho các bài giảng hình học.

3. **Hệ thống phong cách thương hiệu (`style.py`)**:
   - Bảng màu hiện đại (Modern Navy, Cyan, Purple, Accent Pink) có ngữ nghĩa rõ ràng.
   - Chuẩn hóa typography font `Segoe UI` chống lỗi hiển thị dấu tiếng Việt trên Windows.
   - Các hiệu ứng dùng chung: thẻ bài giảng (`make_card`), phát sáng neon (`glow`), lưới tọa độ mờ (`background_grid`), hiệu ứng nhấn mạnh (`emphasize`).

4. **Cẩm nang tra cứu & Kỹ năng AI (`references/`)**:
   - [`manim-gl-api.md`](./references/manim-gl-api.md): Bảng tra cứu cú pháp chuẩn ManimGL (giúp AI và lập trình viên không bao giờ bị nhầm sang ManimCE).
   - [`storytelling.md`](./references/storytelling.md): Nguyên tắc sư phạm trực quan, cấu trúc 3 hồi (Hook ➔ Build ➔ Resolution), chia phân cảnh 15 giây.
   - [`ai-animation-skill.md`](./references/ai-animation-skill.md): Chỉ dẫn hệ thống (System Prompt) chuẩn để giao cho AI (Claude, Gemini, ChatGPT) viết kịch bản và mã nguồn video.
   - [`math-visual-recipes.md`](./references/math-visual-recipes.md): Các công thức toán trực quan (Tiếp tuyến đạo hàm, tổng Riemann, mặt tròn xoay 3D).

---

## 📂 Cấu trúc thư mục

```text
video-factory/
├── components/                 # Các khối linh kiện tái sử dụng
│   ├── characters.py           # Nhân vật giáo viên StickmanTeacher
│   └── geometry.py             # Ký hiệu hình học, góc vuông RightAngle
├── scenes/                     # Thư viện các bài giảng video mẫu
│   ├── integral_tutorial.py    # Bài giảng Tích phân & Tổng Riemann
│   ├── dp_tutorial.py          # Bài giảng Quy hoạch động
│   ├── pythagoras_tutorial.py  # Bài giảng Định lý Pythagoras (Thầy giáo Stickman)
│   └── pythagoras_simple.py    # Bài giảng Pythagoras đồ thị phẳng
├── references/                 # Cẩm nang API & tài liệu huấn luyện AI
│   ├── ai-animation-skill.md
│   ├── manim-gl-api.md
│   ├── math-visual-recipes.md
│   ├── storytelling.md
│   └── README.md
├── gui.py                      # Studio giao diện đồ họa render video
├── run_gui.bat                 # Phím tắt mở Studio một chạm trên Windows
├── style.py                    # Hệ thống màu sắc & typography
├── pyproject.toml              # Cấu hình dự án & dependencies (uv)
├── ke-hoach.md                 # Bản kế hoạch phát triển 6 giai đoạn
└── .gitignore                  # Cấu hình loại trừ Git
```

---

## 🚀 Cài đặt & Bắt đầu nhanh

### 1. Yêu cầu hệ thống
- **Hệ điều hành**: Windows 10/11, macOS hoặc Linux
- **Python**: `>= 3.12`
- **Công cụ quản lý gói**: [`uv`](https://github.com/astral-sh/uv) (khuyên dùng)
- **Hỗ trợ thêm**: [FFmpeg](https://ffmpeg.org/) (xử lý video) và [MiKTeX/TeX Live](https://miktex.org/) (nếu render công thức toán LaTeX phức tạp)

### 2. Cài đặt môi trường
Mở terminal tại thư mục dự án và chạy:

```bash
uv sync
```

Lệnh trên sẽ tự động thiết lập môi trường ảo và cài đặt đầy đủ các thư viện cần thiết (`manimgl`, `numpy`, `av`, v.v.).

---

## 🎬 Cách sử dụng

### Cách 1: Sử dụng Studio giao diện đồ họa (Khuyên dùng)
- Trên Windows: Click đúp vào file **`run_gui.bat`**.
- Hoặc chạy qua dòng lệnh:
  ```bash
  uv run python gui.py
  ```
Giao diện sẽ mở ra, bạn chỉ cần chọn file kịch bản trong thư mục `scenes/`, chọn Scene muốn render và bấm **Render Video**.

### Cách 2: Render trực tiếp bằng dòng lệnh (CLI)
Xem trước nhanh một Scene (mở cửa sổ tương tác):
```bash
uv run manimgl scenes/pythagoras_tutorial.py PythagorasTeacherScene
```

Render xuất file video MP4 chất lượng cao (1080p, 60fps) và tự động mở sau khi render:
```bash
uv run manimgl scenes/integral_tutorial.py IntegralTutorial -w -o
```

---

## 🗺️ Lộ trình phát triển (Roadmap)
Xem chi tiết tại tài liệu [`ke-hoach.md`](./ke-hoach.md).
- [x] **Giai đoạn 1**: Nền tảng render ManimGL, hệ thống Style và các Scene mẫu.
- [x] **Giai đoạn 2**: Xây dựng thư viện component (`StickmanTeacher`, `RightAngle`).
- [ ] **Giai đoạn 3**: Chuẩn hóa cấu trúc kịch bản JSON (`script.json`).
- [ ] **Giai đoạn 4**: Tự động hóa Pipeline sinh code và render hàng loạt.
- [ ] **Giai đoạn 5**: Tích hợp AI Agent (Gemini API) tự động hóa từ chủ đề đến video.
- [ ] **Giai đoạn 6**: Đồng bộ giọng đọc lồng tiếng (TTS), phụ đề và xuất bản YouTube.

---

## 🙏 Ghi nhận & Bản quyền (Credits)
Dự án được xây dựng dựa trên sự kế thừa và cải tiến từ:
- **[ManimGL](https://github.com/3b1b/manim)** của Grant Sanderson (3Blue1Brown).
- Bộ kỹ năng sư phạm trực quan từ **[manim-coding-skill](https://github.com/shihabshahrier/manim-coding-skill)**.
