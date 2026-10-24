# Nhật ký Triển khai Kỹ thuật — Video Factory

Tài liệu ghi nhận kiến trúc thực tế đã hoàn thiện của hệ thống **Video Factory Studio (Gemini AI + VieNeu-TTS + ManimGL)**.

---

## 1. Kiến trúc tổng thể đã triển khai

1. **Lõi đồ họa ManimGL 1.7.2 tích hợp trực tiếp (`manimlib/`, `style.py`, `components/`)**:
   - Đóng gói độc lập trong repository dưới dạng package `video-factory` quản lý bằng `uv` (`pyproject.toml`).
   - Hệ thống **Motion Design Studio v2** (`ChannelScene` trong `style.py`): nền lưới kiến trúc tối màu, tiêu đề chuyển sắc gradient, thanh chú thích pill, thẻ hộp `make_box`, nhãn `make_badge`, mũi tên `make_arrow`, tự động căn tỷ lệ lấp đầy vùng trung tâm / hai cột (`fit_in_center_zone`, `fit_in_left_zone`, `fit_in_right_zone`) và bộ chuyển động mượt (`pop_in`, `stagger_in`, `flow_to`, `morph_text_anim`, `pulse_focus`).
   - Vá triệt để lỗi biên dịch LaTeX song song và bộ đệm `diskcache` trong `manimlib/utils/tex_file_writing.py` & `manimlib/tex_templates.yml`.

2. **Quy trình AI 3 bước có kiểm duyệt & tự sửa lỗi (`core/`)**:
   - **Bước 1 — Planner (`core/prompt_builder.py`, `core/ai_pipeline.py`)**: Gọi Gemini API sinh kịch bản JSON cấu trúc 3 hồi (*Hook ➔ Build ➔ Resolution*) và hiển thị bản nháp Tiếng Việt lên giao diện để người dùng duyệt/sửa trước khi sinh code.
   - **Bước 2 — Coder & Layout Auditor (`core/layout_auditor.py`)**: Sinh file `scene.py` và chạy kiểm định headless tự động phát hiện 7 nhóm lỗi bố cục (tràn viền camera, đè chữ, khung đè chữ, chữ tràn ô bảng, mũi tên cắt chữ/xuyên ô, lệch khung công thức) để tự động căn chỉnh trước khi xuất MP4.
   - **Bước 3 — Self-Healing Renderer**: Tự động kết xuất video `.mp4` (480p / 720p / 1080p / 4K) và tự vá lỗi nếu phát sinh Traceback.

3. **Thuyết minh Giọng đọc AI Tiếng Việt Offline (`core/tts_service.py`)**:
   - Tích hợp `VieNeu-TTS` (48kHz, 100% offline, 25 giọng đọc Bắc – Trung – Nam cài sẵn).
   - Cơ chế **Audio-First Per-Scene Sync**: Thu âm từng phân cảnh trước khi sinh code để truyền thời lượng thực tế cho Coder, sau đó dùng `ffmpeg` ghép đồng bộ từng phân cảnh vào `.mp4` (tự động giữ tĩnh khung hình cuối cảnh bằng `tpad=stop_mode=clone` nếu lời giảng dài hơn hoạt ảnh, triệt tiêu hoàn toàn hiện tượng đứt câu hoặc lệch cảnh).
   - Hỗ trợ nghe thử trực tiếp (`winsound`) và lồng tiếng lại trên video có sẵn mà không cần gọi lại API.

4. **Bảo mật cấu hình & Khóa API (`core/config_store.py`, `.gitignore`, `.env.example`)**:
   - Khóa `GEMINI_API_KEY` chỉ lưu cục bộ tại `.ai_config.json` hoặc `.env` (đã loại trừ hoàn toàn trong `.gitignore`).
