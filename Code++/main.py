from main_ui import NotesApp


def main():
    app = NotesApp()
    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Silent fail for users
        try:
            # optional: log for you (not user)
            base = os.path.join(os.path.expanduser("~"), ".code++")
            os.makedirs(base, exist_ok=True)
            with open(os.path.join(base, "error.log"), "a", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass

        # exit silently
        sys.exit(0)
