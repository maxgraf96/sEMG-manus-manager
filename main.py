import os
import time

import tkinter as tk
from tkinter import ttk
from components.VerticallyScrolledFrame import VerticalScrolledFrame
from PIL import ImageTk, Image
from cefpython3 import cefpython as cef

import ctypes

from components.gesture_detail import p_visualiser, q_visualiser, on_browser_window_close, \
    get_browser_open
from components.session_detail import SessionDetail
from components.sidebar import Sidebar
from config import FONT, BG_COLOUR_LIGHT, FG_COLOUR_LIGHT, BG_COLOUR_DARK, FG_COLOUR_DARK
from helpers import configure_recursively

ctypes.windll.shcore.SetProcessDpiAwareness(1)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('sEMG Manus Manager')
        self.iconbitmap('resources/tap.ico')
        self.geometry("1500x800")
        self.configure(bg=BG_COLOUR_LIGHT)  # Set the background color of the main window
        # Add state variable for theme
        self.theme_mode = "light"
        self.colour_config = {
            "bg": BG_COLOUR_LIGHT,
            "fg": FG_COLOUR_LIGHT,
            # border colour
            "bc": "grey",
        }

        self.create_status_bar()
        self.create_widgets()

        cef.DpiAware.EnableHighDpiSupport()
        cef.Initialize()

    def create_widgets(self):
        self.sidebar = Sidebar(self, self.load_user_data)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.detail_frame = VerticalScrolledFrame(self)
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        self.status_bar = tk.Frame(self, height=36, bg='grey')  # Create a frame for the status bar
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)  # Attach the status bar to the bottom
        self.status_bar.pack_propagate(False)  # Prevent the status bar from resizing

        # MANUS status label
        self.status_label = tk.Label(self.status_bar, text="Waiting for Manus connection...", bg='grey', anchor='e')
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Light/dark theme toggle button
        # Load the ico file
        photo_image = ImageTk.PhotoImage(file="resources/day-and-night.ico")
        # Create the button and set the image
        self.theme_toggle_button = tk.Button(self.status_bar, image=photo_image, name="theme_toggle_button",
                                             command=self.toggle_theme, bg='grey', borderwidth=0, width=24, height=24)
        self.theme_toggle_button.image = photo_image
        self.theme_toggle_button.pack(side=tk.LEFT, padx=10)

    def load_user_data(self, user_id):
        user_name = self.sidebar.get_user_name(f'u_{user_id}')

        # Clear the detail frame
        for widget in self.detail_frame.interior.winfo_children():
            widget.destroy()

        tk.Label(self.detail_frame.interior, text=f"User {user_id} - {user_name}", font=(FONT, 20),
                 bg=self.colour_config["bg"],
                 fg=self.colour_config["fg"]).pack(pady=(10, 0))

        user_folder = os.path.join('user_data', f'u_{user_id}')
        session_folders = [folder for folder in os.listdir(user_folder) if folder.startswith('s_')]

        for session_folder in sorted(session_folders, key=lambda x: int(x.split('_')[1])):
            session_id = session_folder.split('_')[1]
            session_detail = SessionDetail(self.detail_frame.interior, user_id, session_id, self)
            session_detail.pack(fill=tk.BOTH, expand=True)

        # Add New Session button
        new_session_button = tk.Button(self.detail_frame.interior, text="Add New Session",
                                       command=lambda: self.create_new_session(user_id), bg=self.colour_config["bg"],
                                       fg=self.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        new_session_button.pack(ipadx=20, pady=10)

    def create_new_session(self, user_id):
        user_folder = os.path.join('user_data', f'u_{user_id}')
        existing_sessions = [folder for folder in os.listdir(user_folder) if folder.startswith('s_')]
        next_session_id = 1 if not existing_sessions else max(
            [int(folder.split('_')[1]) for folder in existing_sessions]) + 1

        new_session_folder = os.path.join(user_folder, f's_{next_session_id}')
        os.makedirs(new_session_folder, exist_ok=True)

        # Refresh the user data view to include the new session
        self.load_user_data(user_id)

    def create_new_session_button(self, user_folder):
        new_session_button = tk.Button(self.detail_frame, text="Create New Session",
                                       command=lambda: self.create_new_session(user_folder))
        new_session_button.pack(pady=20)

    def toggle_theme(self):
        if self.theme_mode == "light":
            self.theme_mode = "dark"
            self.colour_config = {
                "bg": BG_COLOUR_DARK,
                "fg": FG_COLOUR_DARK,
            }
        else:
            self.theme_mode = "light"
            self.colour_config = {
                "bg": BG_COLOUR_LIGHT,
                "fg": FG_COLOUR_LIGHT,

            }

        bg = self.colour_config["bg"]

        # Configure all widgets recursively
        configure_recursively(self, self.colour_config)

        self.detail_frame.canvas.configure(bg=bg)
        self.status_bar.configure(bg='grey')
        self.status_label.configure(bg='grey', fg='black')

    def on_close(self):
        if get_browser_open():
            # Close the browser window
            on_browser_window_close()

        cef.Shutdown()
        q_visualiser.put("terminate")
        if p_visualiser is not None:
            p_visualiser.wait()
        self.destroy()


if __name__ == '__main__':
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
