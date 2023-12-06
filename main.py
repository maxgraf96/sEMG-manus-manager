import os
import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import simpledialog, ttk
from tkinter import *
from components.VerticallyScrolledFrame import VerticalScrolledFrame

import ctypes

from config import FONT, BG_COLOUR, FG_COLOUR

ctypes.windll.shcore.SetProcessDpiAwareness(1)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('sEMG Manus Manager')
        self.geometry("1300x800")
        self.configure(bg=BG_COLOUR)  # Set the background color of the main window

        self.create_status_bar()
        self.create_widgets()

    def create_widgets(self):
        self.sidebar = Sidebar(self, self.load_user_data)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.detail_frame = VerticalScrolledFrame(self)
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        self.status_bar = tk.Frame(self, height=25, bg='grey')  # Create a frame for the status bar
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)  # Attach the status bar to the bottom
        self.status_bar.pack_propagate(False)  # Prevent the status bar from resizing

        self.status_label = tk.Label(self.status_bar, text="Waiting for Manus connection...", bg='grey', anchor='e')
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def load_user_data(self, user_id):
        user_name = self.sidebar.get_user_name(f'u_{user_id}')

        # Clear the detail frame
        for widget in self.detail_frame.interior.winfo_children():
            widget.destroy()

        tk.Label(self.detail_frame.interior, text=f"User {user_id} - {user_name}", font=(FONT, 20), bg=BG_COLOUR,
                 fg=FG_COLOUR).pack(pady=(10, 0))

        user_folder = os.path.join('user_data', f'u_{user_id}')
        session_folders = [folder for folder in os.listdir(user_folder) if folder.startswith('s_')]

        for session_folder in sorted(session_folders, key=lambda x: int(x.split('_')[1])):
            session_id = session_folder.split('_')[1]
            session_detail = SessionDetail(self.detail_frame.interior, user_id, session_id, self)
            session_detail.pack(fill=tk.BOTH, expand=True)

        # Add New Session button
        new_session_button = tk.Button(self.detail_frame.interior, text="Add New Session",
                                       command=lambda: self.create_new_session(user_id), bg=BG_COLOUR, fg=FG_COLOUR)
        new_session_button.pack(pady=10)

        # buttons = []
        # for i in range(10):
        #     buttons.append(ttk.Button(self.detail_frame.interior, text="Button " + str(i)))
        #     buttons[-1].pack()

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


class Sidebar(tk.Frame):
    def __init__(self, parent, callback):
        super().__init__(parent, bg=BG_COLOUR)
        self.callback = callback
        self.create_widgets()

        self.pack_configure(padx=(10, 0), pady=10, fill=tk.Y)

    def create_widgets(self):
        self.label = tk.Label(self, text="Users", font=(FONT, 14), bg=BG_COLOUR, fg=FG_COLOUR)
        self.label.pack()

        self.add_user_button = tk.Button(self, text="Add New User", command=self.add_new_user, bg=BG_COLOUR,
                                         fg=FG_COLOUR)
        self.add_user_button.pack(side=tk.BOTTOM)
        # Add top and bottom padding to the button
        self.add_user_button.pack_configure(fill=tk.X)

        self.listbox = tk.Listbox(self, fg=FG_COLOUR, bg=BG_COLOUR, selectbackground='grey', selectforeground='white',
                                  highlightthickness=1, highlightbackground='grey')
        self.listbox.pack(fill=tk.BOTH, expand=True)

        # Load users and populate the listbox
        self.load_users()

        self.listbox.bind('<<ListboxSelect>>', self.on_select)

    def load_users(self):
        # Load user IDs from the user_data directory
        self.listbox.delete(0, tk.END)  # Clear existing entries
        user_folders = [folder for folder in os.listdir('user_data') if folder.startswith('u_')]
        for folder in sorted(user_folders, key=lambda x: int(x.split('_')[1])):
            user_id = folder.split('_')[1]
            user_name = self.get_user_name(folder)
            self.listbox.insert(tk.END, f"ID {user_id} - {user_name}")

    def get_user_name(self, folder):
        name_path = os.path.join('user_data', folder, 'name.txt')
        if os.path.exists(name_path):
            with open(name_path, 'r') as name_file:
                return name_file.read().strip()
        return "Unknown"

    def on_select(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            # Extract the user ID from the selected listbox entry
            selected_text = self.listbox.get(selected_index[0])
            user_id = selected_text.split()[1]  # Split the string and get the second element, which is the ID
            user_name = self.get_user_name(f'u_{user_id}')
            self.callback(user_id)

    def add_new_user(self):
        next_user_id = self.get_next_user_id()
        user_name = simpledialog.askstring("New User", "Enter name for new user:")
        if user_name:
            if msgbox.askyesno("Create New User",
                               f"Creating a new user with ID {next_user_id} and name {user_name}. Continue?"):
                self.create_new_user_folder(next_user_id, user_name)
                self.load_users()

    def get_next_user_id(self):
        # Logic to find the next available user ID
        existing_ids = [int(folder[2:]) for folder in os.listdir('user_data') if folder.startswith('u_')]
        return 0 if not existing_ids else max(existing_ids) + 1

    def create_new_user_folder(self, user_id, user_name):
        new_user_path = os.path.join('user_data', f'u_{user_id}')
        if not os.path.exists(new_user_path):
            os.makedirs(new_user_path)
            with open(os.path.join(new_user_path, 'name.txt'), 'w') as name_file:
                name_file.write(user_name)


class SessionDetail(tk.Frame):
    def __init__(self, parent, user_id, session_id, root):
        super().__init__(parent, bg=BG_COLOUR)
        self.user_id = user_id
        self.session_id = session_id
        self.create_widgets()
        self.root = root

        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        tk.Label(self, text=f"Session {self.session_id}", font=(FONT, 14), bg=BG_COLOUR, fg=FG_COLOUR).pack()

        self.recordings_listbox = tk.Listbox(self, height=5, fg=FG_COLOUR, bg=BG_COLOUR, selectbackground='grey',
                                             selectforeground='white',
                                             highlightthickness=1, highlightbackground='grey')
        self.recordings_listbox.pack(fill=tk.BOTH)

        # Load recordings for this session
        self.load_recordings()

        self.new_recording_button = tk.Button(self, text="Start New Recording", command=self.start_new_recording,
                                              bg=BG_COLOUR, fg=FG_COLOUR)
        # New recording button should be 200px wide and left-aligned
        self.new_recording_button.pack_configure(side=LEFT, ipadx=30)

        self.delete_session_button = tk.Button(self, text="x", command=self.delete_session, bg='darkred', fg='white')
        self.delete_session_button.pack_configure(side=RIGHT, ipadx=10)

    def load_recordings(self):
        # Load recordings from the session's CSV files and populate the listbox
        pass

    def start_new_recording(self):
        # Implement logic to start a new recording for this session
        pass

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


if __name__ == '__main__':
    app = App()
    app.mainloop()
