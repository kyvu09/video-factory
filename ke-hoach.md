# Kế hoạch dự án: Video Factory

> **Nguồn sự thật chính thức** cho toàn bộ project.
> Tài liệu `manim_coding_skill_mvp_plan.md` là hướng dẫn triển khai MVP chi tiết bổ sung cho file này.
>
> **Cập nhật lần cuối:** 2026-10-21
> **Trạng thái hiện tại: 🟡 Giai đoạn 1 — Đang hoàn thiện nền tảng render**

---

## Mục tiêu

Bạn nhập chủ đề (tích phân, thuật toán sắp xếp, quy hoạch động...) → AI hỗ trợ viết kịch bản và code animation → hệ thống render video → kiểm tra lỗi và xuất video hoàn chỉnh để đăng YouTube.

Vì ưu tiên chạy miễn phí trên máy cá nhân, kế hoạch theo hướng **local-first**, chia module rõ ràng, làm được từng giai đoạn và chưa cần API AI ngay từ đầu.

---

## Quyết định kỹ thuật đã chốt

| Thành phần | Quyết định |
|---|---|
| Ngôn ngữ | Python 3.12 |
| **Animation engine** | **ManimGL 1.7.2** (dùng `from manimlib import *`) |
| Quản lý môi trường | `uv` |
| Cấu hình giao diện | `style.py` + class `ChannelScene` |
| Định dạng kịch bản | JSON có schema rõ ràng |
| Render | Chạy tiến trình ManimGL riêng, thu thập log |
| Video đầu ra | MP4 |
| Phụ đề | SRT |
| AI | Gemini API — chưa tích hợp trong MVP |
| Giao diện | CLI trước, GUI sau |
| Lưu dự án | File trên máy tính, không cần server |

> **Lưu ý quan trọng:** Project dùng **ManimGL** (`manimlib`), KHÔNG phải ManimCE (`manim`).
> Hai thư viện có API khác nhau và không tương thích. Không trộn lẫn import giữa hai bản.

---

## 1. Kiến trúc tổng thể

1. **Nhập chủ đề** — Ví dụ: *"Giải thích tích phân trong 3 phút"*
2. **Tạo kịch bản** — Nội dung, lời thuyết minh, các cảnh và mục tiêu hình ảnh
3. **Sinh code ManimGL** — Dùng `style.py`, `components.py` và `animations.py` dùng chung
4. **Render và kiểm tra** — Phát hiện lỗi, kiểm tra bố cục, xem video thử
5. **Xuất video** — MP4, phụ đề, lời đọc và metadata YouTube

**Nguyên tắc quan trọng:** AI tạo nội dung, còn hệ thống kiểm soát cấu trúc, phong cách, render và chất lượng đầu ra. Không để AI tự viết toàn bộ project từ đầu cho mỗi video.

---

## 2. Cấu trúc thư mục

Thư mục gốc của toàn bộ dự án là `video-factory/`.

```
video-factory/               ← thư mục gốc dự án
│
├── manimlib/                # ⚡ Lõi engine đồ họa ManimGL (đã tích hợp trực tiếp)
├── main.py                  # Điểm chạy chính của hệ thống
├── config.py                # Cấu hình chung
├── style.py                 # ✅ Phong cách video (đã có)
├── references/              # ✅ Tài liệu API & chỉ dẫn AI (đã có)
│
├── core/
│   ├── project_manager.py   # Quản lý từng video
│   ├── script_parser.py     # Đọc kịch bản
│   ├── code_generator.py    # Tạo code từ template
│   └── pipeline.py          # Điều phối các bước
│
├── components/
│   ├── text.py              # Tiêu đề, nội dung, công thức
│   ├── diagrams.py          # Đồ thị, hình học, sơ đồ
│   └── code_display.py      # Hiển thị code lập trình
│
├── animations/
│   ├── transitions.py       # Chuyển cảnh
│   ├── highlights.py        # Làm nổi bật nội dung
│   └── formulas.py          # Animation công thức
│
├── templates/
│   ├── math.py              # Template video Toán
│   ├── algorithms.py        # Template thuật toán
│   └── programming.py       # Template lập trình
│
├── projects/
│   └── integral/            # ✅ Ví dụ đã có (integral_tutorial.py)
│       ├── script.json
│       ├── scene.py
│       └── assets/
│
├── output/
│   └── integral/
│       ├── video.mp4
│       ├── subtitles.srt
│       └── metadata.json
│
├── tests/
│   ├── test_style.py
│   ├── test_parser.py
│   └── test_pipeline.py
│
├── pyproject.toml
└── README.md
```

> Đây là cấu trúc **mục tiêu**, không phải danh sách file cần tạo ngay.
> Bổ sung module khi có nhu cầu thực tế để tránh overengineering.

---

## 3. Lộ trình triển khai

### 🟡 Giai đoạn 1 — Hoàn thiện nền tảng render
**Ưu tiên cao nhất · Chưa cần AI**

- [x] Cài đặt ManimGL 1.7.2 và sửa lỗi LaTeX cơ bản.
- [x] Tạo `style.py` với class `ChannelScene` để dùng chung màu sắc, cỡ chữ và thời lượng.
- [x] Render thử video tích phân (`integral_tutorial.py`).
- [ ] Chuẩn hóa API tương thích ManimGL 1.7.2 (sửa `dp_tutorial.py` và các file cũ).
- [ ] Sửa lỗi chữ chồng nhau, nội dung tràn màn hình.
- [ ] Tạo một scene mẫu hoàn chỉnh với nhiều loại animation.

**Đầu ra:** một video mẫu render ổn định và một bộ style dùng chung.

---

### ⬜ Giai đoạn 2 — Xây thư viện thành phần
**Ưu tiên cao · Không cần API**

- Tạo component cho tiêu đề, văn bản, công thức, đồ thị, bảng và sơ đồ.
- Tạo các animation dùng lại như `show_title()`, `highlight()` và `transition()`.
- Chuẩn hóa cách định vị nội dung để giảm lỗi bố cục.
- Xây template riêng cho Toán học và thuật toán.

**Đầu ra:** tạo video mới bằng cách kết hợp component thay vì viết lại toàn bộ animation.

---

### ⬜ Giai đoạn 3 — Chuẩn hóa dữ liệu kịch bản
**Ưu tiên cao · Không cần API**

Xây dựng định dạng JSON mô tả từng cảnh:

```json
{
  "title": "Tich phan la gi?",
  "scenes": [
    {
      "type": "text",
      "content": "Ta can tinh dien tich duoi duong cong."
    },
    {
      "type": "formula",
      "content": "\\int_0^2 x\\,dx = 2"
    }
  ]
}
```

- Viết `script_parser.py` để đọc và validate dữ liệu.
- Kiểm tra trường bắt buộc, loại cảnh và tham số.
- Chuyển dữ liệu thành các component ManimGL tương ứng.

**Đầu ra:** sửa nội dung video chủ yếu bằng cách chỉnh JSON, không phải sửa code animation.

---

### ⬜ Giai đoạn 4 — Tự động hóa pipeline
**Không cần API**

- Tạo project video tự động.
- Sinh file scene từ template.
- Chạy lệnh render bằng `subprocess`.
- Thu thập log và lưu lỗi vào file.
- Quản lý trạng thái: `draft` → `rendering` → `failed` / `completed`.
- Xuất video vào đúng thư mục dự án.

**Đầu ra:** một lệnh chạy được quy trình từ kịch bản đến video MP4.

---

### ⬜ Giai đoạn 5 — Tích hợp AI (Gemini API)
**Cần Gemini API**

- AI chuyển chủ đề thành kịch bản.
- AI chia kịch bản thành các cảnh có cấu trúc (JSON).
- AI tạo code ManimGL theo quy tắc và danh sách component được hỗ trợ.
- Tự động kiểm tra code trước khi render.
- Nếu lỗi, gửi log trở lại để AI đề xuất bản sửa.

**Đầu ra:** nhập chủ đề và nhận được video nháp có thể kiểm tra.

> Giai đoạn này mới cần lựa chọn model/API; pipeline cơ bản vẫn hoạt động khi không có API.
>
> **Quan trọng:** không để AI tùy ý phát minh tên component hay API ManimGL.
> Phải cung cấp cho AI danh sách component được hỗ trợ (ví dụ: `TextBlock`, `FormulaBlock`, `GraphBlock`, `CodeBlock`).

---

### ⬜ Giai đoạn 6 — Hoàn thiện video YouTube

- Ghép lời thuyết minh và âm thanh (TTS tiếng Việt).
- Đồng bộ phụ đề SRT.
- Kiểm tra độ phân giải, thời lượng, âm lượng và các khung hình lỗi.
- Sinh tiêu đề, mô tả, thumbnail brief và metadata.
- Tạo bản preview trước khi xuất bản.

**Đầu ra:** video hoàn chỉnh, sẵn sàng để duyệt và đăng.
