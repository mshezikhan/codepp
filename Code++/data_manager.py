import json
import os
from datetime import datetime
from tkinter import messagebox

APP_NAME = "Code++"
DEFAULT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Code++")
DEFAULT_FILE = os.path.join(DEFAULT_DIR, "Code++_Data.codepp")


class DataManagerMixin:

    @staticmethod
    def _get_created(obj, default="1970-01-01T00:00:00"):
        created = obj.get("created", default)
        try:
            return datetime.fromisoformat(created)
        except Exception:
            try:
                return datetime.fromisoformat(default)
            except Exception:
                return datetime.min

    def ensure_default_file(self):
        os.makedirs(DEFAULT_DIR, exist_ok=True)

        if not os.path.exists(DEFAULT_FILE):
            now = datetime.now().isoformat()
            default_data = {
                "meta": {
                    "app": APP_NAME,
                    "version": "1.0",
                    "created": now,
                    "last_modified": now
                },
                "folders": {}
            }
            with open(DEFAULT_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)

    def load_data(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

            if "meta" not in self.data:
                now = datetime.now().isoformat()
                self.data["meta"] = {
                    "app": APP_NAME,
                    "version": "1.0",
                    "created": now,
                    "last_modified": now
                }
            if "folders" not in self.data:
                self.data["folders"] = {}

            self.data_path = path
            if self.status_var is not None:
                self.update_status()

        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def save_data(self):
        try:
            if "meta" not in self.data:
                self.data["meta"] = {}
            self.data["meta"]["last_modified"] = datetime.now().isoformat()
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
