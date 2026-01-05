import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ui_utils import init_placeholder
from datetime import datetime
from dialogs_ui import center_window, warn_required_fields


class BlockUIMixin:

    # ---------------- FILE DETAIL / BLOCKS ----------------

    def render_file_detail(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        file_data = self.data["folders"][self.current_folder]["files"][self.current_file]

        header = ttk.Frame(self.content_frame)
        header.pack(fill="x", pady=(0, 10))

        ttk.Button(header, text="← Back", command=self.render_file_list).pack(side="left")

        ttk.Label(
            header,
            text=self.current_file,
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=10)

        ttk.Button(header, text="Add Content", command=self.add_content_popup).pack(side="right")

        # -------- BLOCKS --------
        self.block_widgets = []
        blocks = file_data.get("blocks", [])

        if not blocks:
            empty_frame = ttk.Frame(self.content_frame)
            empty_frame.pack(fill="both", pady=20)

            ttk.Label(
                empty_frame,
                text="No content yet. Add some blocks.",
                foreground="gray",
                font=("Segoe UI", 12)
            ).pack(expand=True)

            return



        # -------- SEARCH BAR (always visible) --------
        search_var = tk.StringVar()
        search_entry = ttk.Entry(self.content_frame, textvariable=search_var)
        search_entry.pack(fill="x", padx=5, pady=5)
        init_placeholder(search_entry, "Search in this file...")

        # -------- SCROLL AREA (always exists) --------
        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


        for block in blocks:
            self.render_block(scroll_frame, block)

        # -------- BLOCK SEARCH + HIGHLIGHT --------
        def search_in_file(*args):
            query = search_var.get().strip().lower()
            if not query:
                return

            for frame, text in self.block_widgets:
                if query in text:
                    canvas.update_idletasks()
                    canvas_height = max(1, scroll_frame.winfo_height())
                    canvas.yview_moveto(frame.winfo_y() / canvas_height)
                    frame.configure(style="Highlight.TFrame")
                    self.after(1500, lambda f=frame: f.configure(style="TFrame"))
                    break

        search_var.trace_add("write", search_in_file)




    # ---------------- SINGLE BLOCK ----------------

    def render_block(self, parent, block):
        frame = ttk.Frame(parent, padding=10, relief="ridge")
        frame.pack(fill="x", pady=6)

        header_frame = ttk.Frame(frame)
        header_frame.pack(fill="x")

        ttk.Label(
            header_frame,
            text="",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", fill="x", expand=True)

        ttk.Button(
            header_frame,
            text="Edit",
            width=6,
            command=lambda b=block: self.edit_block_popup(b)
        ).pack(side="right", padx=2)

        ttk.Button(
            header_frame,
            text="Delete",
            width=6,
            command=lambda b=block: self.delete_block(b)
        ).pack(side="right", padx=2)

        content_text = ""

        if block["type"] == "heading":
            content_text = block["content"]
            ttk.Label(
                frame,
                text=content_text,
                font=("Segoe UI", 14, "bold")
            ).pack(anchor="w", pady=(2, 6))


        if block["type"] == "text":
            content_text = block["content"]
            content_label = ttk.Label(
                frame,
                text=content_text,
                wraplength=760,
                font=("Segoe UI", 11),
                justify="left"
            )
            content_label.pack(fill="x", anchor="w", pady=(4, 0))


        elif block["type"] == "code":
            content_text = block["content"]
            txt = tk.Text(
                frame,
                height=max(4, content_text.count("\n") + 1),
                wrap="none",
                borderwidth=1,
                relief="solid",
                highlightthickness=0,
                bg="#1e1e1e",
                fg="#dcdcdc",
                insertbackground="#ffffff"
            )
            txt.insert("1.0", content_text)
            txt.config(font=("Consolas", 11))
            txt.pack(fill="x", padx=2, pady=(10, 0))

        elif block["type"] == "link":
            content_text = block["content"]

            lbl = ttk.Label(
                frame,
                text=content_text,
                foreground="blue",
                cursor="hand2",
                font=("Segoe UI", 11, "underline")
            )
            lbl.pack(anchor="w", pady=(4, 0))

            def open_link(event=None, url=content_text):
                try:
                    if sys.platform.startswith("win"):
                        os.startfile(url)
                    elif sys.platform.startswith("darwin"):
                        os.system(f"open '{url}'")
                    else:
                        os.system(f"xdg-open '{url}'")
                except Exception as e:
                    messagebox.showerror("Open Link Error", str(e))

            lbl.bind("<Button-1>", open_link)


        elif block["type"] == "image":
            # 🔹 Small info note (very subtle)
            ttk.Label(
                frame,
                text="*Images won’t be shared or backed up.",
                font=("Segoe UI", 9, "italic"),
                foreground="#6b4e31"
            ).pack(anchor="w", pady=(0, 4))

            img_path = os.path.join(os.path.dirname(self.data_path), block["content"])
            try:
                from PIL import Image, ImageTk
                img = Image.open(img_path)
                img.thumbnail((500, 300))
                photo = ImageTk.PhotoImage(img)

                lbl = ttk.Label(frame, image=photo)
                lbl.image = photo  # keep reference
                lbl.pack(anchor="w")

                content_text = block["content"]

            except Exception:
                content_text = "[Image not found]"
                txt = tk.Text(
                    frame,
                    height=1,
                    wrap="none",
                    borderwidth=0,
                    highlightthickness=0,
                    fg="red"
                )
                txt.insert("1.0", content_text)
                txt.config(state="disabled")
                txt.pack(anchor="w")


        self.block_widgets.append(
            (frame, (content_text).lower())
        )

    # ---------------- BLOCK ACTIONS ----------------

    def delete_block(self, block):
        if not messagebox.askyesno("Delete Block", "Delete this block permanently?"):
            return

        file_data = self.data["folders"][self.current_folder]["files"][self.current_file]
        file_data["blocks"].remove(block)

        self.save_data()
        self.render_file_detail()

    def edit_block_popup(self, block):
        popup = tk.Toplevel(self)
        popup.title("Edit Block")
        popup.geometry("700x350")
        center_window(popup)
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Type").pack(pady=5)
        type_var = tk.StringVar(value=block["type"])
        ttk.Combobox(
            popup,
            textvariable=type_var,
            values=["Heading", "Text", "Code", "Link", "Image"],
            state="readonly"
        ).pack()

        ttk.Label(popup, text="Content").pack(pady=5)
        content_box = tk.Text(popup, height=8)
        content_box.pack(fill="both", padx=20, pady=(0, 12))

        image_path_var = tk.StringVar()

        if block["type"] != "image":
            content_box.insert("1.0", block["content"])

        def choose_image():
            path = filedialog.askopenfilename(
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")]
            )
            if path:
                image_path_var.set(path)

        ttk.Button(popup, text="Choose Image", command=choose_image).pack(pady=5)

        def save():
            block_type = type_var.get().lower()

            if block_type == "image":
                src = image_path_var.get()
                if src:
                    ext = os.path.splitext(src)[1]
                    filename = f"{int(datetime.now().timestamp())}{ext}"
                    dst = os.path.join(self.assets_dir, filename)
                    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                        fdst.write(fsrc.read())
                    block["content"] = os.path.relpath(dst, os.path.dirname(self.data_path))
            else:
                content = content_box.get("1.0", "end").strip()
                if not content:
                    warn_required_fields()
                    return
                block["content"] = content
            block["type"] = block_type

            self.save_data()
            popup.destroy()
            self.render_file_detail()

        ttk.Button(popup, text="Save", command=save).pack(pady=10)

    def add_content_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Add Content")
        popup.geometry("700x350")
        center_window(popup)
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Type").pack(pady=5)
        type_var = tk.StringVar(value="heading")
        ttk.Combobox(
            popup,
            textvariable=type_var,
            values=["Heading", "Text", "Code", "Link", "Image"],
            state="readonly"
        ).pack()

        ttk.Label(popup, text="Content").pack(pady=5)
        content_box = tk.Text(popup, height=8)
        content_box.pack(fill="both", padx=20, pady=(0, 12))
        content_box.focus()

        image_path_var = tk.StringVar()

        def choose_image():
            path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")]
            )
            if path:
                image_path_var.set(path)

        ttk.Button(popup, text="Choose Image", command=choose_image).pack(pady=5)

        def add():
            block_type = type_var.get().lower()
            file_data = self.data["folders"][self.current_folder]["files"][self.current_file]

            if block_type == "image":
                src = image_path_var.get()
                if not src:
                    warn_required_fields()
                    return

                ext = os.path.splitext(src)[1]
                filename = f"{int(datetime.now().timestamp())}{ext}"
                dst = os.path.join(self.assets_dir, filename)

                with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                    fdst.write(fsrc.read())

                content = os.path.relpath(dst, os.path.dirname(self.data_path))
            else:
                content = content_box.get("1.0", "end").strip()
                if not content:
                    warn_required_fields()
                    return

            if "blocks" not in file_data:
                file_data["blocks"] = []

            file_data["blocks"].append({
                "type": block_type,
                "content": content
            })

            self.save_data()
            popup.destroy()
            self.render_file_detail()

        ttk.Button(popup, text="Add", command=add).pack(pady=10)
