import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from dialogs_ui import simple_prompt, center_window, warn_required_fields



class FolderUIMixin:

    # ---------------- FOLDERS ----------------

    def render_folders(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        folders = self.data.get("folders", {})

        if not folders:
            ttk.Label(
                self.content_frame,
                text="No folders yet. Create one.",
                foreground="gray"
            ).pack(expand=True)
            return

        container = ttk.Frame(self.content_frame)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        grid = ttk.Frame(canvas)

        grid.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=grid, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        cols = 12
        row = col = 0

        sorted_folders = sorted(
            folders.items(),
            key=lambda item: self._get_created(item[1]),
            reverse=True
        )

        for folder_name, folder_data in sorted_folders:
            card = ttk.Frame(grid, padding=10, relief="ridge")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            ttk.Label(card, text="📁", font=("Segoe UI", 40)).pack()
            ttk.Label(card, text=folder_name, font=("Segoe UI", 12, "bold")).pack()
            ttk.Label(
                card,
                text=f"{len(folder_data.get('files', {}))} files",
                foreground="gray"
            ).pack()

            def left_handler(e, n=folder_name):
                self.open_folder(n)

            card.bind("<Button-1>", left_handler)
            for w in card.winfo_children():
                w.bind("<Button-1>", left_handler)

            def right_handler(e, n=folder_name):
                self.show_folder_context_menu(e, n)

            card.bind("<Button-3>", right_handler)
            for w in card.winfo_children():
                w.bind("<Button-3>", right_handler)

            col += 1
            if col >= cols:
                col = 0
                row += 1

    def show_folder_context_menu(self, event, folder_name):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Rename Folder", command=lambda: self.rename_folder(folder_name))
        menu.add_command(label="Delete Folder", command=lambda: self.delete_folder(folder_name))
        menu.add_command(label="Share Folder", command=lambda: self.share_folder(folder_name))

        menu.tk_popup(event.x_root, event.y_root)

    def rename_folder(self, old_name):
        new_name = simple_prompt(self, "Rename Folder", "New folder name:", old_name)
        if not new_name or new_name == old_name:
            return

        if new_name in self.data["folders"]:
            messagebox.showerror("Error", "A folder with this name already exists.")
            return

        self.data["folders"][new_name] = self.data["folders"].pop(old_name)

        if self.current_folder == old_name:
            self.current_folder = new_name

        self.save_data()
        self.render_folders()

    def delete_folder(self, folder_name):
        if not messagebox.askyesno("Delete Folder", f"Delete folder '{folder_name}' and all its files?"):
            return
        self.data["folders"].pop(folder_name, None)
        if self.current_folder == folder_name:
            self.current_folder = None
        self.save_data()
        self.render_folders()

    def share_folder(self, folder_name):
        folder_data = self.data["folders"].get(folder_name)
        if not folder_data:
            return

        export_data = {
            "type": "folder",
            "name": folder_name,
            "data": folder_data
        }

        path = filedialog.asksaveasfilename(
            defaultextension=".codepp",
            initialfile=f"{folder_name}.codepp",
            filetypes=[("Code++ Files", "*.codepp")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4)
            messagebox.showinfo("Shared", "Folder exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


    def create_folder_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Create Folder")
        popup.geometry("300x180")
        center_window(popup)

        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Folder Name").pack(pady=10)

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

            if name in self.data.get("folders", {}):
                messagebox.showerror("Error", "Folder already exists")
                return

            if "folders" not in self.data:
                self.data["folders"] = {}

            now = datetime.now().isoformat()
            self.data["folders"][name] = {
                "created": now,
                "files": {}
            }

            self.save_data()
            self.render_folders()
            popup.destroy()



        ttk.Button(popup, text="Create", command=create).pack(pady=15)
        ttk.Button(popup, text="Import Folder", command=self.import_folder).pack(pady=5)



    def import_folder(self):
        path = filedialog.askopenfilename(filetypes=[("Code++ Files", "*.codepp")])
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            if payload.get("type") != "folder":
                raise ValueError("Invalid folder file")

            name = payload["name"]
            data = payload["data"]

            now = datetime.now().isoformat()

            # Update folder timestamp
            data["created"] = now

            # Update files and blocks timestamps
            for file_data in data.get("files", {}).values():
                file_data["created"] = now
                for block in file_data.get("blocks", []):
                    block["created"] = now

            base = name
            i = 1
            while name in self.data["folders"]:
                name = f"{base}_{i}"
                i += 1

            self.data["folders"][name] = data
            self.save_data()
            self.render_folders()
            messagebox.showinfo("Imported", "Folder imported successfully.")

        except Exception as e:
            messagebox.showerror("Import Error", str(e))


    def open_folder(self, folder_name):
        self.current_folder = folder_name
        self.render_file_list()
