import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tray import TrayManager

from data_manager import (
    DataManagerMixin,
    APP_NAME,
    DEFAULT_FILE
)

from folders_ui import FolderUIMixin
from files_ui import FileUIMixin
from blocks_ui import BlockUIMixin
from ui_utils import init_placeholder


class NotesApp(
    tk.Tk,
    DataManagerMixin,
    FolderUIMixin,
    FileUIMixin,
    BlockUIMixin
):
    def __init__(self):
        super().__init__()

        self.tray = TrayManager(self)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ✅ keep reference
        self.app_icon = tk.PhotoImage(file="icon.png")

        # ✅ apply icon to THIS window
        self.iconphoto(True, self.app_icon)

        self.title(APP_NAME + " — Programmer’s Notebook")
        self.state("zoomed")
        self.minsize(800, 500)

        # -------- STATE --------
        self.current_folder = None
        self.current_file = None
        self.status_var = None
        self.search_results = []

        # -------- DATA --------
        self.data = {}
        self.data_path = DEFAULT_FILE

        self.ensure_default_file()

        self.assets_dir = os.path.join(
            os.path.dirname(self.data_path),
            "assets",
            "images"
        )
        os.makedirs(self.assets_dir, exist_ok=True)

        self.load_data(self.data_path)

        # -------- STYLE --------
        self.style = ttk.Style(self)
        self.style.configure("Highlight.TFrame", background="#fff2a8")

        # -------- Shortcuts Ctrl+N --------


        self.bind_all("<Control-n>", self.shortcut_new_file)
        self.bind_all("<Control-N>", self.shortcut_new_file)


        # -------- UI --------

        self.create_main_ui()

    def on_close(self):
        self.withdraw()
        self.tray.show_tray()


    # ---------------- UI ----------------

    def _window_active(self):
        return self.state() != "iconic" and self.focus_displayof() is not None


    def shortcut_new_file(self, event=None):
        # Safety: only when window is active
        if not self._window_active():
            return "break"

        # 1️⃣ Inside a file → create block
        if self.current_folder and self.current_file:
            self.add_content_popup()

        # 2️⃣ Inside a folder → create file
        elif self.current_folder:
            self.create_file_popup()

        # 3️⃣ On home screen → create folder
        else:
            self.create_folder_popup()

        return "break"


    def create_main_ui(self):
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(fill="x")

        title = ttk.Label(
            top_bar,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold")
        )
        title.pack(side="left")

        btn_frame = ttk.Frame(top_bar)
        btn_frame.pack(side="right")

        support_btn = ttk.Label(
            btn_frame,
            text="Support Code++",
            foreground="#0066cc",
            cursor="hand2",
            font=("Segoe UI", 10, "underline")
        )
        support_btn.pack(side="left", padx=(15, 0))
        support_btn.bind("<Button-1>", self.open_support_page)

        load_btn = ttk.Button(
            btn_frame,
            text="Load",
            command=self.load_button_action
        )
        load_btn.pack(side="left", padx=5)

        backup_btn = ttk.Button(
            btn_frame,
            text="Backup",
            command=self.backup_button_action
        )
        backup_btn.pack(side="left", padx=5)

        create_folder_btn = ttk.Button(
            btn_frame,
            text="Create Folder",
            command=self.create_folder_popup
        )
        create_folder_btn.pack(side="left", padx=5)


        # -------- GLOBAL SEARCH --------
        search_frame = ttk.Frame(self, padding=(10, 5))
        search_frame.pack(fill="x")

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill="x")
        search_entry.bind("<KeyRelease>", self.global_search)

        init_placeholder(search_entry, "Search across all notes...")

        # -------- MAIN CONTENT --------
        self.content_frame = ttk.Frame(self, padding=10)
        self.content_frame.pack(fill="both", expand=True)

        self.render_folders()

        # -------- STATUS BAR --------
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=5
        )
        status_bar.pack(fill="x", side="bottom")

        self.update_status()

    # ---------------- BUTTON ACTIONS ----------------

    def open_support_page(self, event=None):
        url = "https://www.buymeacoffee.com/mshezikhan"
        try:
            if sys.platform.startswith("win"):
                os.startfile(url)
            elif sys.platform.startswith("darwin"):
                os.system(f"open '{url}'")
            else:
                os.system(f"xdg-open '{url}'")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def load_button_action(self):
        file_path = filedialog.askopenfilename(
            title="Load Code++ File",
            filetypes=[("Code++ Files", "*.codepp")]
        )

        if not file_path:
            return

        # 🔴 Confirmation (VERY IMPORTANT)
        confirm = messagebox.askyesno(
            "Load Code++ File",
            "This will overwrite your current data.\n\n"
            "Make sure you have a backup if you want to keep it.\n\n"
            "Do you want to continue?"
        )

        if not confirm:
            return

        try:
            # 1️⃣ Load selected file
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "folders" not in data:
                raise ValueError("Invalid Code++ file")

            # 2️⃣ Ensure meta exists
            if "meta" not in data:
                now = datetime.now().isoformat()
                data["meta"] = {
                    "app": APP_NAME,
                    "version": "1.0",
                    "created": now,
                    "last_modified": now
                }

            if "folders" not in data:
                data["folders"] = {}

            # 3️⃣ OVERWRITE default workspace file
            with open(DEFAULT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # 4️⃣ Reload app state from default workspace
            self.data = data
            self.data_path = DEFAULT_FILE

            self.current_folder = None
            self.current_file = None

            self.update_status()
            self.render_folders()

            # # 5️⃣ Success feedback
            # messagebox.showinfo(
            #     "Workspace Replaced",
            #     "Workspace replaced successfully."
            # )

        except Exception as e:
            messagebox.showerror("Invalid File", str(e))


    def backup_button_action(self):
        file_path = filedialog.asksaveasfilename(
            title="Backup Code++ Data",
            defaultextension=".codepp",
            initialfile="Code++_Backup.codepp",
            filetypes=[("Code++ Files", "*.codepp")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)

            messagebox.showinfo(
                "Backup Created",
                "Backup saved successfully."
            )

        except Exception as e:
            messagebox.showerror("Backup Error", str(e))

    # ---------------- SEARCH ----------------

    def global_search(self, event=None):
        query = self.search_var.get().strip().lower()

        if not query or query == getattr(self, "global_placeholder", "").lower():
            self.render_folders()
            return

        results = []

        for folder_name, folder in self.data.get("folders", {}).items():
            for file_name, file in folder.get("files", {}).items():

                if query in file_name.lower():
                    results.append((folder_name, file_name, None))
                    continue

                for block in file.get("blocks", []):
                    content = block.get("content", "")
                    searchable = (content).lower()

                    if query in searchable:
                        results.append((folder_name, file_name, block))
                        break

        self.render_search_results(results)

    def render_search_results(self, results):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not results:
            ttk.Label(
                self.content_frame,
                text="No results found",
                foreground="gray"
            ).pack(expand=True)
            return

        for folder_name, file_name, block in results:
            item = ttk.Frame(self.content_frame, padding=8, relief="ridge")
            item.pack(fill="x", pady=5)

            text = f"{folder_name}  →  {file_name}"

            if block:
                preview = ""

                if block.get("type") == "heading":
                    preview = block.get("content", "")
                else:
                    preview = block.get("content", "")[:40]

                if preview:
                    text += f"  →  {preview}"

            label = ttk.Label(item, text=text)
            label.pack(side="left")

            def handler(e, f=folder_name, fi=file_name, b=block):
                self.open_search_result(f, fi, b)

            item.bind("<Button-1>", handler)
            for w in item.winfo_children():
                w.bind("<Button-1>", handler)

    def open_search_result(self, folder_name, file_name, block):
        self.current_folder = folder_name
        self.current_file = file_name
        self.render_file_detail()

        if not block:
            return

        self.after(100, lambda: self.scroll_to_block(block))

    def scroll_to_block(self, target_block):
        target_heading = target_block.get("heading", "").lower()
        for frame, text in self.block_widgets:
            if target_heading and target_heading in text:
                frame.update_idletasks()
                canvas = frame.nametowidget(frame.winfo_parent()).master
                canvas_height = max(1, frame.master.winfo_height())
                canvas.yview_moveto(frame.winfo_y() / canvas_height)
                frame.configure(style="Highlight.TFrame")
                self.after(
                    1500,
                    lambda f=frame: f.configure(style="TFrame")
                )
                break

    def update_status(self):
        if self.status_var is not None:
            self.status_var.set(f"Active File: {self.data_path}")
