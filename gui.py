import os
import sys
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from core import (
    DEFAULT_TTS_VOICE,
    TTS_SPEED_OPTIONS,
    VIENEU_PRESET_VOICES,
    AIPipeline,
    CodeSession,
    GeminiAPIError,
    GeminiService,
    PlanSession,
    VieNeuTTSService,
    load_ai_config,
    parse_duration_from_topic,
    parse_scenes_from_file,
    play_wav_async,
    revoice_project_video,
    save_ai_config,
    stop_wav_playback,
)
from core.ai_pipeline import slug_to_scene_class, slugify_topic

# Resolve default working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
]

DURATION_OPTIONS = [
    ("30 giây", 30),
    ("45 giây", 45),
    ("60 giây (1 phút)", 60),
    ("90 giây (1.5 phút)", 90),
    ("120 giây (2 phút)", 120),
]

STYLE_OPTIONS = [
    ("Nền tối hiện đại (ChannelScene)", "channel_dark"),
    ("Bảng trắng + Thầy giáo Stickman", "teacher_light"),
]

RESOLUTION_OPTIONS = [
    ("480p Nhanh (-l)", "-l"),
    ("720p HD (-m)", "-m"),
    ("1080p Full HD (--hd)", "--hd"),
    ("4K UHD (--uhd)", "--uhd"),
]


class ManimGLApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Video Factory Studio — AI (Gemini), VieNeu-TTS & ManimGL")
        w, h = 1020, 860
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(900, 720)

        # Center window on screen
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Process & AI session state
        self.current_process: subprocess.Popen | None = None
        self.stop_event = threading.Event()
        self.is_busy = False
        self.is_playing_audio = False
        self._audio_reset_after_id: str | None = None
        self.log_queue: queue.Queue[str] = queue.Queue()

        self.current_plan_session: PlanSession | None = None
        self.current_code_session: CodeSession | None = None
        self.session_total_tokens = 0

        self.ai_cfg = load_ai_config()

        self._configure_styles()
        self._build_ui()
        self._poll_log_queue()
        self._auto_detect_file()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)

    # ------------------------------------------------------------------
    # GIAO DIỆN & STYLE
    # ------------------------------------------------------------------
    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        self.font_header = ("Segoe UI", 14, "bold")
        self.font_sub = ("Segoe UI", 9)
        self.font_bold = ("Segoe UI", 10, "bold")
        self.font_normal = ("Segoe UI", 10)
        self.font_editor = ("Segoe UI", 10)
        self.font_mono = ("Consolas", 9)

        style.configure(".", font=self.font_normal)
        style.configure("TNotebook.Tab", font=self.font_bold, padding=(14, 6))
        style.configure("TLabelframe", padding=8)
        style.configure("TLabelframe.Label", font=self.font_bold, foreground="#0f172a")

        style.configure("Primary.TButton", font=self.font_bold, foreground="#ffffff", background="#2563eb")
        style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")])

        style.configure("Success.TButton", font=self.font_bold, foreground="#ffffff", background="#059669")
        style.map("Success.TButton", background=[("active", "#047857"), ("disabled", "#6ee7b7")])

        style.configure("Secondary.TButton", font=self.font_normal, foreground="#ffffff", background="#475569")
        style.map("Secondary.TButton", background=[("active", "#334155"), ("disabled", "#94a3b8")])

        style.configure("Danger.TButton", font=self.font_normal, foreground="#ffffff", background="#dc2626")
        style.map("Danger.TButton", background=[("active", "#b91c1c"), ("disabled", "#fca5a5")])

    def _build_ui(self):
        # 1. Header Banner
        header_frame = tk.Frame(self.root, bg="#0f172a", padx=16, pady=10)
        header_frame.pack(fill=tk.X)

        tk.Label(
            header_frame,
            text="🎬 Video Factory Studio — AI & ManimGL",
            font=self.font_header,
            fg="#f8fafc",
            bg="#0f172a",
        ).pack(anchor=tk.W)

        tk.Label(
            header_frame,
            text="Quy trình thông minh: Nhập chủ đề ➔ Duyệt kịch bản & Nghe thử giọng AI VieNeu-TTS 48kHz (Bước 1) ➔ Sinh code ManimGL & Xuất MP4 có lồng tiếng (Bước 2–3)",
            font=self.font_sub,
            fg="#94a3b8",
            bg="#0f172a",
        ).pack(anchor=tk.W)

        # PanedWindow dọc để người dùng kéo chỉnh độ cao giữa phần làm việc và Console Log
        paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 4))

        top_container = ttk.Frame(paned)
        bottom_container = ttk.Frame(paned)
        paned.add(top_container, weight=3)
        paned.add(bottom_container, weight=1)

        # Notebook 2 Tabs
        self.notebook = ttk.Notebook(top_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_ai = ttk.Frame(self.notebook, padding=10)
        self.tab_manual = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.tab_ai, text="✨ Tạo Video bằng AI (Gemini)")
        self.notebook.add(self.tab_manual, text="🎛️ Studio Render Thủ Công (.py)")

        self._build_ai_tab(self.tab_ai)
        self._build_manual_tab(self.tab_manual)

        # Shared Console Log Box
        log_frame = ttk.LabelFrame(bottom_container, text="Nhật ký tiến trình (Console Log)")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.pack(fill=tk.X, pady=(0, 4))
        self.token_lbl_var = tk.StringVar(value="Token phiên này: 0")
        ttk.Label(log_toolbar, textvariable=self.token_lbl_var, foreground="#475569", font=self.font_sub).pack(side=tk.LEFT)
        ttk.Button(
            log_toolbar,
            text="Xóa log",
            command=lambda: self.log_text.delete("1.0", tk.END),
        ).pack(side=tk.RIGHT)

        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            bg="#0f172a",
            fg="#e2e8f0",
            insertbackground="#ffffff",
            font=self.font_mono,
            height=8,
        )
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status Bar
        self.status_var = tk.StringVar(value="Sẵn sàng. Nhập chủ đề và bấm 'Bước 1: Lập Kịch Bản' để bắt đầu.")
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#f1f5f9",
            fg="#334155",
            padx=10,
            pady=4,
            font=self.font_sub,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ------------------------------------------------------------------
    # TAB 1: TẠO VIDEO BẰNG AI (GEMINI)
    # ------------------------------------------------------------------
    def _build_ai_tab(self, parent: ttk.Frame):
        # Khung 0: Cấu hình Gemini API
        cfg_frame = ttk.LabelFrame(parent, text="Cấu hình Gemini API")
        cfg_frame.pack(fill=tk.X, pady=(0, 8))

        cfg_row = ttk.Frame(cfg_frame)
        cfg_row.pack(fill=tk.X)

        ttk.Label(cfg_row, text="API Key:").pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar(value=self.ai_cfg.get("api_key", ""))
        self.api_key_entry = ttk.Entry(cfg_row, textvariable=self.api_key_var, show="•", width=36)
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))

        self._show_key = False
        self.btn_toggle_key = ttk.Button(cfg_row, text="Hiện", width=6, command=self._toggle_api_key)
        self.btn_toggle_key.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(cfg_row, text="Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=self.ai_cfg.get("model", "gemini-2.5-flash"))
        self.model_combo = ttk.Combobox(cfg_row, textvariable=self.model_var, values=GEMINI_MODELS, width=20)
        self.model_combo.pack(side=tk.LEFT, padx=(6, 8))

        ttk.Button(cfg_row, text="💾 Lưu khóa", command=self._save_settings_clicked).pack(side=tk.RIGHT)

        # Khung 1: Nhập Chủ Đề -> Lập Kịch Bản
        step1_frame = ttk.LabelFrame(parent, text="1. Nhập Chủ Đề Bài Giảng (Bước 1 — Chưa tốn token viết code)")
        step1_frame.pack(fill=tk.X, pady=(0, 8))

        topic_row = ttk.Frame(step1_frame)
        topic_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(topic_row, text="Chủ đề / Yêu cầu:", width=16).pack(side=tk.LEFT)
        self.topic_var = tk.StringVar(value="Giải thích Định lý Pytago trong 45 giây")
        self.topic_entry = ttk.Entry(topic_row, textvariable=self.topic_var)
        self.topic_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        opt1_row = ttk.Frame(step1_frame)
        opt1_row.pack(fill=tk.X)

        ttk.Label(opt1_row, text="Thời lượng:", width=16).pack(side=tk.LEFT)
        self.duration_label_var = tk.StringVar(value="45 giây")
        self.duration_combo = ttk.Combobox(
            opt1_row,
            textvariable=self.duration_label_var,
            values=[lbl for lbl, _ in DURATION_OPTIONS],
            state="readonly",
            width=18,
        )
        self.duration_combo.pack(side=tk.LEFT, padx=(0, 14))

        ttk.Label(opt1_row, text="Phong cách:").pack(side=tk.LEFT, padx=(0, 6))
        self.style_label_var = tk.StringVar(value=STYLE_OPTIONS[0][0])
        self.style_combo = ttk.Combobox(
            opt1_row,
            textvariable=self.style_label_var,
            values=[lbl for lbl, _ in STYLE_OPTIONS],
            state="readonly",
            width=30,
        )
        self.style_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_load_plan = ttk.Button(
            opt1_row,
            text="📂 Mở kịch bản cũ...",
            command=self._load_existing_project_script,
        )
        self.btn_load_plan.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_step1_plan = ttk.Button(
            opt1_row,
            text="📝 Bước 1: Lập Kịch Bản",
            style="Primary.TButton",
            command=self._on_step1_generate_plan,
        )
        self.btn_step1_plan.pack(side=tk.RIGHT, ipadx=8, ipady=2)

        # Khung 2: Duyệt & Chỉnh Sửa Kịch Bản -> Sinh Code & Render
        step2_frame = ttk.LabelFrame(
            parent,
            text="2. Duyệt & Chỉnh sửa Kịch bản (Sửa tự do bên dưới trước khi bấm Sinh Code / Tạo Video)",
        )
        step2_frame.pack(fill=tk.BOTH, expand=True)

        info_row = ttk.Frame(step2_frame)
        info_row.pack(fill=tk.X, pady=(0, 4))
        self.plan_info_var = tk.StringVar(
            value="💡 Bấm 'Bước 1: Lập Kịch Bản' (hoặc tự gõ dàn ý vào khung dưới) -> Kiểm tra/sửa ý -> Bấm 'Duyệt & Tạo Video'."
        )
        ttk.Label(info_row, textvariable=self.plan_info_var, foreground="#1e40af", font=self.font_sub).pack(side=tk.LEFT)

        editor_wrap = ttk.Frame(step2_frame)
        editor_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.script_editor = tk.Text(
            editor_wrap,
            wrap=tk.WORD,
            bg="#ffffff",
            fg="#0f172a",
            insertbackground="#0f172a",
            selectbackground="#bfdbfe",
            font=self.font_editor,
            padx=10,
            pady=8,
            height=9,
            undo=True,
        )
        ed_scroll = ttk.Scrollbar(editor_wrap, orient=tk.VERTICAL, command=self.script_editor.yview)
        self.script_editor.configure(yscrollcommand=ed_scroll.set)
        self.script_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ed_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Thanh Thuyết minh Giọng đọc AI (VieNeu-TTS 48kHz — 100% Offline)
        tts_row = ttk.Frame(step2_frame)
        tts_row.pack(fill=tk.X, pady=(0, 6))

        self.tts_enabled_var = tk.BooleanVar(value=bool(self.ai_cfg.get("tts_enabled", True)))
        ttk.Checkbutton(
            tts_row,
            text="🎙️ Thuyết minh AI (VieNeu 48kHz):",
            variable=self.tts_enabled_var,
        ).pack(side=tk.LEFT, padx=(0, 6))

        saved_voice_id = str(self.ai_cfg.get("tts_voice", DEFAULT_TTS_VOICE))
        default_voice_lbl = VIENEU_PRESET_VOICES[0][0]
        for v_lbl, v_id in VIENEU_PRESET_VOICES:
            if v_id == saved_voice_id:
                default_voice_lbl = v_lbl
                break

        self.tts_voice_label_var = tk.StringVar(value=default_voice_lbl)
        self.tts_voice_combo = ttk.Combobox(
            tts_row,
            textvariable=self.tts_voice_label_var,
            values=[lbl for lbl, _ in VIENEU_PRESET_VOICES],
            state="readonly",
            width=35,
        )
        self.tts_voice_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(tts_row, text="Tốc độ:").pack(side=tk.LEFT, padx=(0, 4))
        saved_speed = float(self.ai_cfg.get("tts_speed", 1.0) or 1.0)
        default_speed_lbl = TTS_SPEED_OPTIONS[1][0]
        for s_lbl, s_val in TTS_SPEED_OPTIONS:
            if abs(s_val - saved_speed) < 0.03:
                default_speed_lbl = s_lbl
                break

        self.tts_speed_label_var = tk.StringVar(value=default_speed_lbl)
        self.tts_speed_combo = ttk.Combobox(
            tts_row,
            textvariable=self.tts_speed_label_var,
            values=[lbl for lbl, _ in TTS_SPEED_OPTIONS],
            state="readonly",
            width=18,
        )
        self.tts_speed_combo.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_tts_remux = ttk.Button(
            tts_row,
            text="🔄 Lồng tiếng lại MP4",
            command=self._on_revoice_existing_mp4,
        )
        self.btn_tts_remux.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_tts_preview = ttk.Button(
            tts_row,
            text="🔊 Nghe thử lời dẫn",
            command=self._on_preview_tts_clicked,
        )
        self.btn_tts_preview.pack(side=tk.RIGHT)

        # Hàng điều khiển Bước 2 & Bước 3
        act2_row = ttk.Frame(step2_frame)
        act2_row.pack(fill=tk.X)

        ttk.Label(act2_row, text="Chất lượng xuất:").pack(side=tk.LEFT)
        self.ai_res_label_var = tk.StringVar(value=RESOLUTION_OPTIONS[0][0])
        self.ai_res_combo = ttk.Combobox(
            act2_row,
            textvariable=self.ai_res_label_var,
            values=[lbl for lbl, _ in RESOLUTION_OPTIONS],
            state="readonly",
            width=19,
        )
        self.ai_res_combo.pack(side=tk.LEFT, padx=(6, 12))

        self.ai_open_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(act2_row, text="Tự mở video (-o)", variable=self.ai_open_var).pack(side=tk.LEFT, padx=(0, 10))

        self.ai_autofix_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(act2_row, text="Tự vá lỗi (tối đa 3 lần)", variable=self.ai_autofix_var).pack(side=tk.LEFT)

        # Các nút hành động bên phải
        self.btn_ai_stop = ttk.Button(
            act2_row,
            text="⏹️ Dừng",
            style="Danger.TButton",
            state=tk.DISABLED,
            command=self._stop_process,
        )
        self.btn_ai_stop.pack(side=tk.RIGHT, padx=(6, 0), ipady=2)

        self.btn_view_code = ttk.Button(
            act2_row,
            text="📄 Xem scene.py",
            command=self._open_code_viewer_modal,
            state=tk.DISABLED,
        )
        self.btn_view_code.pack(side=tk.RIGHT, padx=(6, 0), ipady=2)

        self.btn_step2_code_only = ttk.Button(
            act2_row,
            text="💻 Chỉ Sinh Code (.py)",
            style="Secondary.TButton",
            command=lambda: self._on_step2_execute(also_render=False),
        )
        self.btn_step2_code_only.pack(side=tk.RIGHT, padx=(6, 0), ipady=2)

        self.btn_step2_render = ttk.Button(
            act2_row,
            text="🎬 Duyệt & Tạo Video (.mp4)",
            style="Success.TButton",
            command=lambda: self._on_step2_execute(also_render=True),
        )
        self.btn_step2_render.pack(side=tk.RIGHT, ipadx=8, ipady=2)

    # ------------------------------------------------------------------
    # TAB 2: STUDIO RENDER THỦ CÔNG (.PY)
    # ------------------------------------------------------------------
    def _build_manual_tab(self, main_frame: ttk.Frame):
        source_frame = ttk.LabelFrame(main_frame, text="1. Chọn File Python (.py) & Scene")
        source_frame.pack(fill=tk.X, pady=(0, 10))

        file_row = ttk.Frame(source_frame)
        file_row.pack(fill=tk.X, pady=4)
        ttk.Label(file_row, text="File Script (.py):", width=16).pack(side=tk.LEFT)

        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_row, textvariable=self.file_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.file_var.trace_add("write", self._on_file_changed)

        ttk.Button(file_row, text="Duyệt file...", command=self._browse_file).pack(side=tk.RIGHT)

        scene_row = ttk.Frame(source_frame)
        scene_row.pack(fill=tk.X, pady=4)
        ttk.Label(scene_row, text="Tên Scene:", width=16).pack(side=tk.LEFT)

        self.scene_var = tk.StringVar()
        self.scene_combo = ttk.Combobox(scene_row, textvariable=self.scene_var)
        self.scene_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        ttk.Button(scene_row, text="Tải lại Scene", command=self._update_scenes).pack(side=tk.RIGHT)

        res_frame = ttk.LabelFrame(main_frame, text="2. Tùy chọn Độ Phân Giải (Resolution)")
        res_frame.pack(fill=tk.X, pady=(0, 10))

        self.res_var = tk.StringVar(value="-l")
        resolutions = [
            ("-l", "480p (854x480, 15fps)", "Render cực nhanh, thích hợp xem thử"),
            ("-m", "720p (1280x720, 30fps)", "Chất lượng chuẩn HD vừa phải"),
            ("--hd", "1080p (1920x1080, 60fps)", "Full HD sắc nét, khuyên dùng cho video chính"),
            ("--uhd", "4K UHD (3840x2160, 60fps)", "Chất lượng cao nhất, render lâu hơn"),
        ]
        for val, label_text, note in resolutions:
            row = ttk.Frame(res_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Radiobutton(row, text=label_text, variable=self.res_var, value=val).pack(side=tk.LEFT)
            ttk.Label(row, text=f"— {note}", foreground="#64748b", font=self.font_sub).pack(side=tk.LEFT, padx=8)

        opt_frame = ttk.LabelFrame(main_frame, text="3. Tùy chọn xuất file")
        opt_frame.pack(fill=tk.X, pady=(0, 12))

        opts_row = ttk.Frame(opt_frame)
        opts_row.pack(fill=tk.X, pady=2)

        self.open_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_row, text="Tự động mở video sau khi tạo xong (-o)", variable=self.open_var).pack(side=tk.LEFT, padx=(0, 16))

        self.gif_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_row, text="Xuất ảnh GIF (-i)", variable=self.gif_var).pack(side=tk.LEFT, padx=(0, 16))

        self.transparent_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_row, text="Nền trong suốt (-t)", variable=self.transparent_var).pack(side=tk.LEFT)

        name_row = ttk.Frame(opt_frame)
        name_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(name_row, text="Tên file (tùy chọn):", width=18).pack(side=tk.LEFT)
        self.filename_var = tk.StringVar()
        ttk.Entry(name_row, textvariable=self.filename_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(4, 0))

        self.btn_render = ttk.Button(
            action_frame,
            text="🎬 Tạo Video",
            style="Primary.TButton",
            command=self._start_render,
        )
        self.btn_render.pack(side=tk.LEFT, padx=(0, 8), ipadx=10, ipady=4)

        self.btn_preview = ttk.Button(
            action_frame,
            text="👁️ Xem trước (OpenGL Window)",
            style="Secondary.TButton",
            command=self._start_preview,
        )
        self.btn_preview.pack(side=tk.LEFT, padx=(0, 8), ipady=4)

        self.btn_stop = ttk.Button(
            action_frame,
            text="⏹️ Dừng",
            style="Danger.TButton",
            state=tk.DISABLED,
            command=self._stop_process,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8), ipady=4)

        self.btn_open_folder = ttk.Button(
            action_frame,
            text="📂 Mở thư mục Video",
            style="Success.TButton",
            command=self._open_output_folder,
        )
        self.btn_open_folder.pack(side=tk.RIGHT, ipady=4)

    # ------------------------------------------------------------------
    # HELPERS CHO CẤU HÌNH & TRẠNG THÁI NÚT BẤM
    # ------------------------------------------------------------------
    def _toggle_api_key(self):
        self._show_key = not self._show_key
        self.api_key_entry.config(show="" if self._show_key else "•")
        self.btn_toggle_key.config(text="Ẩn" if self._show_key else "Hiện")

    def _get_selected_duration(self) -> int:
        lbl = self.duration_label_var.get()
        for k, v in DURATION_OPTIONS:
            if k == lbl:
                return v
        return 45

    def _get_selected_style_mode(self) -> str:
        lbl = self.style_label_var.get()
        for k, v in STYLE_OPTIONS:
            if k == lbl:
                return v
        return "channel_dark"

    def _get_selected_ai_res_flag(self) -> str:
        lbl = self.ai_res_label_var.get()
        for k, v in RESOLUTION_OPTIONS:
            if k == lbl:
                return v
        return "-l"

    def _get_selected_tts_voice(self) -> str:
        lbl = self.tts_voice_label_var.get()
        for k, v in VIENEU_PRESET_VOICES:
            if k == lbl:
                return v
        return DEFAULT_TTS_VOICE

    def _get_selected_tts_speed(self) -> float:
        lbl = self.tts_speed_label_var.get()
        for k, v in TTS_SPEED_OPTIONS:
            if k == lbl:
                return float(v)
        return 1.0

    def _persist_settings(self):
        save_ai_config(
            {
                "api_key": self.api_key_var.get().strip(),
                "model": self.model_var.get().strip() or "gemini-2.5-flash",
                "default_duration": self._get_selected_duration(),
                "default_style": self._get_selected_style_mode(),
                "default_resolution": self._get_selected_ai_res_flag(),
                "tts_enabled": bool(self.tts_enabled_var.get()),
                "tts_voice": self._get_selected_tts_voice(),
                "tts_speed": self._get_selected_tts_speed(),
            }
        )

    def _save_settings_clicked(self):
        self._persist_settings()
        self.status_var.set("Đã lưu cấu hình Gemini API cục bộ (.ai_config.json).")
        messagebox.showinfo("Đã lưu", "Đã lưu cấu hình API Key & Model trên máy của bạn!")

    def _add_tokens(self, count: int):
        self.session_total_tokens += max(0, int(count))
        self.root.after(
            0,
            lambda: self.token_lbl_var.set(f"Token phiên này: {self.session_total_tokens:,}"),
        )

    def _set_busy(self, busy: bool, status_msg: str | None = None):
        self.is_busy = busy
        state_work = tk.DISABLED if busy else tk.NORMAL
        state_stop = tk.NORMAL if busy else tk.DISABLED

        self.btn_step1_plan.config(state=state_work)
        self.btn_step2_code_only.config(state=state_work)
        self.btn_step2_render.config(state=state_work)
        self.btn_load_plan.config(state=state_work)
        self.btn_tts_remux.config(state=state_work)
        if not self.is_playing_audio:
            self.btn_tts_preview.config(state=state_work)
        self.btn_render.config(state=state_work)
        self.btn_preview.config(state=state_work)

        self.btn_ai_stop.config(state=state_stop)
        self.btn_stop.config(state=state_stop)

        if not busy and self.current_code_session and self.current_code_session.scene_py_path.is_file():
            self.btn_view_code.config(state=tk.NORMAL)

        if status_msg:
            self.status_var.set(status_msg)

    # ------------------------------------------------------------------
    # XỬ LÝ BƯỚC 1 & BƯỚC 2-3 (AI PIPELINE)
    # ------------------------------------------------------------------
    def _create_pipeline(self) -> AIPipeline | None:
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip() or "gemini-2.5-flash"
        if not api_key:
            messagebox.showwarning(
                "Thiếu Gemini API Key",
                "Vui lòng nhập Gemini API Key vào ô 'API Key' ở trên cùng trước khi gọi AI!",
            )
            self.api_key_entry.focus_set()
            return None
        self._persist_settings()
        return AIPipeline(GeminiService(api_key=api_key, model=model))

    def _on_step1_generate_plan(self):
        if self.is_busy:
            return
        topic = self.topic_var.get().strip()
        if not topic:
            messagebox.showwarning("Thiếu chủ đề", "Vui lòng nhập chủ đề bài giảng cần tạo video!")
            self.topic_entry.focus_set()
            return

        pipeline = self._create_pipeline()
        if not pipeline:
            return

        dropdown_dur = self._get_selected_duration()
        detected_dur = parse_duration_from_topic(topic, fallback_sec=dropdown_dur)
        style_mode = self._get_selected_style_mode()

        self.stop_event.clear()
        self.log_text.delete("1.0", tk.END)
        self._set_busy(True, "Bước 1: Đang gọi Gemini lập kịch bản phân cảnh...")

        def worker():
            try:
                plan_session = pipeline.generate_plan(
                    topic=topic,
                    duration_sec=detected_dur,
                    style_mode=style_mode,
                    on_log=self._log,
                )
                self._add_tokens(plan_session.gemini_result.total_tokens)

                def update_ui():
                    self.current_plan_session = plan_session
                    self.script_editor.delete("1.0", tk.END)
                    self.script_editor.insert("1.0", plan_session.review_text)
                    self.plan_info_var.set(
                        f"✅ Đã lập kịch bản: projects/{plan_session.slug}/script.json ({plan_session.duration_sec}s) — "
                        f"Hãy duyệt/sửa nội dung bên dưới rồi bấm 'Duyệt & Tạo Video'!"
                    )
                    self._set_busy(
                        False,
                        "Bước 1 hoàn tất! Mời bạn duyệt/chỉnh sửa kịch bản trước khi sinh code.",
                    )

                self.root.after(0, update_ui)
            except GeminiAPIError as api_err:
                self._log(f"\n❌ {api_err}\n")
                self.root.after(0, lambda: messagebox.showerror("Lỗi Gemini API", str(api_err)))
                self.root.after(0, lambda: self._set_busy(False, "Lỗi khi gọi Gemini API."))
            except Exception as exc:
                self._log(f"\n❌ Lỗi không xác định ở Bước 1: {exc}\n")
                self.root.after(0, lambda: self._set_busy(False, "Có lỗi xảy ra ở Bước 1."))

        threading.Thread(target=worker, daemon=True).start()

    def _on_step2_execute(self, also_render: bool = True):
        if self.is_busy:
            return

        approved_text = self.script_editor.get("1.0", tk.END).strip()
        if not approved_text:
            messagebox.showwarning(
                "Chưa có kịch bản",
                "Khung kịch bản đang trống!\nHãy bấm '📝 Bước 1: Lập Kịch Bản' trước (hoặc tự gõ kịch bản vào khung).",
            )
            return

        pipeline = self._create_pipeline()
        if not pipeline:
            return

        topic = self.topic_var.get().strip() or "Bai giang moi"
        if self.current_plan_session:
            slug = self.current_plan_session.slug
            scene_class_name = self.current_plan_session.scene_class_name
            duration_sec = self.current_plan_session.duration_sec
        else:
            slug = slugify_topic(topic)
            scene_class_name = slug_to_scene_class(slug)
            duration_sec = parse_duration_from_topic(topic, fallback_sec=self._get_selected_duration())

        style_mode = self._get_selected_style_mode()
        res_flag = self._get_selected_ai_res_flag()
        open_after = self.ai_open_var.get()
        max_retries = 4 if self.ai_autofix_var.get() else 0
        tts_enabled = bool(self.tts_enabled_var.get())
        tts_voice = self._get_selected_tts_voice()
        tts_speed = self._get_selected_tts_speed()
        self._stop_audio_preview_ui()

        self.stop_event.clear()
        action_label = "Sinh code & Render video" if also_render else "Sinh code ManimGL (.py)"
        self._set_busy(True, f"Đang thực hiện: {action_label}...")

        def worker():
            try:
                code_session = pipeline.generate_code_from_approved_script(
                    approved_script_text=approved_text,
                    slug=slug,
                    scene_class_name=scene_class_name,
                    duration_sec=duration_sec,
                    style_mode=style_mode,
                    auto_fix_layout=self.ai_autofix_var.get(),
                    max_layout_retries=4 if self.ai_autofix_var.get() else 0,
                    tts_enabled=tts_enabled,
                    tts_voice=tts_voice,
                    tts_speed=tts_speed,
                    stop_event=self.stop_event,
                    on_log=self._log,
                )
                self.current_code_session = code_session
                self._add_tokens(code_session.gemini_result.total_tokens + code_session.fix_tokens_used)

                # Đồng bộ file scene.py vừa tạo sang Tab Studio Thủ Công
                self.root.after(0, lambda: self._sync_generated_scene_to_manual_tab(code_session))

                if not also_render or self.stop_event.is_set():
                    self.root.after(
                        0,
                        lambda: self._set_busy(
                            False,
                            f"Đã sinh xong code tại projects/{code_session.slug}/scene.py!",
                        ),
                    )
                    return

                ok, out_path = pipeline.render_with_self_healing(
                    code_session=code_session,
                    resolution_flag=res_flag,
                    open_after=open_after,
                    max_fix_retries=max_retries,
                    tts_enabled=tts_enabled,
                    tts_voice=tts_voice,
                    tts_speed=tts_speed,
                    script_text=approved_text,
                    stop_event=self.stop_event,
                    on_process_created=self._set_current_process,
                    on_log=self._log,
                )
                self.current_process = None

                if ok:
                    msg = f"🎉 Hoàn tất! Video đã lưu tại: {out_path}"
                    self.root.after(0, lambda: self._set_busy(False, msg))
                else:
                    self.root.after(
                        0,
                        lambda: self._set_busy(
                            False,
                            "Render chưa thành công. Xem chi tiết ở Console Log hoặc bấm 'Xem scene.py'.",
                        ),
                    )
            except GeminiAPIError as api_err:
                self._log(f"\n❌ {api_err}\n")
                self.root.after(0, lambda: messagebox.showerror("Lỗi Gemini API", str(api_err)))
                self.root.after(0, lambda: self._set_busy(False, "Lỗi khi gọi Gemini API."))
            except Exception as exc:
                self._log(f"\n❌ Lỗi hệ thống: {exc}\n")
                self.root.after(0, lambda: self._set_busy(False, "Có lỗi xảy ra."))
            finally:
                self.current_process = None

        threading.Thread(target=worker, daemon=True).start()

    def _set_current_process(self, proc: subprocess.Popen):
        self.current_process = proc

    def _sync_generated_scene_to_manual_tab(self, code_session: CodeSession):
        self.file_var.set(str(code_session.scene_py_path))
        self._update_scenes()
        self.scene_var.set(code_session.scene_class_name)
        self.filename_var.set(code_session.slug)
        self.btn_view_code.config(state=tk.NORMAL)

    def _load_existing_project_script(self):
        projects_dir = os.path.join(BASE_DIR, "projects")
        os.makedirs(projects_dir, exist_ok=True)
        f = filedialog.askopenfilename(
            title="Chọn file kịch bản đã lưu (script_review.md / script_approved.md / script.json)",
            initialdir=projects_dir,
            filetypes=[("Script Files", "*.md *.json"), ("All Files", "*.*")],
        )
        if not f:
            return
        p = Path(f)
        try:
            content = p.read_text(encoding="utf-8")
            if p.suffix.lower() == ".json":
                import json as _json
                from core import format_plan_to_review_text

                data = _json.loads(content)
                content = format_plan_to_review_text(data)
                if data.get("topic"):
                    self.topic_var.set(data["topic"])

            self.script_editor.delete("1.0", tk.END)
            self.script_editor.insert("1.0", content)

            slug = p.parent.name if p.parent != Path(projects_dir) else slugify_topic(self.topic_var.get())
            scene_py = p.parent / "scene.py"
            scene_cls = slug_to_scene_class(slug)
            if scene_py.is_file():
                found = parse_scenes_from_file(scene_py)
                if found:
                    scene_cls = found[0]
                self.current_code_session = CodeSession(
                    slug=slug,
                    scene_class_name=scene_cls,
                    project_dir=p.parent,
                    scene_py_path=scene_py,
                    approved_script_path=p,
                    code=scene_py.read_text(encoding="utf-8"),
                    gemini_result=None,  # type: ignore[arg-type]
                )
                self._sync_generated_scene_to_manual_tab(self.current_code_session)

            self.plan_info_var.set(f"📂 Đã nạp kịch bản từ: {p}")
            self.status_var.set(f"Đã nạp kịch bản từ {p.name}.")
        except Exception as exc:
            messagebox.showerror("Không đọc được file", str(exc))

    def _open_code_viewer_modal(self):
        if not self.current_code_session or not self.current_code_session.scene_py_path.is_file():
            messagebox.showinfo("Chưa có file", "Chưa có file `scene.py` nào được tạo trong phiên này.")
            return

        scene_path = self.current_code_session.scene_py_path
        win = tk.Toplevel(self.root)
        win.title(f"Mã nguồn ManimGL — {scene_path}")
        win.geometry("820x620")

        top_bar = ttk.Frame(win, padding=8)
        top_bar.pack(fill=tk.X)
        ttk.Label(top_bar, text=f"File: {scene_path}", font=self.font_bold).pack(side=tk.LEFT)

        txt = tk.Text(
            win,
            wrap=tk.NONE,
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#ffffff",
            font=("Consolas", 10),
            undo=True,
            padx=10,
            pady=8,
        )
        yscroll = ttk.Scrollbar(win, orient=tk.VERTICAL, command=txt.yview)
        xscroll = ttk.Scrollbar(win, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        txt.insert("1.0", scene_path.read_text(encoding="utf-8"))

        def save_code():
            new_code = txt.get("1.0", tk.END)
            scene_path.write_text(new_code, encoding="utf-8")
            if self.current_code_session:
                self.current_code_session.code = new_code
            self._update_scenes()
            self.status_var.set(f"Đã lưu thay đổi vào {scene_path.name}!")
            messagebox.showinfo("Đã lưu", f"Đã lưu mã nguồn vào:\n{scene_path}", parent=win)

        ttk.Button(top_bar, text="💾 Lưu scene.py", style="Primary.TButton", command=save_code).pack(side=tk.RIGHT)
        ttk.Button(
            top_bar,
            text="👁️ Chuyển sang Tab Xem trước",
            command=lambda: (save_code(), win.destroy(), self.notebook.select(self.tab_manual)),
        ).pack(side=tk.RIGHT, padx=(0, 8))

        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # CÁC HÀM CỦA TAB 2: STUDIO RENDER THỦ CÔNG
    # ------------------------------------------------------------------
    def _auto_detect_file(self):
        candidates = [
            os.path.join("scenes", "integral_tutorial.py"),
            os.path.join("scenes", "pythagoras_tutorial.py"),
            os.path.join("scenes", "dp_tutorial.py"),
        ]
        for c in candidates:
            p = os.path.join(BASE_DIR, c)
            if os.path.isfile(p):
                self.file_var.set(p)
                self._on_file_changed()
                return
        scenes_dir = os.path.join(BASE_DIR, "scenes")
        if os.path.isdir(scenes_dir):
            for item in os.listdir(scenes_dir):
                if item.endswith(".py"):
                    self.file_var.set(os.path.join(scenes_dir, item))
                    self._on_file_changed()
                    return

    def _browse_file(self):
        f = filedialog.askopenfilename(
            title="Chọn file kịch bản Manim (.py)",
            initialdir=BASE_DIR,
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
        )
        if f:
            self.file_var.set(os.path.normpath(f))

    def _on_file_changed(self, *_args):
        self._update_scenes()

    def _update_scenes(self):
        filepath = self.file_var.get().strip()
        scenes = parse_scenes_from_file(filepath)
        self.scene_combo["values"] = scenes
        if scenes:
            current = self.scene_var.get()
            if current not in scenes:
                self.scene_var.set(scenes[0])
        else:
            self.scene_var.set("")

    def _log(self, text: str):
        self.log_queue.put(text)

    def _poll_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_text.insert(tk.END, msg)
            self.log_text.see(tk.END)
        self.root.after(80, self._poll_log_queue)

    def _build_command(self, is_preview: bool = False) -> list[str] | None:
        script_file = self.file_var.get().strip()
        scene_name = self.scene_var.get().strip()

        if not script_file or not os.path.isfile(script_file):
            messagebox.showwarning("Thiếu file", "Vui lòng chọn file script Python (.py) hợp lệ!")
            return None

        if not scene_name:
            messagebox.showwarning("Thiếu Scene", "Vui lòng chọn hoặc nhập tên Scene cần render!")
            return None

        cmd = [sys.executable, "-m", "manimlib", script_file, scene_name]

        if not is_preview:
            cmd.append("-w")
            res_flag = self.res_var.get()
            if res_flag:
                cmd.append(res_flag)
            if self.open_var.get():
                cmd.append("-o")
            if self.gif_var.get():
                cmd.append("-i")
            if self.transparent_var.get():
                cmd.append("-t")
            fname = self.filename_var.get().strip()
            if fname:
                cmd.extend(["--file_name", fname])

        return cmd

    def _start_render(self):
        cmd = self._build_command(is_preview=False)
        if cmd:
            self._run_command_async(cmd, mode="render")

    def _start_preview(self):
        cmd = self._build_command(is_preview=True)
        if cmd:
            self._run_command_async(cmd, mode="preview")

    def _run_command_async(self, cmd: list[str], mode: str = "render"):
        if self.is_busy or (self.current_process and self.current_process.poll() is None):
            messagebox.showinfo("Đang chạy", "Một tiến trình khác đang chạy. Hãy chờ hoặc nhấn 'Dừng'.")
            return

        self.stop_event.clear()
        label_mode = "Tạo video" if mode == "render" else "Xem trước"
        self._set_busy(True, f"Đang thực hiện ({label_mode})...")

        self.log_text.delete("1.0", tk.END)
        self._log(f"=== Bắt đầu {label_mode} ===\n")
        self._log(f"Lệnh: {' '.join(cmd)}\n\n")

        def worker():
            try:
                creation_flags = 0
                if sys.platform == "win32":
                    creation_flags = subprocess.CREATE_NO_WINDOW if mode == "render" else 0

                self.current_process = subprocess.Popen(
                    cmd,
                    cwd=BASE_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    creationflags=creation_flags,
                )

                assert self.current_process.stdout is not None
                for line in iter(self.current_process.stdout.readline, ""):
                    if line:
                        self._log(line)

                self.current_process.stdout.close()
                return_code = self.current_process.wait()

                if return_code == 0:
                    self._log(f"\n✅ Hoàn tất thành công! ({label_mode})\n")
                    self.root.after(0, lambda: self._set_busy(False, "Hoàn tất thành công!"))
                else:
                    self._log(f"\n❌ Tiến trình kết thúc với mã lỗi: {return_code}\n")
                    self.root.after(0, lambda: self._set_busy(False, f"Lỗi (Mã: {return_code})"))
            except Exception as e:
                self._log(f"\n❌ Lỗi hệ thống: {e}\n")
                self.root.after(0, lambda: self._set_busy(False, "Có lỗi xảy ra."))
            finally:
                self.current_process = None

        threading.Thread(target=worker, daemon=True).start()

    def _stop_audio_preview_ui(self):
        stop_wav_playback()
        self.is_playing_audio = False
        if self._audio_reset_after_id:
            try:
                self.root.after_cancel(self._audio_reset_after_id)
            except Exception:
                pass
            self._audio_reset_after_id = None
        if hasattr(self, "btn_tts_preview"):
            self.btn_tts_preview.config(text="🔊 Nghe thử lời dẫn")

    def _resolve_current_slug(self) -> str:
        if self.current_code_session:
            return self.current_code_session.slug
        if self.current_plan_session:
            return self.current_plan_session.slug
        return slugify_topic(self.topic_var.get().strip() or "bai_giang_moi")

    def _on_preview_tts_clicked(self):
        if self.is_playing_audio:
            self._stop_audio_preview_ui()
            self.status_var.set("Đã dừng phát nghe thử.")
            return

        if self.is_busy:
            return

        # Hỗ trợ bôi đen 1 đoạn để nghe thử nhanh hoặc đọc toàn bộ kịch bản
        selected_snippet = ""
        try:
            if self.script_editor.tag_ranges(tk.SEL):
                selected_snippet = self.script_editor.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except Exception:
            selected_snippet = ""

        full_script = self.script_editor.get("1.0", tk.END).strip()
        if not selected_snippet and not full_script:
            messagebox.showwarning(
                "Chưa có nội dung",
                "Khung kịch bản đang trống! Hãy bấm '📝 Bước 1: Lập Kịch Bản' hoặc nhập văn bản cần đọc thử.",
            )
            return

        voice = self._get_selected_tts_voice()
        speed = self._get_selected_tts_speed()
        self._persist_settings()
        slug = self._resolve_current_slug()
        proj_dir = Path(BASE_DIR) / "projects" / slug

        self.stop_event.clear()
        self._set_busy(True, f"🎙️ Đang tạo giọng đọc thử ({voice}, {speed:.1f}x)...")

        def worker():
            try:
                svc = VieNeuTTSService.get_instance()
                if selected_snippet:
                    preview_wav = proj_dir / "audio" / "snippet_preview.wav"
                    self._log(f"\n🎙️ [Nghe thử đoạn chọn] Giọng `{voice}` ({speed:.1f}x)...\n")
                    dur = svc.synthesize_to_wav(
                        text=selected_snippet,
                        output_wav=preview_wav,
                        voice=voice,
                        speed=speed,
                        on_log=self._log,
                    )
                else:
                    pack = svc.synthesize_script_scenes(
                        script_text=full_script,
                        project_dir=proj_dir,
                        voice=voice,
                        speed=speed,
                        stop_event=self.stop_event,
                        on_log=self._log,
                    )
                    if not pack:
                        self.root.after(0, lambda: self._set_busy(False, "Không tìm thấy lời dẫn để đọc."))
                        return
                    preview_wav = pack.preview_wav_path
                    dur = pack.total_audio_duration + max(0, len(pack.clips) - 1) * 0.42

                def start_play():
                    self._set_busy(False, f"🔊 Đang phát giọng đọc `{voice}` ({dur:.1f}s)... Bấm '⏹ Dừng nghe' để ngắt.")
                    if play_wav_async(preview_wav):
                        self.is_playing_audio = True
                        self.btn_tts_preview.config(text="⏹ Dừng nghe", state=tk.NORMAL)
                        wait_ms = int((dur + 0.35) * 1000)
                        self._audio_reset_after_id = self.root.after(wait_ms, self._stop_audio_preview_ui)

                self.root.after(0, start_play)
            except Exception as exc:
                self._log(f"\n❌ Lỗi VieNeu-TTS: {exc}\n")
                self.root.after(0, lambda: messagebox.showerror("Lỗi TTS", str(exc)))
                self.root.after(0, lambda: self._set_busy(False, "Có lỗi khi tạo giọng đọc thử."))

        threading.Thread(target=worker, daemon=True).start()

    def _on_revoice_existing_mp4(self):
        if self.is_busy:
            return
        script_text = self.script_editor.get("1.0", tk.END).strip()
        if not script_text:
            messagebox.showwarning("Chưa có kịch bản", "Khung kịch bản đang trống! Hãy nạp kịch bản của video cần lồng tiếng.")
            return

        self._stop_audio_preview_ui()
        voice = self._get_selected_tts_voice()
        speed = self._get_selected_tts_speed()
        open_after = bool(self.ai_open_var.get())
        slug = self._resolve_current_slug()
        self._persist_settings()

        self.stop_event.clear()
        self._set_busy(True, f"🔄 Đang lồng tiếng lại cho videos/{slug}.mp4 ({voice}, {speed:.1f}x)...")

        def worker():
            try:
                out_mp4 = revoice_project_video(
                    slug=slug,
                    script_text=script_text,
                    voice=voice,
                    speed=speed,
                    open_after=open_after,
                    stop_event=self.stop_event,
                    on_log=self._log,
                )
                if out_mp4 and out_mp4.is_file():
                    self.root.after(
                        0,
                        lambda: self._set_busy(False, f"🎉 Đã lồng tiếng mới thành công: {out_mp4}"),
                    )
                else:
                    self.root.after(0, lambda: self._set_busy(False, "Đã dừng hoặc không có lời dẫn."))
            except FileNotFoundError as fnf:
                self._log(f"\n⚠️ {fnf}\n")
                self.root.after(0, lambda: messagebox.showwarning("Chưa có MP4", str(fnf)))
                self.root.after(0, lambda: self._set_busy(False, "Chưa có file MP4 gốc để lồng tiếng."))
            except Exception as exc:
                self._log(f"\n❌ Lỗi khi lồng tiếng lại: {exc}\n")
                self.root.after(0, lambda: messagebox.showerror("Lỗi lồng tiếng", str(exc)))
                self.root.after(0, lambda: self._set_busy(False, "Lỗi khi lồng tiếng lại."))

        threading.Thread(target=worker, daemon=True).start()

    def _stop_process(self):
        self.stop_event.set()
        self._stop_audio_preview_ui()
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self._log("\n⚠️ Đã gửi lệnh dừng tiến trình!\n")
                self.status_var.set("Đã dừng.")
            except Exception as e:
                self._log(f"\nLỗi khi dừng: {e}\n")

    def _on_close_window(self):
        self.stop_event.set()
        self._stop_audio_preview_ui()
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
            except Exception:
                pass
        self.root.destroy()

    def _open_output_folder(self):
        video_dir = os.path.join(BASE_DIR, "videos")
        os.makedirs(video_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(video_dir)
        else:
            subprocess.run(["xdg-open", video_dir])


def main():
    root = tk.Tk()
    ManimGLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
