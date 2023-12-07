import multiprocessing
import os
import time
import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import LEFT, RIGHT
import datetime

import numpy as np

from myo.data_collection import start_recording
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
        tk.Label(self, text=f"Session {self.session_id}", font=(FONT, 14), bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]).pack()

        self.recordings_listbox = tk.Listbox(self, height=5,
                                             fg=self.root.colour_config["fg"],
                                             bg=self.root.colour_config["bg"],
                                             selectbackground='grey',
                                             selectforeground='white',
                                             highlightthickness=0, highlightbackground='grey',
                                             relief=tk.RIDGE, borderwidth=1)
        self.recordings_listbox.pack(fill=tk.BOTH)

        # Load recordings for this session
        self.load_recordings()

        self.new_recording_button = tk.Button(self, text="Start New Recording", command=self.start_new_recording,
                                              bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"],
                                              relief=tk.RIDGE, borderwidth=1)
        # New recording button should be 200px wide and left-aligned
        self.new_recording_button.pack_configure(side=LEFT, ipadx=30, pady=(5, 0))

        self.delete_session_button = tk.Button(self,
                                               name="delete_session_button",
                                               text="x",
                                               command=self.delete_session,
                                               bg='darkred',
                                               fg='white',
                                               relief=tk.RIDGE, borderwidth=1)
        self.delete_session_button.pack_configure(side=RIGHT, ipadx=10, pady=(5, 0))

    def load_recordings(self):
        # Get the session folder path
        session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}')

        # Clear the existing recordings listbox
        self.recordings_listbox.delete(0, tk.END)

        # Check if the session folder exists
        if not os.path.exists(session_folder):
            return

        # Find all CSV files in the session folder
        recording_files = [f for f in os.listdir(session_folder) if
                           os.path.isfile(os.path.join(session_folder, f)) and f.endswith('.csv')]

        # For each recording file, extract information and add it to the listbox
        for recording_file in recording_files:
            # Extract the filename
            filename = recording_file.split('.csv')[0]

            # Get the recording date and time from the filename
            # This assumes the filename format is recording_<date_time>.csv
            date_time = filename.split('_')[1]

            # Add the recording information to the listbox
            # You can modify this to display additional information from the CSV file
            self.recordings_listbox.insert(tk.END, f"{date_time} - {filename}")

        # Bind double-click event to open the selected recording
        self.recordings_listbox.bind(
            "<Double-Button-1>", lambda event: self.open_selected_recording()
        )

    def open_selected_recording(self):
        # Get the selected recording index
        selected_index = self.recordings_listbox.curselection()
        # Check if a recording is selected
        if not selected_index:
            return
        # Get the session folder path
        session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}')
        # Get the selected filename
        selected_filename = self.recordings_listbox.get(selected_index[0]).split(' - ')[1] + '.csv'
        # Open the selected recording file
        os.startfile(os.path.join(session_folder, selected_filename))

    def start_new_recording(self):
        q_result = multiprocessing.Queue()
        # Helper q to terminate the recording
        q_terminate = multiprocessing.Queue()
        # Helper q to check if the myo is ready
        # Only when the myo is ready, the recording will start
        q_myo_ready = multiprocessing.Queue()

        # Start a new recording
        start_recording(q_result, q_terminate, q_myo_ready)

        # Record for 5 seconds
        should_stop_recording = False
        recording = []
        while q_myo_ready.empty():
            time.sleep(0.01)

        timer = time.time()
        while not should_stop_recording:
            while not q_result.empty():
                emg = q_result.get()
                # Convert the data to a flat list
                emg_flat = [float(item) for item in emg]
                # recording.append(emg_flat.copy())
                print(emg_flat)
                recording.append(emg_flat.copy())

                if time.time() - timer > 5:
                    should_stop_recording = True

                now = time.time()
            else:
                time.sleep(0.001)

        # Terminate the recording
        q_terminate.put(True)

        # Generate a unique filename for the recording
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        recording_filename = f"recording_{now}.csv"
        # Get the session folder path
        session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}')
        # Create the recording file
        recording_path = os.path.join(session_folder, recording_filename)
        np.savetxt(recording_path, np.array(recording, dtype=float), delimiter=",")

        # Update the recordings listbox
        self.load_recordings()

        # Display a confirmation message
        msgbox.showinfo("Recording Finished", f"Recording saved as {recording_filename}")

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