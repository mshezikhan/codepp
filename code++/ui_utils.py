def init_placeholder(entry, placeholder_text, color="gray"):
    normal_color = entry.cget("foreground") or "black"
    entry.placeholder = placeholder_text
    entry.placeholder_color = color
    entry.normal_color = normal_color

    parent = entry.master
    root = parent.winfo_toplevel()
    if hasattr(root, "global_placeholder"):
        if "Search across all notes" in placeholder_text:
            root.global_placeholder = placeholder_text

    if entry.get() == "":
        entry.insert(0, placeholder_text)
        entry.config(foreground=color)

    def on_focus_in(event):
        if entry.get() == entry.placeholder:
            entry.delete(0, "end")
            entry.config(foreground=entry.normal_color)

    def on_focus_out(event):
        if entry.get() == "":
            entry.insert(0, entry.placeholder)
            entry.config(foreground=entry.placeholder_color)

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
