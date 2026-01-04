import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from dialogs_ui import simple_prompt, center_window, warn_required_fields
from ui_utils import init_placeholder


class FileUIMixin:

    # ---------------- FILE LIST ----------------

    def render_file_list(self):
        self.current_file = None 
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        folder_data = self.data["folders"][self.current_folder]

        header = ttk.Frame(self.content_frame)
        header.pack(fill="x", pady=(0, 5))

        ttk.Button(
            header,
            text="← Back",
            command=self.back_to_home
        ).pack(side="left")

        ttk.Label(
            header,
            text=self.current_folder,
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=10)

        ttk.Button(
            header,
            text="Create File",
            command=self.create_file_popup
        ).pack(side="right")

        files = folder_data.get("files", {})

        if not files:
            empty_frame = ttk.Frame(self.content_frame)
            empty_frame.pack(fill="both", pady=20)

            ttk.Label(
                empty_frame,
                text="No files yet. Create one.",
                foreground="gray",
                font=("Segoe UI", 11)
            ).pack(expand=True)

            return

        search_var = tk.StringVar()
        search_entry = ttk.Entry(self.content_frame, textvariable=search_var)
        search_entry.pack(fill="x", padx=5, pady=(0, 5))

        container = ttk.Frame(self.content_frame)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        list_frame = ttk.Frame(canvas)

        list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._folder_files_frame = list_frame
        self._folder_files_canvas = canvas
        self._folder_files_data = files

        def populate_file_rows(filter_query=""):
            for child in list_frame.winfo_children():
                child.destroy()

            filter_lower = filter_query.lower().strip()

            sorted_files_local = sorted(
                self._folder_files_data.items(),
                key=lambda item: self._get_created(item[1]),
                reverse=True
            )

            for file_name, file_data in sorted_files_local:
                if filter_lower and filter_lower not in file_name.lower():
                    continue

                item = ttk.Frame(list_frame, padding=8, relief="ridge")
                item.pack(fill="x", pady=10)

                ttk.Label(
                    item,
                    text=file_name,
                    font=("Segoe UI", 12, "bold"),
               
                ).pack(side="left")


                ttk.Label(
                    item,
                    text=f"     {file_data.get("created", "")[:10]}",
                    foreground="gray"
                ).pack(side="right")

                def left_handler(e, n=file_name):
                    self.open_file(n)

                item.bind("<Button-1>", left_handler)
                for w in item.winfo_children():
                    w.bind("<Button-1>", left_handler)

                def right_handler(e, n=file_name):
                    self.show_file_context_menu(e, n)

                item.bind("<Button-3>", right_handler)
                for w in item.winfo_children():
                    w.bind("<Button-3>", right_handler)

        init_placeholder(search_entry, "Search files in this folder...")
        populate_file_rows()

        def on_folder_search_change(*args):
            query = search_var.get()
            if query == getattr(search_entry, "placeholder", ""):
                query = ""
            populate_file_rows(query)

        search_var.trace_add("write", on_folder_search_change)

    def show_file_context_menu(self, event, file_name):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Rename File", command=lambda: self.rename_file(file_name))
        menu.add_command(label="Delete File", command=lambda: self.delete_file(file_name))
        menu.add_command(label="Share File", command=lambda: self.share_file(file_name))
        menu.tk_popup(event.x_root, event.y_root)

    def rename_file(self, old_name):
        folder = self.data["folders"][self.current_folder]
        new_name = simple_prompt(self, "Rename File", "New file name:", old_name)
        if not new_name or new_name == old_name:
            return
        if new_name in folder.get("files", {}):
            messagebox.showerror("Error", "A file with this name already exists in this folder.")
            return

        folder["files"][new_name] = folder["files"].pop(old_name)

        if self.current_file == old_name:
            self.current_file = new_name

        self.save_data()
        self.render_file_list()

    def delete_file(self, file_name):
        if not messagebox.askyesno("Delete File", f"Delete file '{file_name}'?"):
            return
        folder = self.data["folders"][self.current_folder]
        folder["files"].pop(file_name, None)
        if self.current_file == file_name:
            self.current_file = None
        self.save_data()
        self.render_file_list()

    def share_file(self, file_name):
        folder = self.data["folders"][self.current_folder]
        file_data = folder["files"].get(file_name)
        if not file_data:
            return

        export_data = {
            "type": "file",
            "name": file_name,
            "data": file_data
        }

        path = filedialog.asksaveasfilename(
            defaultextension=".codepp",
            initialfile=f"{self.current_folder}_{file_name}.codepp",
            filetypes=[("Code++ Files", "*.codepp")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4)
            messagebox.showinfo("Exported", "File exported successfully.\nAsk your friend to import this file in Code++.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


    def back_to_home(self):
        self.current_folder = None
        self.render_folders()

    def create_file_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Create File")
        popup.geometry("300x180")
        popup.transient(self)
        popup.grab_set()
        center_window(popup)   # 👈 THIS LINE

        ttk.Label(popup, text="File Name").pack(pady=10)

        name_var = tk.StringVar()
        entry = ttk.Entry(popup, textvariable=name_var)
        entry.pack(fill="x", padx=20)
        entry.focus()
        entry.bind("<Return>", lambda e: create())

        def create():
            name = name_var.get().strip()
            if not name:
                warn_required_fields()
                return

            folder = self.data["folders"][self.current_folder]

            if name in folder.get("files", {}):
                messagebox.showerror("Error", "File already exists")
                return

            now = datetime.now().isoformat()
            folder["files"][name] = {
                "created": now,
                "blocks": []
            }

            self.save_data()
            self.render_file_list()
            popup.destroy()


        ttk.Button(popup, text="Create", command=create).pack(pady=15)
        ttk.Button(popup, text="Import File", command=self.import_file).pack(pady=5)


    def import_file(self):
        path = filedialog.askopenfilename(filetypes=[("Code++ Files", "*.codepp")])
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            if payload.get("type") != "file":
                raise ValueError("Invalid file")

            name = payload["name"]
            data = payload["data"]

            now = datetime.now().isoformat()

            # Update file timestamp
            data["created"] = now

            # Update all block timestamps
            for block in data.get("blocks", []):
                block["created"] = now

            folder = self.data["folders"][self.current_folder]["files"]

            base = name
            i = 1
            while name in folder:
                name = f"{base}_{i}"
                i += 1

            folder[name] = data
            self.save_data()
            self.render_file_list()
            messagebox.showinfo("Imported", "File imported successfully.")

        except Exception as e:
            messagebox.showerror("Import Error", str(e))


    def open_file(self, file_name):
        self.current_file = file_name
        self.render_file_detail()
