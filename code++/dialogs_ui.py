import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def simple_prompt(root, title, label, initial=""):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry("300x150")
    center_window(popup)
    popup.transient(root)
    popup.grab_set()

    ttk.Label(popup, text=label).pack(pady=10)

    var = tk.StringVar(value=initial)
    entry = ttk.Entry(popup, textvariable=var)
    entry.pack(fill="x", padx=20)
    entry.focus()

    result = {"value": None}

    def ok():
        text = var.get().strip()
        if text:
            result["value"] = text
        popup.destroy()

    def cancel():
        popup.destroy()

    btn_frame = ttk.Frame(popup)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="OK", command=ok).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=cancel).pack(side="left", padx=5)

    popup.wait_window()
    return result["value"]

def warn_required_fields():
    messagebox.showwarning(
        "Missing Information",
        "Please fill all required fields."
    )