import os
import os
import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import RIGHT

from components.gesture_detail import GESTURES, GestureDetail
from config import FONT


class SessionDetail(tk.Frame):
    def __init__(self, parent, user_id, session_id, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.user_id = user_id
        self.session_id = session_id
        self.root = root
        self.is_recording = False

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text=f"Session {self.session_id}", font=(FONT, 20), bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]).pack()
        self.delete_session_button = tk.Button(top_frame,
                                               name="delete_session_button",
                                               text="x",
                                               command=self.delete_session,
                                               bg='darkred',
                                               fg='white',
                                               relief=tk.RIDGE, borderwidth=1)
        self.delete_session_button.pack_configure(side=RIGHT, ipadx=10, pady=(0, 0))

        # Create two frames for the two columns
        left_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        right_frame = tk.Frame(self, bg=self.root.colour_config["bg"])

        # Pack the frames side by side
        left_frame.pack(side='left', fill='both', expand=True)
        right_frame.pack(side='right', fill='both', expand=True)

        for index, gesture in enumerate(GESTURES):
            column = index % 2  # Remainder to determine the column
            is_left = column == 0  # True if the gesture is on the left column
            if is_left:
                gesture_detail = GestureDetail(left_frame, self.user_id, self.session_id, gesture, self.root)
                gesture_detail.pack(fill='x', anchor='nw', expand=True)
            else:
                gesture_detail = GestureDetail(right_frame, self.user_id, self.session_id, gesture, self.root)
                gesture_detail.pack(fill='x', anchor='nw', expand=True)



    def delete_session(self):
        # Ask for confirmation
        if msgbox.askyesno("Delete Session", f"Are you sure you want to delete session {self.session_id}?"):
            # Delete the session folder
            session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}')
            if os.path.exists(session_folder):
                import shutil
                shutil.rmtree(session_folder)

            # Refresh the user data view
            self.root.load_user_data(self.root.sidebar.listbox.curselection()[0])