import threading
import pystray
from pystray import MenuItem as item
from PIL import Image
import tkinter as tk


class TrayManager:
    def __init__(self, app, icon_path=None):
        self.app = app
        self.icon = None
        self.icon_path = icon_path
        self._running = False

    def _create_image(self):
        if self.icon_path:
            return Image.open(self.icon_path)

        # Icon
        image = Image.open("icon.png")
        return image

    def show_tray(self):
        if self._running:
            return

        self._running = True

        image = self._create_image()

        menu = (
            item("Open Code++", self.open_app),
            item("Exit", self.exit_app)
        )

        self.icon = pystray.Icon(
            "Code++",
            image,
            "Code++",
            menu
        )

        threading.Thread(target=self.icon.run, daemon=True).start()

    def open_app(self):
        self.app.after(0, self._restore)

    def _restore(self):
        self.app.deiconify()
        self.app.lift()
        self.app.focus_force()

        # ✅ Re-maximize window
        try:
            # Windows
            self.app.state("zoomed")
        except:
            try:
                # Linux / others
                self.app.attributes("-zoomed", True)
            except:
                pass

        self.stop_tray()


    def exit_app(self):
        self.stop_tray()
        self.app.after(0, self.app.destroy)

    def stop_tray(self):
        if self.icon:
            self.icon.stop()
            self.icon = None
        self._running = False
