import os
import sys
import ast
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Resolve default working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_scenes_from_file(filepath):
    """Parse class names from python file that are likely Scenes."""
    scenes = []
    if not filepath or not os.path.isfile(filepath):
        return scenes
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = [getattr(b, "id", "") for b in node.bases if hasattr(b, "id")]
                if any("Scene" in b for b in base_names) or node.name.endswith("Scene"):
                    scenes.append(node.name)
        # Fallback if no Scene class explicitly found
        if not scenes:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    scenes.append(node.name)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return scenes

class ManimGLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ManimGL Video Studio")
        self.root.geometry("780x680")
        self.root.minsize(680, 580)

        # Center window on screen
        self.root.update_idletasks()
        w, h = 780, 680
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Process management
        self.current_process = None
        self.log_queue = queue.Queue()

        self._configure_styles()
        self._build_ui()
        self._poll_log_queue()

        # Auto-detect default python files in BASE_DIR
        self._auto_detect_file()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Fonts
        self.font_header = ("Segoe UI", 14, "bold")
        self.font_sub = ("Segoe UI", 9)
        self.font_bold = ("Segoe UI", 10, "bold")
        self.font_normal = ("Segoe UI", 10)
        self.font_mono = ("Consolas", 9)

        # Style colors
        style.configure(".", font=self.font_normal)
        style.configure("TLabelframe", padding=10)
        style.configure("TLabelframe.Label", font=self.font_bold, foreground="#1f2937")

        style.configure("Primary.TButton", font=self.font_bold, foreground="#ffffff", background="#2563eb")
        style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")])

        style.configure("Secondary.TButton", font=self.font_normal, foreground="#ffffff", background="#4b5563")
        style.map("Secondary.TButton", background=[("active", "#374151"), ("disabled", "#9ca3af")])

        style.configure("Danger.TButton", font=self.font_normal, foreground="#ffffff", background="#dc2626")
        style.map("Danger.TButton", background=[("active", "#b91c1c"), ("disabled", "#fca5a5")])

        style.configure("Success.TButton", font=self.font_normal, foreground="#ffffff", background="#059669")
        style.map("Success.TButton", background=[("active", "#047857"), ("disabled", "#6ee7b7")])

    def _build_ui(self):
        # 1. Header Banner
        header_frame = tk.Frame(self.root, bg="#1e293b", padx=16, pady=12)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="🎬 ManimGL Video Creator",
            font=self.font_header,
            fg="#f8fafc",
            bg="#1e293b"
        )
        title_lbl.pack(anchor=tk.W)

        desc_lbl = tk.Label(
            header_frame,
            text="Giao diện tạo video & tùy chọn độ phân giải dễ dàng với ManimGL",
            font=self.font_sub,
            fg="#94a3b8",
            bg="#1e293b"
        )
        desc_lbl.pack(anchor=tk.W)

        main_frame = ttk.Frame(self.root, padding="14")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 2. File & Scene Selection Frame
        source_frame = ttk.LabelFrame(main_frame, text="1. Chọn Kịch bản & Scene")
        source_frame.pack(fill=tk.X, pady=(0, 10))

        # Script File Row
        file_row = ttk.Frame(source_frame)
        file_row.pack(fill=tk.X, pady=4)
        ttk.Label(file_row, text="File Script (.py):", width=16).pack(side=tk.LEFT)
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_row, textvariable=self.file_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.file_var.trace_add("write", self._on_file_changed)

        browse_btn = ttk.Button(file_row, text="Duyệt file...", command=self._browse_file)
        browse_btn.pack(side=tk.RIGHT)

        # Scene Name Row
        scene_row = ttk.Frame(source_frame)
        scene_row.pack(fill=tk.X, pady=4)
        ttk.Label(scene_row, text="Tên Scene:", width=16).pack(side=tk.LEFT)

        self.scene_var = tk.StringVar()
        self.scene_combo = ttk.Combobox(scene_row, textvariable=self.scene_var)
        self.scene_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        refresh_btn = ttk.Button(scene_row, text="Tải lại Scene", command=self._update_scenes)
        refresh_btn.pack(side=tk.RIGHT)

        # 3. Resolution Frame
        res_frame = ttk.LabelFrame(main_frame, text="2. Tùy chọn Độ Phân Giải (Resolution)")
        res_frame.pack(fill=tk.X, pady=(0, 10))

        self.res_var = tk.StringVar(value="-l")

        resolutions = [
            ("-l", "480p (854x480, 15fps)", "Render cực nhanh, thích hợp xem thử"),
            ("-m", "720p (1280x720, 30fps)", "Chất lượng chuẩn HD vừa phải"),
            ("--hd", "1080p (1920x1080, 60fps)", "Full HD sắc nét, khuyên dùng cho video chính"),
            ("--uhd", "4K UHD (3840x2160, 60fps)", "Chất lượng cao nhất, render lâu hơn"),
        ]

        grid_frame = ttk.Frame(res_frame)
        grid_frame.pack(fill=tk.X, pady=4)

        for i, (val, label_text, note) in enumerate(resolutions):
            row = ttk.Frame(grid_frame)
            row.pack(fill=tk.X, pady=2)
            rb = ttk.Radiobutton(row, text=label_text, variable=self.res_var, value=val)
            rb.pack(side=tk.LEFT)
            ttk.Label(row, text=f"— {note}", foreground="#6b7280", font=self.font_sub).pack(side=tk.LEFT, padx=8)

        # 4. Output & Options Frame
        opt_frame = ttk.LabelFrame(main_frame, text="3. Tùy chọn xuất file")
        opt_frame.pack(fill=tk.X, pady=(0, 10))

        opts_row = ttk.Frame(opt_frame)
        opts_row.pack(fill=tk.X, pady=2)

        self.open_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_row, text="Tự động mở video sau khi tạo xong (-o)", variable=self.open_var).pack(side=tk.LEFT, padx=(0, 16))

        self.gif_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_row, text="Xuất ảnh GIF (-i)", variable=self.gif_var).pack(side=tk.LEFT, padx=(0, 16))

        self.transparent_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_row, text="Nền trong suốt (-t)", variable=self.transparent_var).pack(side=tk.LEFT)

        # Optional Custom File Name
        name_row = ttk.Frame(opt_frame)
        name_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(name_row, text="Tên file (tùy chọn):", width=18).pack(side=tk.LEFT)
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(name_row, textvariable=self.filename_var)
        self.filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 5. Buttons Actions Row
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        self.btn_render = ttk.Button(
            action_frame,
            text="🎬 Tạo Video",
            style="Primary.TButton",
            command=self._start_render
        )
        self.btn_render.pack(side=tk.LEFT, padx=(0, 8), ipadx=10, ipady=4)

        self.btn_preview = ttk.Button(
            action_frame,
            text="👁️ Xem trước (OpenGL Window)",
            style="Secondary.TButton",
            command=self._start_preview
        )
        self.btn_preview.pack(side=tk.LEFT, padx=(0, 8), ipady=4)

        self.btn_stop = ttk.Button(
            action_frame,
            text="⏹️ Dừng",
            style="Danger.TButton",
            state=tk.DISABLED,
            command=self._stop_process
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8), ipady=4)

        self.btn_open_folder = ttk.Button(
            action_frame,
            text="📂 Mở thư mục Video",
            style="Success.TButton",
            command=self._open_output_folder
        )
        self.btn_open_folder.pack(side=tk.RIGHT, ipady=4)

        # 6. Console Log Box
        log_frame = ttk.LabelFrame(main_frame, text="Nhật ký tiến trình (Console Log)")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            bg="#0f172a",
            fg="#e2e8f0",
            insertbackground="#ffffff",
            font=self.font_mono,
            height=10
        )
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 7. Status bar
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#f1f5f9",
            fg="#334155",
            padx=8,
            pady=3,
            font=self.font_sub
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _auto_detect_file(self):
        """Auto detect python scene files in BASE_DIR and scenes/."""
        candidates = [
            "integral_tutorial.py",
            "dp_tutorial.py",
            os.path.join("scenes", "pythagoras_tutorial.py"),
            "pythagoras_scene.py",
            "my_animation.py"
        ]
        for c in candidates:
            p = os.path.join(BASE_DIR, c)
            if os.path.isfile(p):
                self.file_var.set(p)
                self._on_file_changed()
                return
        # Or look for any .py file in scenes or BASE_DIR
        scenes_dir = os.path.join(BASE_DIR, "scenes")
        if os.path.isdir(scenes_dir):
            for item in os.listdir(scenes_dir):
                if item.endswith(".py"):
                    self.file_var.set(os.path.join(scenes_dir, item))
                    self._on_file_changed()
                    return
        for item in os.listdir(BASE_DIR):
            if item.endswith(".py") and item not in ("gui.py", "setup.py", "style.py"):
                self.file_var.set(os.path.join(BASE_DIR, item))
                self._on_file_changed()
                return

    def _browse_file(self):
        f = filedialog.askopenfilename(
            title="Chọn file kịch bản Manim",
            initialdir=BASE_DIR,
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if f:
            self.file_var.set(os.path.normpath(f))

    def _on_file_changed(self, *args):
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

    def _log(self, text):
        self.log_queue.put(text)

    def _poll_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_text.insert(tk.END, msg)
            self.log_text.see(tk.END)
        self.root.after(100, self._poll_log_queue)

    def _build_command(self, is_preview=False):
        script_file = self.file_var.get().strip()
        scene_name = self.scene_var.get().strip()

        if not script_file or not os.path.isfile(script_file):
            messagebox.showwarning("Thiếu file", "Vui lòng chọn file script Python (.py) hợp lệ!")
            return None

        if not scene_name:
            messagebox.showwarning("Thiếu Scene", "Vui lòng chọn hoặc nhập tên Scene cần render!")
            return None

        # Build args
        cmd = [sys.executable, "-m", "manimlib", script_file, scene_name]

        if not is_preview:
            # Video creation flags
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
        if not cmd:
            return
        self._run_command_async(cmd, mode="render")

    def _start_preview(self):
        cmd = self._build_command(is_preview=True)
        if not cmd:
            return
        self._run_command_async(cmd, mode="preview")

    def _run_command_async(self, cmd, mode="render"):
        if self.current_process and self.current_process.poll() is None:
            messagebox.showinfo("Đang chạy", "Một tiến trình khác đang chạy. Hãy chờ hoặc nhấn 'Dừng'.")
            return

        self.btn_render.config(state=tk.DISABLED)
        self.btn_preview.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        label_mode = "Tạo video" if mode == "render" else "Xem trước"
        self.status_var.set(f"Đang thực hiện ({label_mode})...")

        self.log_text.delete("1.0", tk.END)
        self._log(f"=== Bắt đầu {label_mode} ===\n")
        self._log(f"Lệnh: {' '.join(cmd)}\n\n")

        def worker():
            try:
                # Use Windows subprocess flags
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
                    creationflags=creation_flags
                )

                for line in iter(self.current_process.stdout.readline, ""):
                    if line:
                        self._log(line)

                self.current_process.stdout.close()
                return_code = self.current_process.wait()

                if return_code == 0:
                    self._log(f"\n✅ Hoàn tất thành công! ({label_mode})\n")
                    self.root.after(0, lambda: self.status_var.set("Hoàn tất thành công!"))
                else:
                    self._log(f"\n❌ Tiến trình kết thúc với mã lỗi: {return_code}\n")
                    self.root.after(0, lambda: self.status_var.set(f"Lỗi (Mã: {return_code})"))

            except Exception as e:
                self._log(f"\n❌ Lỗi hệ thống: {e}\n")
                self.root.after(0, lambda: self.status_var.set("Có lỗi xảy ra."))
            finally:
                self.root.after(0, self._on_finish_process)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_finish_process(self):
        self.current_process = None
        self.btn_render.config(state=tk.NORMAL)
        self.btn_preview.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def _stop_process(self):
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self._log("\n⚠️ Đã gửi lệnh dừng tiến trình!\n")
                self.status_var.set("Đã dừng.")
            except Exception as e:
                self._log(f"\nLỗi khi dừng: {e}\n")

    def _open_output_folder(self):
        video_dir = os.path.join(BASE_DIR, "videos")
        if not os.path.exists(video_dir):
            os.makedirs(video_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(video_dir)
        else:
            subprocess.run(["xdg-open", video_dir])

def main():
    root = tk.Tk()
    # Try icon if available
    app = ManimGLApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
