import os
import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import simpledialog, ttk

from config import FONT


class Sidebar(tk.Frame):
    def __init__(self, parent, callback):
        super().__init__(parent, bg=parent.colour_config["bg"])
        self.callback = callback
        self.parent = parent
        self.create_widgets()

        self.pack_configure(padx=(10, 0), pady=10, fill=tk.Y)
        # Set the width of the sidebar to 200px
        self.pack_propagate(False)
        self.config(width=250)

    def create_widgets(self):
        self.label = tk.Label(self, text="Users", font=(FONT, 14), bg=self.parent.colour_config["bg"], fg=self.parent.colour_config["fg"])
        self.label.pack()

        self.add_user_button = tk.Button(self, text="Add New User", command=self.add_new_user, bg=self.parent.colour_config["bg"],
                                         fg=self.parent.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.add_user_button.pack(side=tk.BOTTOM, pady=(10, 0))
        # Add top and bottom padding to the button
        self.add_user_button.pack_configure(fill=tk.X)

        self.listbox = tk.Listbox(self, fg=self.parent.colour_config["fg"], bg=self.parent.colour_config["bg"], selectbackground='grey', selectforeground='white',
                                  highlightthickness=0, highlightbackground='grey', relief=tk.RIDGE, borderwidth=1)
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