# 🎬 Video Factory Studio — AI (Gemini), VieNeu-TTS & ManimGL

Hệ thống sản xuất video hoạt ảnh giáo dục tự động (Toán học, Thuật toán, Khoa học máy tính) chất lượng cao kết hợp **Google Gemini API**, **VieNeu-TTS 48kHz (100% Offline)** và **ManimGL 1.7+**.

---

## 🌟 Điểm nổi bật của dự án

1. **Quy trình AI 3 bước thông minh (`core/` & `gui.py`)**:
   - **Bước 1 — Lập & Duyệt Kịch Bản**: Nhập chủ đề bài giảng ➔ Gemini thiết kế kịch bản phân cảnh 3 hồi (*Hook ➔ Build ➔ Resolution*) hiển thị trực tiếp lên Studio để bạn xem/chỉnh sửa ý trước khi tốn token viết code.
   - **Bước 2 — Sinh Code & Kiểm định Bố cục Tự động (`layout_auditor.py`)**: Tự động chạy thử headless kiểm tra 7 lỗi thị giác (tràn lề màn hình, đè chữ, mũi tên cắt chữ/xuyên bảng, chữ tràn ô...) và tự căn chỉnh bố cục.
   - **Bước 3 — Render MP4 & Tự vá lỗi (Self-Healing)**: Kết xuất video 480p / 720p / 1080p / 4K kèm cơ chế tự sửa lỗi Traceback.

2. **Thuyết minh Giọng đọc AI Tiếng Việt Offline (`core/tts_service.py`)**:
   - Tích hợp **VieNeu-TTS 48kHz** chạy hoàn toàn offline với **25 giọng đọc Bắc – Trung – Nam** tự nhiên.
   - **Đồng bộ Âm thanh – Hình ảnh theo từng phân cảnh (Zero-Drift Per-Scene Sync)**: Tự động đo thời lượng lời giảng từng cảnh trước khi sinh code và ghép AAC 48kHz khớp chính xác từng cảnh (không bao giờ đứt câu hay trôi lệch).
   - Hỗ trợ **🔊 Nghe thử lời dẫn** ngay trên giao diện và **🔄 Lồng tiếng lại MP4** khi đổi giọng đọc mà không cần render lại hình.

3. **Motion Design System v2 & Linh kiện Hoạt họa (`style.py`, `components/`)**:
   - `ChannelScene`: Phông nền Studio hiện đại, tiêu đề chuyển sắc gradient, thẻ hộp `make_box`, nhãn pill `make_badge`, tự động cân đối khung hình 16:9 (`fit_in_center_zone`, `fit_in_left_zone`, `fit_in_right_zone`) và hiệu ứng chuyển động mượt (`pop_in`, `stagger_in`, `flow_to`, `pulse_focus`).
   - `StickmanTeacher` & `RightAngle`: Nhân vật giáo viên cầm que chỉ bảng và ký hiệu hình học trực quan.

4. **Bộ Cẩm nang Huấn luyện AI (`references/`)**:
   - [`project-sdk.md`](./references/project-sdk.md), [`manim-gl-api.md`](./references/manim-gl-api.md), [`ai-animation-skill.md`](./references/ai-animation-skill.md), [`storytelling.md`](./references/storytelling.md), [`math-visual-recipes.md`](./references/math-visual-recipes.md).

---

## 📂 Cấu trúc thư mục

```text
video-factory/
├── core/                       # Điều phối AI Pipeline, Gemini API, Layout Auditor & VieNeu-TTS
├── manimlib/                   # ⚡ Lõi engine đồ họa ManimGL 1.7.2 tích hợp trực tiếp
├── components/                 # Linh kiện hoạt họa tái sử dụng (StickmanTeacher, RightAngle)
├── scenes/                     # Thư viện các bài giảng mẫu (Integral, DP, Pythagoras...)
├── references/                 # Cẩm nang API ManimGL & System Prompt cho AI
├── projects/                   # Thư mục lưu kịch bản/code AI sinh ra trên máy (Git ignored)
├── videos/                     # Thư mục chứa video MP4 xuất ra (Git ignored)
├── gui.py                      # Giao diện đồ họa Video Factory Studio
├── run_gui.bat                 # Phím tắt mở Studio một chạm trên Windows
├── style.py                    # Hệ thống màu sắc, bố cục 16:9 & Motion Design v2
├── .env.example                # Mẫu cấu hình khóa API an toàn
└── pyproject.toml              # Cấu hình dự án & dependencies (uv)
```

---

## 🚀 Cài đặt & Cấu hình Bảo mật

### 1. Yêu cầu hệ thống
- **Hệ điều hành**: Windows 10/11, macOS hoặc Linux
- **Python**: `>= 3.12` (khuyên dùng công cụ quản lý gói [`uv`](https://github.com/astral-sh/uv))
- **Công cụ phụ trợ**: [FFmpeg](https://ffmpeg.org/) trong `PATH` (bắt buộc để xuất/ghép âm thanh MP4) và [MiKTeX/TeX Live](https://miktex.org/) (để biên dịch công thức Toán LaTeX)

### 2. Cài đặt môi trường
```bash
uv sync
```

### 3. Cấu hình Gemini API Key (An toàn — Không lộ lên Git)
Bạn có thể chọn 1 trong 2 cách (cả `.env` và `.ai_config.json` đều đã được chặn trong `.gitignore`):
- **Cách 1 (Trực tiếp trên giao diện)**: Mở ứng dụng ➔ Nhập khóa vào ô **API Key** ➔ Bấm **💾 Lưu khóa** (lưu cục bộ vào `.ai_config.json`).
- **Cách 2 (Biến môi trường `.env`)**: Sao chép file `.env.example` thành `.env` và điền `GEMINI_API_KEY=...`.

---

## 🎬 Khởi chạy Studio

- **Trên Windows**: Click đúp vào **`run_gui.bat`** hoặc chạy:
  ```bash
  .venv\Scripts\python.exe gui.py
  ```
- **Render thủ công bằng CLI**:
  ```bash
  uv run manimgl scenes/integral_tutorial.py IntegralTutorial -w -m -o
  ```

---

## 🙏 Ghi nhận & Bản quyền (Credits)
- **[ManimGL](https://github.com/3b1b/manim)** của Grant Sanderson (3Blue1Brown).
- **[VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS)** cho bộ tổng hợp tiếng nói Tiếng Việt 48kHz Offline.
- Bộ kỹ năng sư phạm trực quan kế thừa và mở rộng từ **[manim-coding-skill](https://github.com/shihabshahrier/manim-coding-skill)**.
